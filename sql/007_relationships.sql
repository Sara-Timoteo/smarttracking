-- =====================================================================
-- 007_relationships.sql — caregiver access grants (heart of consent model)
-- =====================================================================
CREATE TABLE relationships (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  granter_id           uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  grantee_id           uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  scope                relationship_scope NOT NULL,
  granted_by           uuid NOT NULL REFERENCES profiles(id),
  granted_by_role      granted_by_role_enum NOT NULL,
  legal_basis_doc_id   uuid REFERENCES legal_basis_docs(id),
  granted_at           timestamptz NOT NULL DEFAULT now(),
  expires_at           timestamptz,
  revoked_at           timestamptz,
  revoked_by           uuid REFERENCES profiles(id),
  UNIQUE(granter_id, grantee_id, scope),
  CHECK (granter_id != grantee_id),
  CHECK (
    granted_by = granter_id
    OR legal_basis_doc_id IS NOT NULL
  )
);

ALTER TABLE relationships ENABLE ROW LEVEL SECURITY;
