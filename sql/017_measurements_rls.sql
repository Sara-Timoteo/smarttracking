-- =====================================================================
-- 017_measurements_rls.sql — RLS policies for measurements
-- =====================================================================
-- More policies will be appended in subsequent migrations.

-- 1. SELECT: owner can see their own measurements
CREATE POLICY measurements_select_owner ON measurements
  FOR SELECT
  USING (user_id = auth.uid());

  -- 2. SELECT: caregivers with an active grant can see the granter's data
--    Canonical "consent-by-construction" policy (Section 6 of the paper).
CREATE POLICY measurements_select_caregiver ON measurements
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM relationships
      WHERE granter_id = measurements.user_id
        AND grantee_id = auth.uid()
        AND scope IN ('full_history','daily_summary','vital_alerts','emergency_only')
        AND revoked_at IS NULL
        AND (expires_at IS NULL OR expires_at > now())
    )
  );