-- ILLUSTRATIVE PostgreSQL schema for SYNTHETIC data only.
-- Never load actual patient-level information into a public portfolio environment.
CREATE SCHEMA IF NOT EXISTS demo_research;

CREATE TABLE IF NOT EXISTS demo_research.registry (
    case_id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL,
    recipient_age INTEGER,
    transplant_date DATE,
    graft_status TEXT
);

CREATE TABLE IF NOT EXISTS demo_research.redcap (
    case_id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL,
    anesthesia_start TIMESTAMP,
    anesthesia_end TIMESTAMP,
    asa_class TEXT
);

CREATE TABLE IF NOT EXISTS demo_research.anesthesia (
    case_id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL,
    ebl_ml INTEGER,
    anesthesia_minutes INTEGER
);

-- In real workflows, raw submissions would be stored and audited before
-- applying constraints; this schema represents deduplicated staging tables.
