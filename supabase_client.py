"""Cliente Supabase - lado servidor, com a chave service_role (bypass ao RLS)."""
from functools import lru_cache

from supabase import Client, create_client

from config import Config, require_service_role


@lru_cache(maxsize=1)
def get_client() -> Client:
    """Devolve um cliente Supabase autenticado com a service_role.

    A service_role ignora o RLS. Usar apenas do lado servidor, nunca exposta.
    """
    require_service_role()
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)