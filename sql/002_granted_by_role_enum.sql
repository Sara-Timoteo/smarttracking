-- =====================================================================
-- 002_granted_by_role_enum.sql — onboarding paths (A, B, C, D)
-- =====================================================================
CREATE TYPE granted_by_role_enum AS ENUM (
  'self',           -- Path A: self-directed
  'representative', -- Path B: anticipatory delegation (springing power)
  'acompanhante',   -- Path C: Lei 49/2018 acompanhamento
  'institution'     -- Path D: institutional fiduciary
);
