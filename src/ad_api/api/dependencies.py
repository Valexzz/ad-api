from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from starlette import status

from ad_api.adapters.conn import LdapClient
from ad_api.adapters.usuario_ldap_repository import UsuarioLdapRepository
from ad_api.config import settings
from ad_api.errors import InfraError, ChaveApiInvalidaError
from ad_api.services.usuario_service import UsuarioService


def get_usuario_service() -> UsuarioService:
    ldap_client = LdapClient()
    repository = UsuarioLdapRepository(ldap_client)
    return UsuarioService(repository)

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

def verificar_api_key(api_key: str = Security(api_key_header)):
    if not api_key or api_key != settings.chave_api:
        raise ChaveApiInvalidaError(
            "Chave de API inválida ou ausente"
        )
    return api_key