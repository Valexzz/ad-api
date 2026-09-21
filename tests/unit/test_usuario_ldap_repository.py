from contextlib import contextmanager
import pytest
from ldap3 import Server, Connection, MOCK_SYNC, OFFLINE_AD_2012_R2

from ad_api.adapters.conn import LdapClient
from ad_api.adapters.usuario_ldap_repository import UsuarioLdapRepository
from ad_api.domain.model import StatusUsuario

# Constantes - Usuário Ativo Completo
LOGIN_USUARIO_ATIVO = "victor"
PRIMEIRO_NOME_USUARIO_ATIVO = "Victor"
SEGUNDO_NOME_USUARIO_ATIVO = "Alexandre Borges Milhomem"
MATRICULA_USUARIO_ATIVO = "12345"

# Constantes - Usuário Inativo
LOGIN_USUARIO_INATIVO = "maria"
PRIMEIRO_NOME_USUARIO_INATIVO = "Maria"
SEGUNDO_NOME_USUARIO_INATIVO = "Souza"
MATRICULA_USUARIO_INATIVO = "67890"

# Constantes - Casos de Borda (Campos Ausentes)
LOGIN_SEM_MATRICULA = "carlos.sem.matricula"
PRIMEIRO_NOME_SEM_MATRICULA = "Carlos"
SEGUNDO_NOME_SEM_MATRICULA = "Ferreira"

LOGIN_SEM_PRIMEIRO_NOME = "sem.primeironome"
SEGUNDO_NOME_SEM_PRIMEIRO_NOME = "Almeida"
MATRICULA_SEM_PRIMEIRO_NOME = "11223"

LOGIN_SEM_SEGUNDO_NOME = "lucas.sem.segundonome"
PRIMEIRO_NOME_SEM_SEGUNDO_NOME = "Lucas"
MATRICULA_SEM_SEGUNDO_NOME = "44556"

LOGIN_INEXISTENTE = "usuario.inexistente"


class FakeLdapClient(LdapClient):
    def __init__(self, conn: Connection):
        self._conn = conn

    @contextmanager
    def get_conn(self):
        yield self._conn


@pytest.fixture
def ldap_mock_conn():
    server = Server("server_ad_fake", get_info=OFFLINE_AD_2012_R2)

    conn = Connection(
        server,
        user="cn=admin,dc=fake,dc=local",
        password="senhaSuperSegura@123",
        client_strategy=MOCK_SYNC,
    )
    conn.bind()

    # 1. Usuário Completo Ativo
    conn.strategy.add_entry(
        f"CN={LOGIN_USUARIO_ATIVO},OU=Users,DC=fake,DC=local",
        {
            "objectCategory": "person",
            "objectClass": ["top", "person", "organizationalPerson", "user"],
            "sAMAccountName": LOGIN_USUARIO_ATIVO,
            "givenName": PRIMEIRO_NOME_USUARIO_ATIVO,
            "sn": SEGUNDO_NOME_USUARIO_ATIVO,
            "userAccountControl": 512,
            "employeeID": MATRICULA_USUARIO_ATIVO,
        },
    )

    # 2. Usuário Inativo
    conn.strategy.add_entry(
        f"CN={LOGIN_USUARIO_INATIVO},OU=Users,DC=fake,DC=local",
        {
            "objectCategory": "person",
            "objectClass": ["top", "person", "organizationalPerson", "user"],
            "sAMAccountName": LOGIN_USUARIO_INATIVO,
            "givenName": PRIMEIRO_NOME_USUARIO_INATIVO,
            "sn": SEGUNDO_NOME_USUARIO_INATIVO,
            "userAccountControl": 514,
            "employeeID": MATRICULA_USUARIO_INATIVO,
        },
    )

    # 3. Usuário sem Matrícula (employeeID omitido)
    conn.strategy.add_entry(
        f"CN={LOGIN_SEM_MATRICULA},OU=Users,DC=fake,DC=local",
        {
            "objectCategory": "person",
            "objectClass": ["top", "person", "organizationalPerson", "user"],
            "sAMAccountName": LOGIN_SEM_MATRICULA,
            "givenName": PRIMEIRO_NOME_SEM_MATRICULA,
            "sn": SEGUNDO_NOME_SEM_MATRICULA,
            "userAccountControl": 512,
        },
    )

    # 4. Usuário sem Primeiro Nome (givenName omitido)
    conn.strategy.add_entry(
        f"CN={LOGIN_SEM_PRIMEIRO_NOME},OU=Users,DC=fake,DC=local",
        {
            "objectCategory": "person",
            "objectClass": ["top", "person", "organizationalPerson", "user"],
            "sAMAccountName": LOGIN_SEM_PRIMEIRO_NOME,
            "sn": SEGUNDO_NOME_SEM_PRIMEIRO_NOME,
            "userAccountControl": 512,
            "employeeID": MATRICULA_SEM_PRIMEIRO_NOME,
        },
    )

    # 5. Usuário sem Segundo Nome (sn omitido)
    conn.strategy.add_entry(
        f"CN={LOGIN_SEM_SEGUNDO_NOME},OU=Users,DC=fake,DC=local",
        {
            "objectCategory": "person",
            "objectClass": ["top", "person", "organizationalPerson", "user"],
            "sAMAccountName": LOGIN_SEM_SEGUNDO_NOME,
            "givenName": PRIMEIRO_NOME_SEM_SEGUNDO_NOME,
            "userAccountControl": 512,
            "employeeID": MATRICULA_SEM_SEGUNDO_NOME,
        },
    )

    return conn


def test_buscar_por_login_deve_retornar_usuario_sem_matricula(ldap_mock_conn):
    client = FakeLdapClient(ldap_mock_conn)
    repo = UsuarioLdapRepository(ldap_client=client)

    usuario = repo.buscar_por_login(LOGIN_SEM_MATRICULA)

    assert usuario is not None
    assert usuario.login == LOGIN_SEM_MATRICULA
    assert usuario.primeiro_nome == PRIMEIRO_NOME_SEM_MATRICULA
    assert usuario.sobrenome == SEGUNDO_NOME_SEM_MATRICULA
    assert usuario.matricula is None
    assert usuario.nome_completo == f"{PRIMEIRO_NOME_SEM_MATRICULA} {SEGUNDO_NOME_SEM_MATRICULA}"


def test_buscar_por_login_deve_retornar_usuario_sem_primeiro_nome(ldap_mock_conn):
    client = FakeLdapClient(ldap_mock_conn)
    repo = UsuarioLdapRepository(ldap_client=client)

    usuario = repo.buscar_por_login(LOGIN_SEM_PRIMEIRO_NOME)

    assert usuario is not None
    assert usuario.login == LOGIN_SEM_PRIMEIRO_NOME
    assert usuario.primeiro_nome == ""
    assert usuario.sobrenome == SEGUNDO_NOME_SEM_PRIMEIRO_NOME
    assert usuario.matricula == MATRICULA_SEM_PRIMEIRO_NOME
    assert usuario.nome_completo == f"{SEGUNDO_NOME_SEM_PRIMEIRO_NOME}"


def test_buscar_por_login_deve_retornar_usuario_sem_segundo_nome(ldap_mock_conn):
    client = FakeLdapClient(ldap_mock_conn)
    repo = UsuarioLdapRepository(ldap_client=client)

    usuario = repo.buscar_por_login(LOGIN_SEM_SEGUNDO_NOME)

    assert usuario is not None
    assert usuario.login == LOGIN_SEM_SEGUNDO_NOME
    assert usuario.primeiro_nome == PRIMEIRO_NOME_SEM_SEGUNDO_NOME
    assert usuario.sobrenome == ""
    assert usuario.matricula == MATRICULA_SEM_SEGUNDO_NOME
    assert usuario.nome_completo == f"{PRIMEIRO_NOME_SEM_SEGUNDO_NOME}"