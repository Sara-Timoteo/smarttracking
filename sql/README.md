# SQL Migrations

Database migrations for the SmartTracking schema. Files are numbered to indicate
the order in which they should be applied to a fresh database.

| # | File | Purpose |
|---|------|---------|
| 001 | `001_heartbeat.sql` | Anti-pause table for Supabase free tier |
| 002 | `002_granted_by_role_enum.sql` | ENUM: onboarding paths (A–D) |
| 003 | `003_relationship_scope.sql` | ENUM: caregiver access scopes |
| 004 | `004_doc_type_enum.sql` | ENUM: legal document types |
| 005 | `005_profiles.sql` | Extends `auth.users` with project-specific fields |
| 006 | `006_legal_basis_docs.sql` | Documents supporting paths B, C, D |
| 007 | `007_relationships.sql` | Caregiver access grants (core of consent model) |
| 008 | `008_invites.sql` | Opaque capability tokens (PII-free invite protocol) |
| 009 | `009_primary_representatives.sql` | Springing-power dormant designations (Path B) |
| 010 | `010_consents.sql` | Article 9 GDPR explicit consent records |
| 011 | `011_measurements.sql` | Wearable health data |
| 012 | `012_audit_log.sql` | Append-only observability and compliance trail |
| 013 | `013_helpers.sql` | Helper functions used by RLS policies (`is_admin()`) |
| 014 | `014_profiles_rls.sql` | RLS policies for the `profiles` table |
| 015 | `015_signup_trigger.sql` | Auto-create profile when a user signs up |

Migrations on the Supabase project `smarttracking` are already applied (state as
of the last reconstruction). These files exist primarily for version control
and to enable replay against a fresh Supabase project if needed.

To apply against a fresh project: run each file in sequence in the Supabase
SQL Editor.
