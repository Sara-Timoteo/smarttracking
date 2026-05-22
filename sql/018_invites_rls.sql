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