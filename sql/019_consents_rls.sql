-- =====================================================================
-- 019_consents_rls.sql — RLS policies for consents
-- =====================================================================
-- More policies will be appended in subsequent migrations.

-- 1. SELECT: user can see their own consent records
CREATE POLICY consents_select_own ON consents
  FOR SELECT
  USING (user_id = auth.uid());