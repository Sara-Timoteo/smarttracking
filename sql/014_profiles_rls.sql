-- =====================================================================
-- 014_profiles_rls.sql — RLS policies for the profiles table
-- =====================================================================
-- Requires 013_helpers.sql to be applied first (uses public.is_admin()).
-- We may append additional policies here in subsequent migrations.

-- 1. Read your own profile
CREATE POLICY profiles_select_self ON profiles
  FOR SELECT
  USING (id = auth.uid());

-- 2. Update your own profile
CREATE POLICY profiles_update_self ON profiles
  FOR UPDATE
  USING (id = auth.uid())
  WITH CHECK (id = auth.uid());

-- 3. Read profiles of people who have granted you access
CREATE POLICY profiles_select_via_grant ON profiles
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM relationships
      WHERE granter_id = profiles.id
        AND grantee_id = auth.uid()
        AND revoked_at IS NULL
        AND (expires_at IS NULL OR expires_at > now())
    )
  );

-- 4. Admin override: full access to all profiles
CREATE POLICY profiles_admin_all ON profiles
  FOR ALL
  USING (public.is_admin());
