-- PR Simulation Engine schema

CREATE TABLE IF NOT EXISTS simulations (
    simulation_id TEXT PRIMARY KEY,
    monitor_id TEXT REFERENCES monitors(monitor_id) ON DELETE CASCADE,
    scenario TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'completed',
    total_rounds INTEGER NOT NULL,
    rounds JSONB NOT NULL,
    aggregate_metrics JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_simulations_monitor ON simulations(monitor_id);
CREATE INDEX IF NOT EXISTS idx_simulations_created ON simulations(created_at);
