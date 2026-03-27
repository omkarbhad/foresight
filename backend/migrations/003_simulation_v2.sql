-- Migration 003: Simulation v2 — CrewAI multi-agent engine support
-- Adds columns for agent states, influence tracking, historical context, and engine version.
-- Backward compatible: old v1 simulations use defaults.

ALTER TABLE simulations ADD COLUMN IF NOT EXISTS agent_states JSONB DEFAULT '{}';
ALTER TABLE simulations ADD COLUMN IF NOT EXISTS influence_log JSONB DEFAULT '[]';
ALTER TABLE simulations ADD COLUMN IF NOT EXISTS historical_briefing TEXT;
ALTER TABLE simulations ADD COLUMN IF NOT EXISTS engine_version TEXT DEFAULT 'v1';
