
-- 001_heartbeat.sql — anti-pause table for Supabase free tier
-- RLS enabled with no policies => only service_role can access

CREATE TABLE heartbeat (
  id        bigserial PRIMARY KEY,
  ping_at   timestamptz NOT NULL DEFAULT now(),
  source    text DEFAULT 'github_actions'
);

ALTER TABLE heartbeat ENABLE ROW LEVEL SECURITY;
