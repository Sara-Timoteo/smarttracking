-- =====================================================================
-- 005_profiles.sql — extends auth.users 1:1 with project-specific fields
-- =====================================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- for gen_random_uuid()

CREATE TABLE profiles (
  id                uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  pseudonym         uuid UNIQUE NOT NULL DEFAULT gen_random_uuid(),
  display_name      text NOT NULL,
  preferred_lang    text NOT NULL DEFAULT 'pt' 
                    CHECK (preferred_lang IN ('pt','en','es')),
  onboarding_path   granted_by_role_enum NOT NULL DEFAULT 'self',
  is_admin          boolean NOT NULL DEFAULT false,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
