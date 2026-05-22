-- =====================================================================
-- 004_doc_type_enum.sql — legal document types (paths B, C, D)
-- =====================================================================
CREATE TYPE doc_type_enum AS ENUM (
  'acompanhante',           -- Path C: Lei 49/2018 court decree
  'springing_power',        -- Path B: anticipatory delegation activation
  'institution_protocol',   -- Path D: fiduciary protocol with family
  'medical_certification'   -- physician declaration of incapacity
);
