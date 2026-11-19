-- PostgreSQL 14+: typed analytical layer built from synthetic, validated CSVs.
-- This schema intentionally contains no customer identity fields.
CREATE SCHEMA IF NOT EXISTS ops;

CREATE TABLE IF NOT EXISTS ops.agent_dimension (
  agent_id text PRIMARY KEY,
  home_region text NOT NULL,
  primary_channel text NOT NULL,
  active boolean NOT NULL
);

CREATE TABLE IF NOT EXISTS ops.workforce_shifts (
  shift_date date NOT NULL,
  region text NOT NULL,
  scheduled_agent_hours numeric(10, 1) NOT NULL,
  shift_source text NOT NULL,
  PRIMARY KEY (shift_date, region)
);

CREATE TABLE IF NOT EXISTS ops.clean_ticket_fact (
  ticket_id text PRIMARY KEY,
  region text NOT NULL,
  agent_id text NOT NULL REFERENCES ops.agent_dimension(agent_id),
  channel text NOT NULL,
  category text NOT NULL,
  priority text NOT NULL,
  opened_at_utc timestamptz NOT NULL,
  resolved_at_utc timestamptz NOT NULL,
  sla_target_minutes integer NOT NULL CHECK (sla_target_minutes > 0),
  resolution_minutes numeric(12, 1) NOT NULL CHECK (resolution_minutes >= 0),
  sla_breached boolean NOT NULL,
  ticket_day date NOT NULL
);

CREATE INDEX IF NOT EXISTS ticket_fact_region_day ON ops.clean_ticket_fact (region, ticket_day);
CREATE INDEX IF NOT EXISTS ticket_fact_agent_id ON ops.clean_ticket_fact (agent_id);

-- Run imports from the repository root in psql, in this order:
-- \copy ops.agent_dimension FROM 'data/raw/agents.csv' WITH (FORMAT csv, HEADER true);
-- \copy ops.workforce_shifts FROM 'data/raw/shifts.csv' WITH (FORMAT csv, HEADER true);
-- \copy ops.clean_ticket_fact FROM 'outputs/clean_tickets.csv' WITH (FORMAT csv, HEADER true);
-- A deliberately negative staffing record is present to test audit logic.
-- It is imported as raw evidence, never treated as valid hours in analytical joins.
