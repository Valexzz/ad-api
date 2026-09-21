from ad_api.adapters.conn import LdapClient
from ad_api.adapters.usuario_ldap_repository import UsuarioLdapRepository
from ad_api.services.usuario_service import UsuarioService


def get_usuario_service() -> UsuarioService:
    ldap_client = LdapClient()
    repository = UsuarioLdapRepository(ldap_client)
    return UsuarioService(repository)