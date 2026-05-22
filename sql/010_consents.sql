-- =====================================================================
-- 010_consents.sql — Article 9 GDPR explicit consent records
-- =====================================================================
CREATE TABLE consents (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id              uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  consent_type         text NOT NULL,    -- e.g. 'data_collection','data_sharing','analytics'
  purpose              text NOT NULL,
  granted              boolean NOT NULL,
  granted_at           timestamptz NOT NULL DEFAULT now(),
  granted_by           uuid NOT NULL REFERENCES profiles(id),
  granted_by_role      granted_by_role_enum NOT NULL,
  legal_basis_doc_id   uuid REFERENCES legal_basis_docs(id),
  consent_version      integer NOT NULL DEFAULT 1,
  revoked_at           timestamptz,
  revoked_by           uuid REFERENCES profiles(id),
  CHECK (
    granted_by = user_id
    OR legal_basis_doc_id IS NOT NULL
  )
);

ALTER TABLE consents ENABLE ROW LEVEL SECURITY;
