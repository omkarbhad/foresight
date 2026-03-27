-- Foresight Initial Schema

CREATE TABLE IF NOT EXISTS monitors (
    monitor_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    keywords TEXT[] NOT NULL,
    negative_keywords TEXT[] DEFAULT '{}',
    sources TEXT[] DEFAULT '{news,reddit,twitter}',
    alert_threshold REAL DEFAULT 0.7,
    competitors TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mentions (
    mention_id TEXT PRIMARY KEY,
    monitor_id TEXT REFERENCES monitors(monitor_id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    source_url TEXT,
    title TEXT,
    content TEXT,
    author TEXT,
    published_at TIMESTAMPTZ,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    sentiment_score REAL,
    sentiment_label TEXT,
    reach_estimate INTEGER,
    crisis_score REAL,
    amplify_worthy BOOLEAN DEFAULT FALSE,
    analysis_summary TEXT,
    topics TEXT[],
    content_hash TEXT NOT NULL,
    is_duplicate BOOLEAN DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_mentions_monitor ON mentions(monitor_id);
CREATE INDEX IF NOT EXISTS idx_mentions_ingested ON mentions(ingested_at);
CREATE INDEX IF NOT EXISTS idx_mentions_crisis ON mentions(crisis_score);
CREATE INDEX IF NOT EXISTS idx_mentions_hash ON mentions(content_hash);
CREATE INDEX IF NOT EXISTS idx_mentions_sentiment ON mentions(sentiment_score);

CREATE TABLE IF NOT EXISTS alert_events (
    event_id TEXT PRIMARY KEY,
    monitor_id TEXT REFERENCES monitors(monitor_id) ON DELETE CASCADE,
    mention_id TEXT REFERENCES mentions(mention_id),
    crisis_score REAL,
    delivered_via TEXT[] DEFAULT '{}',
    delivered_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS digests (
    digest_id TEXT PRIMARY KEY,
    monitor_id TEXT REFERENCES monitors(monitor_id) ON DELETE CASCADE,
    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    summary TEXT,
    stats JSONB,
    top_mention_ids TEXT[]
);
