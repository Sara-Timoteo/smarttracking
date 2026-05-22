-- =====================================================================
-- 012_audit_log.sql — append-only observability and compliance trail
-- =====================================================================
CREATE TABLE audit_log (
  id              bigserial PRIMARY KEY,
  actor_id        uuid REFERENCES profiles(id),
  subject_id      uuid REFERENCES profiles(id),
  action          text NOT NULL,   -- 'invite.create','invite.redeem','data.view',...
  details         jsonb,
  ip_address      inet,
  user_agent      text,
  occurred_at     timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
