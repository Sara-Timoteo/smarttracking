-- =====================================================================
-- 019_consents_rls.sql — RLS policies for consents
-- =====================================================================
-- More policies will be appended in subsequent migrations.

-- 1. SELECT: user can see their own consent records
CREATE POLICY consents_select_own ON consents
  FOR SELECT
  USING (user_id = auth.uid());

  -- 2. INSERT: user can record their own consents (Path A)
--    Paths B/C/D go through service_role with legal-basis verification.
CREATE POLICY consents_insert_own ON consents
  FOR INSERT
  WITH CHECK (
    user_id = auth.uid()
    AND granted_by = auth.uid()
  );