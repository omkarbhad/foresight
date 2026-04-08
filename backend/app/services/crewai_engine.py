"""CrewAI-powered multi-agent Simulation Engine v4.

Features:
- Scenario-driven simulation (no monitor dependency)
- Dynamic agent generation: Claude analyzes scenario and creates tailored agents
- Scenario-based data fetching and sentiment analysis from APIs
- Neo4j graph memory with entity extraction and cross-simulation learning
- Dynamic cross-agent influence graph
- Full memory isolation per simulation
- Graceful fallback when Neo4j unavailable
"""

import os
import uuid
import shutil
import threading
import copy
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# CrewAI imports kept for create_agent() in crewai_agents.py
# Agent execution now uses direct LLM calls for speed

from ..config import Config
from ..utils.llm_client import get_llm_client
from ..utils.logger import get_logger
from ..models.task import TaskManager, TaskStatus
from ..models.simulation import Simulation
from .crewai_agents import (
    AGENT_DEFS, TIME_LABELS, DEFAULT_ROUNDS, create_agent,
    generate_dynamic_agents, expand_agents, renormalize_weights,
    merge_influence_matrix, update_execution_order, prefix_agent_keys,
    MAX_AGENTS_PER_SCENARIO, MAX_TOTAL_AGENTS_MULTI,
)
from .crewai_tools import MediaLandscapeTool
from .scenario_data_fetcher import (
    fetch_scenario_data, analyze_scenario_sentiment, build_scenario_briefing,
)
from .entity_discovery import extract_emerging_entities, fetch_entity_data
from .influence_matrix import (
    get_influence_context, get_agent_order, compute_influence_incoming,
    INFLUENCE_INCOMING, AGENT_ORDER,
)

logger = get_logger('foresight.simulation')

# Base directory for simulation memory isolation
MEMORY_BASE = "/tmp/foresight_sims"


class SimulationCancelled(Exception):
    """Raised when a simulation is cancelled by the user."""
    pass


def _check_cancelled(tm: TaskManager, task_id: str):
    """Check if cancellation has been requested and raise if so."""
    task = tm.get_task(task_id)
    if task and task.cancel_requested:
        raise SimulationCancelled("Simulation cancelled by user")


SCENARIO_COLORS = [
    "#2563eb", "#dc2626", "#059669", "#7c3aed", "#ea580c",
    "#0891b2", "#db2777", "#65a30d",
]


def _generate_per_scenario_agents(
    scenarios: List[str],
    combined_scenario: str,
    tm: TaskManager,
    task_id: str,
) -> tuple:
    """Generate agents per scenario, merge into unified pool.

    Returns:
        (merged_agent_defs, merged_influence_outgoing, merged_execution_order,
         agent_scenario_map, scenario_map)
    """
    scenario_map = {i: sc for i, sc in enumerate(scenarios)}
    agent_scenario_map: Dict[str, str] = {}
    merged_defs: Dict[str, Dict] = {}
    merged_influence: Dict[str, List[str]] = {}
    all_orders: List[List[str]] = []

    for idx, sc in enumerate(scenarios):
        tm.update_task(
            task_id,
            message=f"Generating agents for scenario {idx + 1}/{len(scenarios)}: {sc[:60]}...",
            progress_detail=_update_detail(tm, task_id, phase="planning_agents"),
        )

        sc_defs, sc_influence, sc_order = generate_dynamic_agents(
            monitor_name=sc,
            keywords=[],
            scenario=combined_scenario,
            max_agents=MAX_AGENTS_PER_SCENARIO,
        )

        # Prefix colliding keys
        existing_keys = set(merged_defs.keys())
        if existing_keys:
            sc_defs, sc_influence, sc_order = prefix_agent_keys(
                sc_defs, sc_influence, sc_order,
                prefix=f"s{idx}_",
                existing_keys=existing_keys,
            )

        # Tag each agent with its scenario
        for key, defn in sc_defs.items():
            defn["scenario"] = sc
            defn["scenario_index"] = idx
            agent_scenario_map[key] = sc

        merged_defs.update(sc_defs)

        # Merge influence (cross-scenario connections start empty, emerge organically)
        for source, targets in sc_influence.items():
            merged_influence.setdefault(source, []).extend(targets)

        all_orders.append(sc_order)

        logger.info(
            f"Scenario {idx} agents generated: {list(sc_defs.keys())} "
            f"({len(sc_defs)} agents)"
        )

    # Interleave execution orders from all scenarios
    merged_order = _interleave_orders(all_orders)

    # Ensure every agent has an influence entry
    for key in merged_defs:
        merged_influence.setdefault(key, [])

    renormalize_weights(merged_defs)

    return merged_defs, merged_influence, merged_order, agent_scenario_map, scenario_map


def _interleave_orders(orders: List[List[str]]) -> List[str]:
    """Interleave execution orders from multiple scenarios (round-robin)."""
    result = []
    seen = set()
    max_len = max((len(o) for o in orders), default=0)
    for i in range(max_len):
        for order in orders:
            if i < len(order) and order[i] not in seen:
                result.append(order[i])
                seen.add(order[i])
    return result


def start_simulation(scenarios: List[str], config: Dict = None) -> str:
    """Create a task and launch simulation in a background thread. Returns task_id."""
    tm = TaskManager()
    config = config or {}
    total_rounds = min(max(config.get('total_rounds', DEFAULT_ROUNDS), 3), 8)

    combined_scenario = " | ".join(scenarios)

    sim_config = {
        'total_rounds': total_rounds,
        'scenarios': scenarios,
        'scenario': combined_scenario,
    }

    task_id = tm.create_task("simulation", metadata=sim_config)

    thread = threading.Thread(
        target=_run_simulation,
        args=(task_id, scenarios, combined_scenario, sim_config),
        daemon=True,
    )
    thread.start()
    return task_id


def _run_simulation(task_id: str, scenarios: List[str], scenario: str, config: Dict):
    """Main simulation loop — runs in background thread."""
    tm = TaskManager()
    total_rounds = config['total_rounds']
    simulation_id = f"sim_{uuid.uuid4().hex[:12]}"
    memory_dir = os.path.join(MEMORY_BASE, simulation_id)

    tm.update_task(
        task_id,
        status=TaskStatus.PROCESSING,
        progress=0,
        message="Initializing simulation...",
        progress_detail={
            "rounds": [],
            "current_round": 0,
            "total_rounds": total_rounds,
            "personas": [],
            "simulation_id": None,
            "phase": "initializing",
            "current_agent": None,
            "influence_log": [],
            "agent_defs": {},
            "agent_timeline": [],
        },
    )

    try:
        subject = scenario
        multi_scenario = len(scenarios) > 1
        agent_scenario_map: Dict[str, str] = {}
        scenario_map: Dict[int, str] = {}

        # Phase 0: Agent Planning + Data Fetching (IN PARALLEL)
        # These are independent — run them concurrently to cut startup time in half
        tm.update_task(
            task_id, message="Analyzing scenario and fetching data...",
            progress_detail=_update_detail(tm, task_id, phase="planning_agents"),
        )

        agent_defs_map = None
        influence_outgoing = None
        influence_incoming_map = None
        execution_order = None
        engine_version = "v4"

        # Results containers for parallel work
        all_scenario_data = {}
        all_sentiment = {}
        briefing = ""

        def _do_agent_generation():
            """Generate agents (LLM call)."""
            t0 = time.time()
            if multi_scenario:
                result = _generate_per_scenario_agents(
                    scenarios, scenario, tm, task_id,
                )
            else:
                defs, infl, order = generate_dynamic_agents(
                    monitor_name=subject,
                    keywords=[],
                    scenario=scenario,
                )
                sc_map = {0: scenarios[0]}
                asc_map = {}
                for key in defs:
                    asc_map[key] = scenarios[0]
                    defs[key]["scenario"] = scenarios[0]
                    defs[key]["scenario_index"] = 0
                result = (defs, infl, order, asc_map, sc_map)
            logger.info(f"Agent generation took {time.time() - t0:.1f}s")
            return result

        def _do_data_fetching():
            """Fetch scenario data + sentiment (LLM + API calls)."""
            t0 = time.time()
            local_data = {}
            local_sentiment = {}
            local_briefing = ""
            for sc in scenarios:
                try:
                    sc_data = fetch_scenario_data(sc)
                    local_data[sc] = sc_data
                    sc_sentiment = analyze_scenario_sentiment(sc, sc_data)
                    local_sentiment[sc] = sc_sentiment
                    sc_briefing = build_scenario_briefing(sc, sc_data, sc_sentiment)
                    local_briefing += sc_briefing + "\n\n"
                    logger.info(f"Scenario data for '{sc[:40]}': sentiment={sc_sentiment.get('overall_sentiment', 0):.2f}")
                except Exception as e:
                    logger.warning(f"Scenario data fetch failed for '{sc[:40]}': {e}")
            logger.info(f"Data fetching took {time.time() - t0:.1f}s")
            return local_data, local_sentiment, local_briefing

        # Run both in parallel with timeout
        AGENT_GEN_TIMEOUT = 90  # seconds — fall back to static if too slow
        with ThreadPoolExecutor(max_workers=2) as executor:
            agent_future = executor.submit(_do_agent_generation)
            data_future = executor.submit(_do_data_fetching)

            # Get agent results first (to push to frontend ASAP)
            try:
                agent_result = agent_future.result(timeout=AGENT_GEN_TIMEOUT)
                if multi_scenario:
                    (agent_defs_map, influence_outgoing, execution_order,
                     agent_scenario_map, scenario_map) = agent_result
                else:
                    (agent_defs_map, influence_outgoing, execution_order,
                     agent_scenario_map, scenario_map) = agent_result

                influence_incoming_map = compute_influence_incoming(influence_outgoing)
                logger.info(f"Dynamic agents: {list(agent_defs_map.keys())}")
            except TimeoutError:
                logger.warning(f"Agent generation timed out after {AGENT_GEN_TIMEOUT}s, using static agents")
                agent_defs_map = dict(AGENT_DEFS)
                influence_outgoing = None
                influence_incoming_map = INFLUENCE_INCOMING
                execution_order = list(AGENT_ORDER)
                engine_version = "v3"
                scenario_map = {0: scenarios[0]}
                for key in agent_defs_map:
                    agent_scenario_map[key] = scenarios[0]
            except Exception as e:
                logger.warning(f"Dynamic agent generation failed, falling back to static: {e}")
                agent_defs_map = dict(AGENT_DEFS)
                influence_outgoing = None
                influence_incoming_map = INFLUENCE_INCOMING
                execution_order = list(AGENT_ORDER)
                engine_version = "v3"
                scenario_map = {0: scenarios[0]}
                for key in agent_defs_map:
                    agent_scenario_map[key] = scenarios[0]

        # Push agents to frontend immediately (don't wait for data fetch)
        agent_keys = get_agent_order(
            list(agent_defs_map.keys()),
            custom_order=execution_order,
        )

        agent_defs_meta = {}
        for key in agent_keys:
            defn = agent_defs_map[key]
            meta = {
                "name": defn.get("name", key.replace("_", " ").title()),
                "icon": defn.get("icon", "\u2753"),
                "color": defn.get("color", "#6b7280"),
                "role": defn.get("role", ""),
                "platform": defn.get("platform", "mixed"),
            }
            if multi_scenario:
                meta["scenario"] = agent_scenario_map.get(key, "")
                meta["scenario_index"] = defn.get("scenario_index", 0)
            agent_defs_meta[key] = meta

        agent_timeline = [{"round": 0, "agents": list(agent_keys)}]

        detail = _get_detail(tm, task_id)
        detail["personas"] = agent_keys
        detail["agent_defs"] = agent_defs_meta
        detail["agent_timeline"] = agent_timeline
        if multi_scenario:
            detail["scenario_map"] = scenario_map
            detail["agent_scenario_map"] = agent_scenario_map
        tm.update_task(task_id, progress_detail=detail)

        # Now wait for data fetching to finish (may already be done)
        tm.update_task(task_id, message="Finishing data analysis...",
                       progress_detail=_update_detail(tm, task_id, phase="fetching_scenario_data"))
        try:
            all_scenario_data, all_sentiment, briefing = data_future.result()
        except Exception as e:
            logger.warning(f"Data fetching failed: {e}")

        # Store sentiment in progress detail
        detail = _get_detail(tm, task_id)
        detail["scenario_sentiment"] = {
            sc: {
                "overall_sentiment": s.get("overall_sentiment", 0.0),
                "positive_signals": s.get("positive_signals", [])[:3],
                "negative_signals": s.get("negative_signals", [])[:3],
                "summary": s.get("summary", ""),
            }
            for sc, s in all_sentiment.items()
        }
        tm.update_task(task_id, progress_detail=detail)

        # Phase 0.5b: Initialize graph memory (if enabled)
        graph_writer = None
        graph_reader = None
        scenario_embedding = None
        cross_sim_briefing = ""

        if Config.GRAPH_MEMORY_ENABLED:
            try:
                from .graph_schema import get_neo4j_driver
                from .graph_memory import GraphMemoryWriter, GraphMemoryReader
                from ..utils.embeddings import generate_embedding

                tm.update_task(task_id, message="Initializing knowledge graph...",
                               progress_detail=_update_detail(tm, task_id, phase="graph_init"))

                driver = get_neo4j_driver()
                graph_writer = GraphMemoryWriter(driver, simulation_id)
                graph_writer.init_simulation(
                    None, scenario, agent_defs_map, execution_order, total_rounds
                )
                graph_reader = GraphMemoryReader(driver, simulation_id)

                scenario_embedding = generate_embedding(scenario)
                cross_sim_briefing = graph_reader.get_similar_scenarios(scenario_embedding)
                if cross_sim_briefing:
                    logger.info("Cross-simulation context loaded from graph")
            except Exception as e:
                logger.warning(f"Graph memory init failed, falling back to text mode: {e}")
                graph_writer = None
                graph_reader = None

        if cross_sim_briefing:
            briefing += "\n\n" + cross_sim_briefing

        # Phase 2: Prepare tools
        tm.update_task(task_id, message="Creating simulation agents...",
                       progress_detail=_update_detail(tm, task_id, phase="creating_agents"))

        landscape_tool = MediaLandscapeTool(briefing=briefing)

        # Build tools list (conditionally includes graph tools)
        tools = [landscape_tool]
        if graph_reader:
            from .graph_tools import SimulationMemoryTool, CrossSimulationTool
            tools.append(CrossSimulationTool(
                reader=graph_reader,
                scenario_embedding=scenario_embedding or [],
            ))

        # Phase 3: Execute rounds
        all_rounds = []
        cumulative_actions = []
        influence_log = []

        for round_num in range(1, total_rounds + 1):
            _check_cancelled(tm, task_id)
            round_start = time.time()

            time_label = TIME_LABELS.get(round_num, f"Round {round_num}")
            progress_pct = int((round_num - 1) / (total_rounds + 1) * 100)

            tm.update_task(
                task_id,
                progress=progress_pct,
                message=f"Round {round_num}/{total_rounds}: {time_label}",
                progress_detail=_update_detail(
                    tm, task_id,
                    phase="round_execution",
                    current_round=round_num,
                ),
            )

            round_actions, round_influence = _execute_round(
                round_num=round_num,
                time_label=time_label,
                total_rounds=total_rounds,
                scenario=scenario,
                brand=subject,
                agent_keys=agent_keys,
                agent_defs_map=agent_defs_map,
                influence_incoming=influence_incoming_map,
                previous_rounds=all_rounds,
                cumulative_actions=cumulative_actions,
                tools=tools,
                memory_dir=memory_dir,
                tm=tm,
                task_id=task_id,
                graph_reader=graph_reader,
                graph_writer=graph_writer,
                agent_scenario_map=agent_scenario_map if multi_scenario else None,
            )

            cumulative_actions.extend(
                a for a in round_actions if a.get('action_type') != 'no_action'
            )
            round_metrics = _compute_round_metrics(
                round_actions, cumulative_actions, agent_keys, agent_defs_map,
                agent_scenario_map=agent_scenario_map if multi_scenario else None,
            )
            influence_log.extend(round_influence)

            round_data = {
                "round_number": round_num,
                "time_label": time_label,
                "actions": round_actions,
                "metrics": round_metrics,
            }
            all_rounds.append(round_data)

            detail = _get_detail(tm, task_id)
            detail["rounds"] = copy.deepcopy(all_rounds)
            detail["current_round"] = round_num
            detail["influence_log"] = influence_log
            tm.update_task(task_id, progress_detail=detail)

            # Update round metrics in graph
            if graph_writer:
                try:
                    graph_writer.update_round_metrics(round_num, round_metrics)
                except Exception:
                    pass

            logger.info(
                f"Round {round_num}/{total_rounds} complete in {time.time() - round_start:.1f}s "
                f"(sentiment={round_metrics.get('avg_sentiment', 0):.2f}, "
                f"volume={round_metrics.get('total_volume', 0)}, agents={len(agent_keys)})"
            )

            # --- Dynamic Agent Expansion (skip last round) ---
            if round_num < total_rounds:
                try:
                    tm.update_task(
                        task_id,
                        message=f"Analyzing round {round_num} for emerging entities...",
                        progress_detail=_update_detail(
                            tm, task_id, phase="discovering_agents",
                        ),
                    )

                    new_entities = extract_emerging_entities(
                        scenario=scenario,
                        existing_agent_keys=agent_keys,
                        existing_agent_defs=agent_defs_map,
                        round_actions=round_actions,
                        round_num=round_num,
                    )

                    if new_entities:
                        tm.update_task(
                            task_id,
                            message=f"Fetching data for {len(new_entities)} new entities...",
                            progress_detail=_update_detail(
                                tm, task_id, phase="fetching_entity_data",
                            ),
                        )
                        entity_data = fetch_entity_data(new_entities, scenario)

                        tm.update_task(
                            task_id,
                            message="Generating new agent personas...",
                            progress_detail=_update_detail(
                                tm, task_id, phase="expanding_agents",
                            ),
                        )
                        new_agent_defs, new_influence, order_inserts = expand_agents(
                            scenario=scenario,
                            existing_agent_defs=agent_defs_map,
                            new_entities=new_entities,
                            entity_data=entity_data,
                            round_actions=round_actions,
                            max_agents=MAX_TOTAL_AGENTS_MULTI if multi_scenario else None,
                        )

                        if new_agent_defs:
                            # Assign scenario to new agents based on which scenario's agents triggered them
                            if multi_scenario:
                                for key in new_agent_defs:
                                    # Determine which scenario triggered this entity
                                    mentioning_scenarios = {}
                                    for action in round_actions:
                                        persona = action.get("persona", "")
                                        sc = agent_scenario_map.get(persona, "")
                                        if sc:
                                            mentioning_scenarios[sc] = mentioning_scenarios.get(sc, 0) + 1
                                    # Assign to the most-represented scenario, or "cross_scenario"
                                    if mentioning_scenarios:
                                        top_sc = max(mentioning_scenarios, key=mentioning_scenarios.get)
                                        agent_scenario_map[key] = top_sc
                                        new_agent_defs[key]["scenario"] = top_sc
                                        sc_idx = next(
                                            (i for i, s in scenario_map.items() if s == top_sc), 0
                                        )
                                        new_agent_defs[key]["scenario_index"] = sc_idx
                                    else:
                                        agent_scenario_map[key] = "cross_scenario"
                                        new_agent_defs[key]["scenario"] = "cross_scenario"

                            agent_defs_map.update(new_agent_defs)
                            renormalize_weights(agent_defs_map)

                            if influence_outgoing is not None:
                                merge_influence_matrix(influence_outgoing, new_influence)
                                for key in new_agent_defs:
                                    influence_outgoing.setdefault(key, [])
                                influence_incoming_map = compute_influence_incoming(influence_outgoing)

                            new_keys = list(new_agent_defs.keys())
                            agent_keys = update_execution_order(
                                agent_keys, order_inserts, new_keys,
                            )

                            for key in new_keys:
                                defn = agent_defs_map[key]
                                meta = {
                                    "name": defn.get("name", key.replace("_", " ").title()),
                                    "icon": defn.get("icon", "\u2753"),
                                    "color": defn.get("color", "#6b7280"),
                                    "role": defn.get("role", ""),
                                    "platform": defn.get("platform", "mixed"),
                                }
                                if multi_scenario:
                                    meta["scenario"] = agent_scenario_map.get(key, "")
                                    meta["scenario_index"] = defn.get("scenario_index", 0)
                                agent_defs_meta[key] = meta

                            agent_timeline.append({
                                "round": round_num,
                                "agents": new_keys,
                            })

                            detail = _get_detail(tm, task_id)
                            detail["personas"] = agent_keys
                            detail["agent_defs"] = agent_defs_meta
                            detail["agent_timeline"] = agent_timeline
                            tm.update_task(task_id, progress_detail=detail)

                            logger.info(
                                f"Round {round_num} expansion: added {len(new_keys)} agents "
                                f"{new_keys} (total: {len(agent_keys)})"
                            )

                except Exception as exp_err:
                    logger.warning(f"Agent expansion after round {round_num} failed: {exp_err}")

        # Phase 4: Generate final summary
        tm.update_task(
            task_id, progress=90, message="Generating final analysis...",
            progress_detail=_update_detail(tm, task_id, phase="generating_summary"),
        )
        client = get_llm_client()
        aggregate_metrics = _generate_summary(
            client, all_rounds, scenario, subject, agent_keys,
            scenarios=scenarios if multi_scenario else None,
            agent_scenario_map=agent_scenario_map if multi_scenario else None,
            influence_log=influence_log if multi_scenario else None,
        )

        # Update simulation-level metrics in graph
        if graph_writer:
            try:
                graph_writer.update_simulation_metrics(
                    final_sentiment=aggregate_metrics.get("final_sentiment", 0.0),
                    peak_crisis=aggregate_metrics.get("peak_crisis_level", 0.0),
                )
            except Exception:
                pass

        # Phase 5: Persist to DB and cleanup
        tm.update_task(
            task_id, message="Saving results...",
            progress_detail=_update_detail(tm, task_id, phase="persisting"),
        )

        try:
            Simulation.create(
                simulation_id=simulation_id,
                monitor_id="",
                scenario=scenario,
                config=config,
                total_rounds=total_rounds,
                rounds=all_rounds,
                aggregate_metrics=aggregate_metrics,
                agent_states={
                    "_version": f"{engine_version}_dynamic" if engine_version == "v4" else "v3",
                    "_agent_defs": {
                        k: {kk: vv for kk, vv in v.items() if kk != "backstory"}
                        for k, v in agent_defs_map.items()
                    },
                    "_influence_matrix": influence_outgoing,
                    "_execution_order": execution_order,
                    "_agent_timeline": agent_timeline,
                    **({"_scenario_map": scenario_map, "_agent_scenario_map": agent_scenario_map}
                       if multi_scenario else {}),
                    **{k: {"rounds_participated": total_rounds} for k in agent_keys},
                },
                influence_log=influence_log,
                historical_briefing=briefing[:5000] if briefing else None,
                engine_version=engine_version,
            )
        except Exception as db_err:
            logger.error(f"Failed to persist simulation: {db_err}")

        # Persist graph influence data
        if graph_writer:
            try:
                graph_writer.persist_influence_graph(influence_log)
            except Exception as e:
                logger.warning(f"Graph influence persist failed: {e}")

        # Cleanup CrewAI file-based memory (graph data persists in Neo4j)
        try:
            if os.path.exists(memory_dir):
                shutil.rmtree(memory_dir)
        except Exception:
            pass

        # Complete
        result = {
            "simulation_id": simulation_id,
            "total_rounds": total_rounds,
            "rounds": all_rounds,
            "aggregate_metrics": aggregate_metrics,
            "agent_defs": agent_defs_meta,
            "influence_log": influence_log,
            "agent_timeline": agent_timeline,
        }
        if multi_scenario:
            result["scenario_map"] = scenario_map
            result["agent_scenario_map"] = agent_scenario_map

        detail = _get_detail(tm, task_id)
        detail["simulation_id"] = simulation_id
        detail["rounds"] = all_rounds
        detail["aggregate_metrics"] = aggregate_metrics
        detail["phase"] = "completed"
        detail["influence_log"] = influence_log
        detail["agent_timeline"] = agent_timeline
        if multi_scenario:
            detail["scenario_map"] = scenario_map
            detail["agent_scenario_map"] = agent_scenario_map
        tm.update_task(task_id, progress_detail=detail)
        tm.complete_task(task_id, result=result)

        logger.info(f"Simulation {simulation_id} completed successfully ({engine_version} engine)")

    except SimulationCancelled:
        logger.info(f"Simulation {task_id} cancelled by user")
        detail = _get_detail(tm, task_id)
        partial_result = {
            "simulation_id": simulation_id,
            "total_rounds": detail.get("current_round", 0),
            "rounds": detail.get("rounds", []),
            "aggregate_metrics": {},
            "agent_defs": detail.get("agent_defs", {}),
            "influence_log": detail.get("influence_log", []),
            "agent_timeline": detail.get("agent_timeline", []),
            "cancelled": True,
        }
        detail["phase"] = "cancelled"
        tm.update_task(
            task_id,
            status=TaskStatus.CANCELLED,
            message="Simulation cancelled",
            result=partial_result,
            progress_detail=detail,
        )
        try:
            if os.path.exists(memory_dir):
                shutil.rmtree(memory_dir)
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        tm.fail_task(task_id, str(e))
        try:
            if os.path.exists(memory_dir):
                shutil.rmtree(memory_dir)
        except Exception:
            pass


def _execute_round(
    round_num, time_label, total_rounds, scenario, brand,
    agent_keys, agent_defs_map, influence_incoming,
    previous_rounds, cumulative_actions,
    tools, memory_dir, tm, task_id,
    graph_reader=None, graph_writer=None,
    agent_scenario_map=None,
) -> tuple:
    """Execute one round: call each agent in influence order via mini-crews."""
    round_actions = []
    round_influence = []
    current_metrics = _get_current_aggregate(cumulative_actions, agent_keys, agent_defs_map)

    for agent_key in agent_keys:
        _check_cancelled(tm, task_id)

        defn = agent_defs_map[agent_key]

        detail = _get_detail(tm, task_id)
        detail["current_agent"] = agent_key
        tm.update_task(task_id, progress_detail=detail)

        try:
            # Use graph-based influence context if available, else flat matrix
            if graph_reader:
                influence_ctx = graph_reader.get_influence_context(
                    agent_key, round_num, influence_incoming,
                )
                # Fall back to flat if graph returned nothing
                if not influence_ctx:
                    influence_ctx = get_influence_context(
                        agent_key, round_actions, previous_rounds,
                        influence_incoming=influence_incoming,
                        agent_scenario_map=agent_scenario_map,
                    )
            else:
                influence_ctx = get_influence_context(
                    agent_key, round_actions, previous_rounds,
                    influence_incoming=influence_incoming,
                    agent_scenario_map=agent_scenario_map,
                )

            # Use graph memory for history context if available, else text dump
            if graph_reader:
                history_text = graph_reader.get_simulation_context(agent_key, round_num)
            else:
                history_text = _summarize_previous_rounds(previous_rounds)

            task_prompt = _build_task_prompt(
                agent_key=agent_key,
                defn=defn,
                scenario=scenario,
                brand=brand,
                round_num=round_num,
                time_label=time_label,
                total_rounds=total_rounds,
                influence_ctx=influence_ctx,
                current_metrics=current_metrics,
                history_text=history_text,
                primary_scenario=agent_scenario_map.get(agent_key) if agent_scenario_map else None,
                per_scenario_metrics=_build_per_scenario_metrics_text(
                    cumulative_actions, agent_scenario_map
                ) if agent_scenario_map else None,
            )

            # Direct LLM call (bypasses CrewAI overhead — much faster)
            client = get_llm_client(temperature=0.7, max_tokens=1024)
            system_prompt = (
                f"You are {defn['name']}, a {defn['role']}.\n\n"
                f"Backstory: {defn.get('backstory', '')}\n\n"
                f"Goal: {defn.get('goal', '')}"
            )
            raw_response = client.chat(
                messages=[{"role": "user", "content": task_prompt}],
                system=system_prompt,
                temperature=0.7,
                max_tokens=1024,
            )
            action = _parse_agent_response(raw_response, agent_key, defn, agent_keys)

            # Record action to graph memory
            if graph_writer:
                try:
                    graph_writer.record_action(agent_key, defn, action, round_num, round_actions)
                except Exception as ge:
                    logger.warning(f"Graph record_action failed for {agent_key}: {ge}")

            if action.get("influenced_by"):
                for source in action["influenced_by"]:
                    entry = {
                        "round": round_num,
                        "from": source,
                        "to": agent_key,
                        "action": action["action_type"],
                    }
                    if agent_scenario_map:
                        from_sc = agent_scenario_map.get(source, "")
                        to_sc = agent_scenario_map.get(agent_key, "")
                        entry["from_scenario"] = from_sc
                        entry["to_scenario"] = to_sc
                        entry["cross_scenario"] = from_sc != to_sc
                    round_influence.append(entry)

        except Exception as e:
            logger.error(f"Agent {agent_key} failed in round {round_num}: {e}")
            action = {
                "action_type": "no_action",
                "title": f"[Error: {agent_key} could not respond]",
                "content": str(e),
                "sentiment_score": 0.0,
                "reach_estimate": 0,
                "reasoning": "Agent error",
                "influenced_by": [],
            }

        action["persona"] = agent_key
        action["platform"] = defn.get("platform", "mixed")
        if agent_scenario_map:
            action["scenario"] = agent_scenario_map.get(agent_key, "")
        round_actions.append(action)

        # Stream: push partial round to frontend immediately after each agent
        _stream_partial_round(
            tm, task_id, round_num, time_label, round_actions, round_influence,
            agent_keys, agent_defs_map, cumulative_actions + [
                a for a in round_actions if a.get('action_type') != 'no_action'
            ],
            agent_scenario_map,
        )

    return round_actions, round_influence


def _stream_partial_round(
    tm, task_id, round_num, time_label, round_actions, round_influence,
    agent_keys, agent_defs_map, all_actions_so_far, agent_scenario_map,
):
    """Push partial round data to progress_detail so frontend updates per-agent."""
    detail = _get_detail(tm, task_id)
    partial_metrics = _compute_round_metrics(
        round_actions, all_actions_so_far, agent_keys, agent_defs_map,
        agent_scenario_map=agent_scenario_map,
    )

    # Build or update the current round in the rounds list
    current_round_data = {
        "round_number": round_num,
        "time_label": time_label,
        "actions": list(round_actions),
        "metrics": partial_metrics,
    }

    # Replace last round if same round_number, else append
    rounds = detail.get("rounds", [])
    if rounds and rounds[-1].get("round_number") == round_num:
        rounds[-1] = current_round_data
    else:
        rounds.append(current_round_data)

    detail["rounds"] = rounds
    detail["current_round"] = round_num
    detail["influence_log"] = detail.get("influence_log", []) + [
        e for e in round_influence
        if e not in detail.get("influence_log", [])
    ]
    tm.update_task(task_id, progress_detail=detail)


TASK_PROMPT = """You are playing the role of {role} in a multi-agent scenario simulation about {brand}.

SCENARIO: {scenario}
{primary_scenario_section}
CURRENT TIME: {time_label} (Round {round_num} of {total_rounds})

{influence_section}

{history_section}

CURRENT AGGREGATE METRICS:
- Overall sentiment: {current_sentiment}
- Total media volume: {current_volume} pieces
{per_scenario_metrics}

You have access to a media_landscape tool with real-world data about this scenario.
Use it if you need context about the subject's recent media history.

Based on the scenario, the current time period, what has happened so far, and the actions
of agents that influence you, decide your next action.

Choose one action_type from: {action_types}
(Choose "no_action" if it's strategically better to stay silent this round.)

Respond with ONLY this JSON (no other text):
{{
    "action_type": "one of your available types",
    "title": "headline or title of your action (max 100 chars)",
    "content": "2-3 sentence description of what you publish/post/say",
    "sentiment_score": float from -1.0 (very negative toward the subject) to 1.0 (very positive),
    "reach_estimate": integer estimated audience reach,
    "reasoning": "1 sentence explaining why you chose this action now",
    "influenced_by": ["list of exact agent_key identifiers (snake_case) whose actions influenced your decision, or empty"]
}}"""


def _build_per_scenario_metrics_text(
    cumulative_actions: List[Dict],
    agent_scenario_map: Dict[str, str],
) -> str:
    """Build per-scenario metrics text for the task prompt."""
    if not agent_scenario_map or not cumulative_actions:
        return ""

    scenarios = set(agent_scenario_map.values())
    lines = []
    for sc in sorted(scenarios):
        sc_actions = [
            a for a in cumulative_actions
            if agent_scenario_map.get(a.get("persona", "")) == sc
            and a.get("action_type") != "no_action"
        ]
        if sc_actions:
            avg = sum(a.get("sentiment_score", 0) for a in sc_actions) / len(sc_actions)
            lines.append(f"  - {sc[:60]}: sentiment {avg:.2f}, volume {len(sc_actions)}")

    if not lines:
        return ""
    return "Per-scenario metrics:\n" + "\n".join(lines)


def _build_task_prompt(
    agent_key, defn, scenario, brand, round_num, time_label,
    total_rounds, influence_ctx, current_metrics, history_text,
    primary_scenario=None, per_scenario_metrics=None,
) -> str:
    """Build the task prompt for a specific agent."""
    influence_section = influence_ctx if influence_ctx else "No influence context available yet."
    if not history_text:
        history_section = "This is the first round."
    elif history_text.startswith("SIMULATION MEMORY"):
        history_section = history_text  # Graph reader already includes header
    else:
        history_section = f"WHAT HAS HAPPENED SO FAR:\n{history_text}"

    # Multi-scenario: include primary scenario section
    if primary_scenario and primary_scenario != scenario:
        primary_scenario_section = (
            f"\nYOUR PRIMARY SCENARIO: {primary_scenario}\n"
            "You originated from this scenario. While you can see and react to events from all "
            "scenarios, your primary motivations and actions should be grounded in your scenario. "
            "When agents from other scenarios do things that affect your domain, you may react — "
            "this creates cross-scenario dynamics.\n"
        )
    else:
        primary_scenario_section = ""

    return TASK_PROMPT.format(
        role=defn["role"],
        scenario=scenario,
        brand=brand,
        time_label=time_label,
        round_num=round_num,
        total_rounds=total_rounds,
        influence_section=influence_section,
        history_section=history_section,
        current_sentiment=f"{current_metrics.get('avg_sentiment', 0.0):.2f}",
        current_volume=current_metrics.get('total_volume', 0),
        action_types=", ".join(defn["action_types"]),
        primary_scenario_section=primary_scenario_section,
        per_scenario_metrics=per_scenario_metrics or "",
    )


def _parse_agent_response(
    raw: str, agent_key: str, defn: Dict, agent_keys: List[str] = None,
) -> Dict:
    """Parse the agent's response into a structured action dict."""
    import json
    import re

    cleaned = raw.strip()
    cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\n?```\s*$', '', cleaned)
    cleaned = cleaned.strip()

    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning(f"Agent {agent_key} returned non-JSON: {cleaned[:200]}")
        result = {
            "action_type": "no_action",
            "title": "Could not parse response",
            "content": cleaned[:300],
            "sentiment_score": 0.0,
            "reach_estimate": 0,
            "reasoning": "Response was not valid JSON",
            "influenced_by": [],
        }

    result.setdefault("action_type", "no_action")
    result.setdefault("title", "")
    result.setdefault("content", "")
    result.setdefault("sentiment_score", 0.0)
    result.setdefault("reach_estimate", 0)
    result.setdefault("reasoning", "")
    result.setdefault("influenced_by", [])

    result["sentiment_score"] = max(-1.0, min(1.0, float(result["sentiment_score"])))
    result["reach_estimate"] = int(result["reach_estimate"] * defn.get("reach_multiplier", 1.0))
    if not isinstance(result["influenced_by"], list):
        result["influenced_by"] = []

    if agent_keys:
        result["influenced_by"] = _normalize_influenced_by(
            result["influenced_by"], agent_keys, agent_key,
        )

    return result


def _normalize_influenced_by(
    raw_influences: List, valid_keys: List[str], self_key: str,
) -> List[str]:
    """Validate and fuzzy-match influenced_by entries against actual agent keys."""
    valid_set = set(valid_keys)
    key_lookup = {k: k for k in valid_keys}
    for k in valid_keys:
        key_lookup[k.lower()] = k
        key_lookup[k.replace("_", " ")] = k
        key_lookup[k.replace("_", " ").lower()] = k
        key_lookup[k.replace("_", " ").title()] = k

    resolved = []
    for entry in raw_influences:
        if not isinstance(entry, str):
            continue
        entry = entry.strip()
        if not entry or entry == self_key:
            continue

        if entry in valid_set:
            resolved.append(entry)
            continue

        normalized = entry.lower().replace(" ", "_").replace("-", "_")
        if normalized in valid_set:
            resolved.append(normalized)
            continue

        if entry in key_lookup:
            resolved.append(key_lookup[entry])
            continue

        for vk in valid_keys:
            if vk in normalized or normalized in vk:
                resolved.append(vk)
                break

    return list(dict.fromkeys(resolved))


# --- Metrics computation ---

def _get_current_aggregate(
    cumulative_actions: List[Dict], agent_keys: List[str],
    agent_defs_map: Dict[str, Dict] = None,
) -> Dict:
    """Quick aggregate from all actions so far."""
    if not cumulative_actions:
        return {"avg_sentiment": 0.0, "total_volume": 0}

    defs = agent_defs_map or AGENT_DEFS
    total_weight = 0.0
    weighted_sentiment = 0.0
    for a in cumulative_actions:
        defn = defs.get(a.get("persona", ""), {})
        w = defn.get("influence_weight", 0.1)
        weighted_sentiment += a.get("sentiment_score", 0.0) * w
        total_weight += w

    avg_sent = weighted_sentiment / total_weight if total_weight > 0 else 0.0
    volume = len(cumulative_actions)

    return {"avg_sentiment": avg_sent, "total_volume": volume}


def _compute_round_metrics(
    round_actions: List[Dict], cumulative_actions: List[Dict],
    agent_keys: List[str], agent_defs_map: Dict[str, Dict] = None,
    agent_scenario_map: Dict[str, str] = None,
) -> Dict:
    """Compute metrics for a single round."""
    agg = _get_current_aggregate(cumulative_actions, agent_keys, agent_defs_map)

    sentiment_by_persona = {}
    for a in round_actions:
        if a.get("action_type") != "no_action":
            sentiment_by_persona[a["persona"]] = round(a.get("sentiment_score", 0.0), 3)

    active = [a for a in round_actions if a.get("action_type") != "no_action"]
    dominant = ""
    if active:
        top = max(active, key=lambda x: x.get("reach_estimate", 0))
        dominant = top.get("title", "")

    metrics = {
        "avg_sentiment": round(agg["avg_sentiment"], 3),
        "total_volume": agg["total_volume"],
        "round_volume": len(active),
        "sentiment_by_persona": sentiment_by_persona,
        "dominant_narrative": dominant,
    }

    # Per-scenario breakdown (only when multi-scenario)
    if agent_scenario_map:
        scenarios = set(agent_scenario_map.values())
        per_scenario = {}
        for sc in scenarios:
            sc_active = [
                a for a in active
                if agent_scenario_map.get(a.get("persona", "")) == sc
            ]
            sc_cumulative = [
                a for a in cumulative_actions
                if agent_scenario_map.get(a.get("persona", "")) == sc
                and a.get("action_type") != "no_action"
            ]
            sc_sentiment = (
                sum(a.get("sentiment_score", 0) for a in sc_active) / len(sc_active)
                if sc_active else 0.0
            )
            per_scenario[sc] = {
                "avg_sentiment": round(sc_sentiment, 3),
                "round_volume": len(sc_active),
                "total_volume": len(sc_cumulative),
            }

        # Count cross-scenario interactions this round
        cross_count = sum(
            1 for a in active
            for src in a.get("influenced_by", [])
            if agent_scenario_map.get(src, "") != agent_scenario_map.get(a.get("persona", ""), "")
        )

        metrics["per_scenario"] = per_scenario
        metrics["cross_scenario_interactions"] = cross_count

    return metrics


def _summarize_previous_rounds(previous_rounds: List[Dict]) -> str:
    """Compress previous rounds into concise text for context."""
    if not previous_rounds:
        return ""

    lines = []
    for rnd in previous_rounds:
        round_label = rnd["time_label"]
        action_lines = []
        for a in rnd["actions"]:
            if a["action_type"] == "no_action":
                action_lines.append(f"  - {a['persona'].replace('_', ' ').title()}: stayed silent")
            else:
                action_lines.append(
                    f"  - {a['persona'].replace('_', ' ').title()} [{a['action_type']}]: "
                    f"\"{a['title']}\" (sentiment: {a['sentiment_score']:.1f}, "
                    f"reach: {a['reach_estimate']:,})"
                )
        metrics = rnd.get("metrics", {})
        lines.append(
            f"{round_label}:\n"
            + "\n".join(action_lines)
            + f"\n  Aggregate: sentiment={metrics.get('avg_sentiment', 0):.2f}, "
            f"volume={metrics.get('total_volume', 0)}"
        )

    return "\n\n".join(lines)


# --- Summary generation ---

SUMMARY_PROMPT = """You are a senior strategist analyzing the results of a multi-agent scenario simulation.

SCENARIO: {scenario}
SUBJECT: {brand}
{scenario_list_section}
SIMULATION RESULTS ({total_rounds} rounds, {agent_count} agents):
{rounds_text}
{cross_scenario_section}
Produce a final analysis as JSON:
{{
    "final_sentiment": float (-1.0 to 1.0, where things settled),
    "total_volume": integer (total media pieces produced),
    "sentiment_trajectory": [float array, one per round],
    "key_turning_points": ["Round N: description", ...],
    "recommended_actions": ["action1", "action2", ...],
    "narrative_summary": "3-4 paragraph executive summary of how the scenario played out, key dynamics between agents, influence chains, and what should be done"{multi_scenario_fields}
}}"""

MULTI_SCENARIO_SUMMARY_FIELDS = """,
    "per_scenario_summary": {{
        "scenario text here": {{
            "final_sentiment": float,
            "total_volume": int,
            "sentiment_trajectory": [float per round],
            "key_dynamics": "1-2 paragraph summary of this scenario's dynamics"
        }}
    }},
    "cross_scenario_dynamics": "2-3 paragraph analysis of how the scenarios interacted, amplified, or dampened each other",
    "interaction_effects": ["effect1: description of how scenario A affected scenario B", ...]"""


def _compute_cross_scenario_stats(
    influence_log: List[Dict],
    agent_scenario_map: Dict[str, str],
) -> str:
    """Compute cross-scenario influence stats as text for the summary prompt."""
    cross_entries = [e for e in influence_log if e.get("cross_scenario")]
    if not cross_entries:
        return ""

    total_cross = len(cross_entries)
    total_within = len(influence_log) - total_cross

    # Count by scenario pair
    pair_counts: Dict[str, int] = {}
    for e in cross_entries:
        pair = f"{e.get('from_scenario', '?')} -> {e.get('to_scenario', '?')}"
        pair_counts[pair] = pair_counts.get(pair, 0) + 1

    lines = [
        f"CROSS-SCENARIO INFLUENCE DATA:",
        f"- Total within-scenario influences: {total_within}",
        f"- Total cross-scenario influences: {total_cross}",
        "- Scenario pair breakdown:",
    ]
    for pair, count in sorted(pair_counts.items(), key=lambda x: -x[1]):
        lines.append(f"  {pair}: {count} influences")

    return "\n".join(lines)


def _generate_summary(
    client, all_rounds: List[Dict], scenario: str, brand: str, agent_keys: List[str],
    scenarios: List[str] = None, agent_scenario_map: Dict[str, str] = None,
    influence_log: List[Dict] = None,
) -> Dict:
    """Generate final aggregate metrics via Claude."""
    rounds_text = _summarize_previous_rounds(all_rounds)
    multi = scenarios and len(scenarios) > 1

    # Build multi-scenario sections
    if multi:
        scenario_list_section = "SCENARIOS:\n" + "\n".join(
            f"  {i+1}. {sc}" for i, sc in enumerate(scenarios)
        ) + "\n"
        cross_section = _compute_cross_scenario_stats(
            influence_log or [], agent_scenario_map or {}
        )
        cross_scenario_section = cross_section + "\n" if cross_section else ""
        multi_scenario_fields = MULTI_SCENARIO_SUMMARY_FIELDS
    else:
        scenario_list_section = ""
        cross_scenario_section = ""
        multi_scenario_fields = ""

    try:
        result = client.chat_json(
            messages=[{
                "role": "user",
                "content": SUMMARY_PROMPT.format(
                    scenario=scenario,
                    brand=brand,
                    total_rounds=len(all_rounds),
                    agent_count=len(agent_keys),
                    rounds_text=rounds_text,
                    scenario_list_section=scenario_list_section,
                    cross_scenario_section=cross_scenario_section,
                    multi_scenario_fields=multi_scenario_fields,
                ),
            }],
            system="You are a world-class strategist. Provide realistic, actionable analysis.",
            temperature=0.3,
            max_tokens=6144 if multi else 4096,
        )

        result.setdefault("final_sentiment", 0.0)
        result.setdefault("total_volume", 0)
        result.setdefault("sentiment_trajectory", [])
        result.setdefault("key_turning_points", [])
        result.setdefault("recommended_actions", [])
        result.setdefault("narrative_summary", "")
        if multi:
            result.setdefault("per_scenario_summary", {})
            result.setdefault("cross_scenario_dynamics", "")
            result.setdefault("interaction_effects", [])

        return result

    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return {
            "final_sentiment": all_rounds[-1]["metrics"]["avg_sentiment"] if all_rounds else 0,
            "total_volume": sum(r["metrics"]["round_volume"] for r in all_rounds),
            "sentiment_trajectory": [r["metrics"]["avg_sentiment"] for r in all_rounds],
            "key_turning_points": [],
            "recommended_actions": [],
            "narrative_summary": f"Simulation completed with {len(all_rounds)} rounds. Summary generation failed: {e}",
        }


# --- Helper for progress_detail updates ---

def _get_detail(tm: TaskManager, task_id: str) -> Dict:
    """Get a mutable copy of current progress_detail."""
    task = tm.get_task(task_id)
    return copy.deepcopy(task.progress_detail) if task and task.progress_detail else {}


def _update_detail(tm: TaskManager, task_id: str, **updates) -> Dict:
    """Get current detail and apply updates."""
    detail = _get_detail(tm, task_id)
    detail.update(updates)
    return detail
