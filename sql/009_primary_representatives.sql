-- =====================================================================
-- 009_primary_representatives.sql — Path B (Springing Power) dormant designations
-- =====================================================================
CREATE TABLE primary_representatives (
  id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_id               uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  representative_id        uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  activation_conditions    jsonb NOT NULL,
  designated_at            timestamptz NOT NULL DEFAULT now(),
  activated_at             timestamptz,
  activated_reason         text,
  activated_by             uuid REFERENCES profiles(id),
  revoked_at               timestamptz,
  revoked_by               uuid REFERENCES profiles(id),
  UNIQUE(subject_id, representative_id),
  CHECK (subject_id != representative_id)
);

ALTER TABLE primary_representatives ENABLE ROW LEVEL SECURITY;
