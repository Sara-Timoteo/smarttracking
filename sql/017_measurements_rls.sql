-- =====================================================================
-- 017_measurements_rls.sql — RLS policies for measurements
-- =====================================================================
-- More policies will be appended in subsequent migrations.

-- 1. SELECT: owner can see their own measurements
CREATE POLICY measurements_select_owner ON measurements
  FOR SELECT
  USING (user_id = auth.uid());