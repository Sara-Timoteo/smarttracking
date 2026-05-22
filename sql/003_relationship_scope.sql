-- =====================================================================
-- 003_relationship_scope.sql — five caregiver access scopes
-- =====================================================================
CREATE TYPE relationship_scope AS ENUM (
  'vital_alerts',    -- critical out-of-band events only
  'daily_summary',   -- aggregated daily metrics
  'full_history',    -- complete time series
  'consent_proxy',   -- modify consents on behalf of granter (needs legal basis)
  'emergency_only'   -- temporary, SOS-triggered
);
