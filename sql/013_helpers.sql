-- =====================================================================
-- 013_helpers.sql — helper functions used by RLS policies
-- =====================================================================
-- These functions are SECURITY DEFINER so they bypass RLS internally
-- and can be safely called from within RLS policies on the same tables.
-- auth.uid() always returns the JWT 'sub' claim regardless.
--
-- NOTE: must be applied BEFORE 014_profiles_rls.sql, which uses is_admin().

-- is_admin() — TRUE if the calling user has profiles.is_admin = true
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT COALESCE(
    (SELECT is_admin FROM public.profiles WHERE id = auth.uid()),
    false
  );
$$;
