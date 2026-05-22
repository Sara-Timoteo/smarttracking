-- =====================================================================
-- 008_invites.sql — opaque capability tokens (PII-free invite protocol)
-- =====================================================================
CREATE TABLE invites (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  token_hash             text UNIQUE NOT NULL,        -- sha256 hex of opaque token
  granter_id             uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  created_by             uuid NOT NULL REFERENCES profiles(id),
  created_by_role        granted_by_role_enum NOT NULL,
  legal_basis_doc_id     uuid REFERENCES legal_basis_docs(id),
  intended_scope         relationship_scope NOT NULL,
  intended_expires_at    timestamptz,                 -- expiry of resulting relationship
  max_uses               integer NOT NULL DEFAULT 1,
  used_count             integer NOT NULL DEFAULT 0,
  created_at             timestamptz NOT NULL DEFAULT now(),
  expires_at             timestamptz NOT NULL,        -- expiry of invite itself
  revoked_at             timestamptz,
  CHECK (max_uses >= 1),
  CHECK (used_count >= 0 AND used_count <= max_uses),
  CHECK (
    created_by = granter_id
    OR legal_basis_doc_id IS NOT NULL
  )
);

ALTER TABLE invites ENABLE ROW LEVEL SECURITY;
