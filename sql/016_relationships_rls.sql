-- =====================================================================
-- 016_relationships_rls.sql — RLS policies for relationships
-- =====================================================================
-- More policies will be appended in subsequent migrations.

-- 1. SELECT: either party (granter or grantee) can see the relationship
CREATE POLICY relationships_select_party ON relationships
  FOR SELECT
  USING (
    granter_id = auth.uid()
    OR grantee_id = auth.uid()
  );