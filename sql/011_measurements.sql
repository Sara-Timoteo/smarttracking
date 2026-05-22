-- =====================================================================
-- 011_measurements.sql — actual wearable health data
-- =====================================================================
CREATE TABLE measurements (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  source              text NOT NULL,          -- 'huawei_health','manual_import','sync_auto'
  metric_type         text NOT NULL,          -- 'steps','heart_rate','sleep_duration_min',...
  metric_value        numeric NOT NULL,
  unit                text,
  measured_at         timestamptz NOT NULL,
  imported_at         timestamptz NOT NULL DEFAULT now(),
  raw_payload_hash    text,
  UNIQUE(user_id, metric_type, measured_at, raw_payload_hash)
);

ALTER TABLE measurements ENABLE ROW LEVEL SECURITY;
