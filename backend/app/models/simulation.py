"""Simulation model — persists completed multi-agent PR simulations"""

import uuid
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from ..db import execute_query, execute_one, execute_write


@dataclass
class Simulation:
    simulation_id: str = ""
    monitor_id: str = ""
    scenario: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    status: str = "completed"
    total_rounds: int = 6
    rounds: List[Dict] = field(default_factory=list)
    aggregate_metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    agent_states: Dict[str, Any] = field(default_factory=dict)
    influence_log: List[Dict] = field(default_factory=list)
    historical_briefing: Optional[str] = None
    engine_version: str = "v1"

    def to_dict(self):
        return {
            "simulation_id": self.simulation_id,
            "monitor_id": self.monitor_id,
            "scenario": self.scenario,
            "config": self.config,
            "status": self.status,
            "total_rounds": self.total_rounds,
            "rounds": self.rounds,
            "aggregate_metrics": self.aggregate_metrics,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "agent_states": self.agent_states,
            "influence_log": self.influence_log,
            "historical_briefing": self.historical_briefing,
            "engine_version": self.engine_version,
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None

        def _parse_json(val, default):
            if val is None:
                return default
            if isinstance(val, (dict, list)):
                return val
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                return default

        return cls(
            simulation_id=row['simulation_id'],
            monitor_id=row['monitor_id'],
            scenario=row['scenario'],
            config=_parse_json(row['config'], {}),
            status=row['status'],
            total_rounds=row['total_rounds'],
            rounds=_parse_json(row['rounds'], []),
            aggregate_metrics=_parse_json(row['aggregate_metrics'], {}),
            created_at=row['created_at'].isoformat() if row.get('created_at') else None,
            completed_at=row['completed_at'].isoformat() if row.get('completed_at') else None,
            agent_states=_parse_json(row.get('agent_states'), {}),
            influence_log=_parse_json(row.get('influence_log'), []),
            historical_briefing=row.get('historical_briefing'),
            engine_version=row.get('engine_version', 'v1'),
        )

    @classmethod
    def create(cls, simulation_id, monitor_id, scenario, config, total_rounds,
               rounds, aggregate_metrics, agent_states=None, influence_log=None,
               historical_briefing=None, engine_version="v1"):
        execute_write(
            """INSERT INTO simulations
               (simulation_id, monitor_id, scenario, config, status, total_rounds,
                rounds, aggregate_metrics, agent_states, influence_log,
                historical_briefing, engine_version, completed_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
            (simulation_id, monitor_id, scenario,
             json.dumps(config), 'completed', total_rounds,
             json.dumps(rounds), json.dumps(aggregate_metrics),
             json.dumps(agent_states or {}), json.dumps(influence_log or []),
             historical_briefing, engine_version)
        )
        return cls.get_by_id(simulation_id)

    @classmethod
    def get_by_id(cls, simulation_id):
        row = execute_one("SELECT * FROM simulations WHERE simulation_id = %s",
                          (simulation_id,))
        return cls.from_row(row)

    @classmethod
    def list_by_monitor(cls, monitor_id, limit=10):
        rows = execute_query(
            "SELECT * FROM simulations WHERE monitor_id = %s ORDER BY created_at DESC LIMIT %s",
            (monitor_id, limit)
        )
        return [cls.from_row(r) for r in (rows or [])]

    @classmethod
    def list_recent(cls, limit=10):
        rows = execute_query(
            "SELECT * FROM simulations ORDER BY created_at DESC LIMIT %s",
            (limit,)
        )
        return [cls.from_row(r) for r in (rows or [])]
