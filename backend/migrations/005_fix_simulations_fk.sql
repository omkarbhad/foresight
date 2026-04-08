-- Make monitor_id nullable and drop the FK constraint
ALTER TABLE simulations ALTER COLUMN monitor_id DROP NOT NULL;
ALTER TABLE simulations DROP CONSTRAINT IF EXISTS simulations_monitor_id_fkey;
