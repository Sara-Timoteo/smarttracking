CREATE OR REPLACE FUNCTION resolve_import_user_id(p_token_hash text)
RETURNS uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT granter_id
  FROM invites
  WHERE token_hash = p_token_hash
    AND intended_scope = 'data_source'
    AND revoked_at IS NULL
    AND expires_at > now()
  LIMIT 1;
$$;

REVOKE EXECUTE ON FUNCTION resolve_import_user_id(text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION resolve_import_user_id(text) FROM anon, authenticated;
GRANT EXECUTE ON FUNCTION resolve_import_user_id(text) TO service_role;