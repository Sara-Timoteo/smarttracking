-- =====================================================================
-- 006_legal_basis_docs.sql — legal documents supporting paths B, C, D
-- =====================================================================
CREATE TABLE legal_basis_docs (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  doc_type         doc_type_enum NOT NULL,
  subject_id       uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  storage_path     text NOT NULL,
  uploaded_by      uuid NOT NULL REFERENCES profiles(id),
  uploaded_at      timestamptz NOT NULL DEFAULT now(),
  verified_at      timestamptz,
  verified_by      uuid REFERENCES profiles(id),
  notes            text
);

ALTER TABLE legal_basis_docs ENABLE ROW LEVEL SECURITY;
