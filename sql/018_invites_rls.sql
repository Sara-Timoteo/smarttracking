-- =====================================================================
-- 018_invites_rls.sql — RLS policies for invites
-- =====================================================================
-- More policies will be appended in subsequent migrations.

-- 1. SELECT: granter (data subject) or creator can see the invite
CREATE POLICY invites_select_party ON invites
  FOR SELECT
  USING (
    granter_id = auth.uid()
    OR created_by = auth.uid()
  );

  -- 2. INSERT: user can create invites for themselves (Path A only)
--    Paths B, C, D go through service_role with legal-basis verification.
CREATE POLICY invites_insert_self ON invites
  FOR INSERT
  WITH CHECK (
    created_by = auth.uid()
    AND granter_id = auth.uid()
  );

