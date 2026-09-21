from contextlib import contextmanager

from ad_api.adapters.usuario_ldap_repository import UsuarioLdapRepository
from ad_api.domain.model import StatusUsuario


class FakeLdapClient:
    def __init__(self, conn):
        self._conn = conn

    @contextmanager
    def get_conn(self):
        yield self._conn

def test_buscar_por_login_deve_retornar_usuario(ldap_mock_conn):
    client = FakeLdapClient(ldap_mock_conn)
    repo = UsuarioLdapRepository(ldap_client=client)

    usuario = repo.buscar_por_login("victor")

    assert usuario is not None
    assert usuario.login == "victor"
    assert usuario.primeiro_nome == "Victor"
    assert usuario.sobrenome == "Alexandre Borges Milhomem"
    assert usuario.status == StatusUsuario.ATIVO
    assert usuario.matricula == "12345"
    assert usuario.get_nome_completo() == "Victor Alexandre Borges Milhomem"

def test_buscar_por_login_deve_retornar_none_quando_usuario_nao_existir(ldap_mock_conn):
    client = FakeLdapClient(ldap_mock_conn)
    repo = UsuarioLdapRepository(ldap_client=client)

    usuario = repo.buscar_por_login("usuario_inexistente")

    assert usuario is None