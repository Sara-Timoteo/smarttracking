-- =====================================================================
-- 020_complete_remaining_rls.sql — Complete the RLS layer
-- =====================================================================
-- This migration adds all remaining RLS policies for tables that did not
-- yet have full coverage. heartbeat is intentionally left without any
-- policies (only service_role accesses it).
--
-- Tables covered:
--   - consents (UPDATE + admin)
--   - relationships (admin)
--   - measurements (admin)
--   - invites (UPDATE + admin)
--   - audit_log (SELECT + admin)
--   - legal_basis_docs (SELECT + INSERT + admin)
--   - primary_representatives (SELECT + INSERT + UPDATE + admin)
-- =====================================================================

-- ---------------------------------------------------------------------
-- consents — additional policies
-- ---------------------------------------------------------------------

-- UPDATE: user can update their own consents (typically to revoke)
CREATE POLICY consents_update_own ON consents
  FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

-- Admin override: full access
CREATE POLICY consents_admin_all ON consents
  FOR ALL
  USING (public.is_admin());

-- ---------------------------------------------------------------------
-- relationships — additional policies
-- ---------------------------------------------------------------------

-- Admin override: full access
CREATE POLICY relationships_admin_all ON relationships
  FOR ALL
  USING (public.is_admin());

-- ---------------------------------------------------------------------
-- measurements — additional policies
-- ---------------------------------------------------------------------

-- Admin override: full access
CREATE POLICY measurements_admin_all ON measurements
  FOR ALL
  USING (public.is_admin());

-- ---------------------------------------------------------------------
-- invites — additional policies
-- ---------------------------------------------------------------------

-- UPDATE: granter or creator can update (typically to revoke)
CREATE POLICY invites_update_party ON invites
  FOR UPDATE
  USING (granter_id = auth.uid() OR created_by = auth.uid())
  WITH CHECK (granter_id = auth.uid() OR created_by = auth.uid());

-- Admin override: full access
CREATE POLICY invites_admin_all ON invites
  FOR ALL
  USING (public.is_admin());

-- ---------------------------------------------------------------------
-- audit_log — append-only observability
-- ---------------------------------------------------------------------
-- No INSERT policy for users: audit entries are written server-side via
-- service_role only. SELECT is restricted to the parties an entry
-- concerns, plus admins.

-- SELECT: actor and subject can see entries about themselves
CREATE POLICY audit_log_select_party ON audit_log
  FOR SELECT
  USING (
    actor_id = auth.uid()
    OR subject_id = auth.uid()
  );

-- Admin override: full access (read + write for audit ingestion)
CREATE POLICY audit_log_admin_all ON audit_log
  FOR ALL
  USING (public.is_admin());

-- ---------------------------------------------------------------------
-- legal_basis_docs — legal documents supporting paths B, C, D
-- ---------------------------------------------------------------------

-- SELECT: subject and uploader can see the doc
CREATE POLICY legal_basis_docs_select_party ON legal_basis_docs
  FOR SELECT
  USING (
    subject_id = auth.uid()
    OR uploaded_by = auth.uid()
  );

-- INSERT: user can upload docs for themselves (Path A use case;
--   delegated uploads go via service_role with verification)
CREATE POLICY legal_basis_docs_insert_self ON legal_basis_docs
  FOR INSERT
  WITH CHECK (
    uploaded_by = auth.uid()
    AND subject_id = auth.uid()
  );

-- Admin override: verification + full access
CREATE POLICY legal_basis_docs_admin_all ON legal_basis_docs
  FOR ALL
  USING (public.is_admin());

-- ---------------------------------------------------------------------
-- primary_representatives — Path B (Springing Power) designations
-- ---------------------------------------------------------------------

-- SELECT: subject or representative can see the designation
CREATE POLICY primary_reps_select_party ON primary_representatives
  FOR SELECT
  USING (
    subject_id = auth.uid()
    OR representative_id = auth.uid()
  );

-- INSERT: subject can designate (only themselves as subject)
CREATE POLICY primary_reps_insert_self ON primary_representatives
  FOR INSERT
  WITH CHECK (subject_id = auth.uid());

-- UPDATE: subject can revoke (sets revoked_at)
CREATE POLICY primary_reps_update_subject ON primary_representatives
  FOR UPDATE
  USING (subject_id = auth.uid())
  WITH CHECK (subject_id = auth.uid());

-- Admin override: activate, manage all
CREATE POLICY primary_reps_admin_all ON primary_representatives
  FOR ALL
  USING (public.is_admin());
