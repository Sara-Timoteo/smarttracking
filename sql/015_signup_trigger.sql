-- =====================================================================
-- 015_signup_trigger.sql — auto-create profile when a user signs up
-- =====================================================================
-- When a new user is created via Supabase Auth, a row appears in
-- auth.users. This trigger fires AFTER that insert and creates the
-- corresponding row in public.profiles, pulling optional fields from
-- raw_user_meta_data when available.

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  INSERT INTO public.profiles (id, display_name, onboarding_path)
  VALUES (
    NEW.id,
    COALESCE(
      NEW.raw_user_meta_data->>'display_name',
      split_part(NEW.email, '@', 1)
    ),
    COALESCE(
      (NEW.raw_user_meta_data->>'onboarding_path')::granted_by_role_enum,
      'self'
    )
  );
  RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();
