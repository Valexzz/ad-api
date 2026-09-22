import time
from contextlib import contextmanager
from typing import Optional

import pytest
from ldap3 import Server, Connection, MOCK_SYNC, OFFLINE_AD_2012_R2
from testcontainers.core.container import DockerContainer

from ad_api.adapters.conn import LdapClient
from ad_api.adapters.usuario_ldap_repository import UsuarioLdapRepository
from ad_api.api.dependencies import get_usuario_service, verificar_api_key
from ad_api.domain.model import Usuario, StatusUsuario
from ad_api.domain.ports import UsuarioRepository
from ad_api.errors import UsuarioNaoEncontradoError
from ad_api.main import app
from ad_api.services.usuario_service import UsuarioService
from fastapi.testclient import TestClient

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

LOGIN_USUARIO_INATIVO_INTEGRACAO = "usuario.inativo"


class FakeLdapClient(LdapClient):
    def __init__(self, conn: Connection):
        self._conn = conn

    @contextmanager
    def get_conn(self):
        yield self._conn


class FakeUsuarioRepository(UsuarioRepository):
    def __init__(self, usuarios: list[Usuario] | None = None):

        self._usuarios = {u.login: u for u in (usuarios or [])}
        self.ultimo_usuario_criado = None
        self.ultima_senha = None
        self.ultimo_forcar_troca_senha = None
        self.ultimo_container_dn = None

        self.ultimo_login_reativado = None
        self.ultima_senha_reativacao = None
        self.ultimo_container_reativacao = None

        self.ultimo_login_redefinicao_senha = None
        self.ultima_senha_redefinicao = None
        self.ultimo_forcar_troca_senha_redefinicao = None

    def buscar_por_login(self, login: str) -> Optional[Usuario]:
        return self._usuarios.get(login)

    def criar_usuario(
            self,
            usuario: Usuario,
            senha: str,
            trocar_senha: bool = False,
            container_dn: Optional[str] = None,
    ):
        self.ultimo_usuario_criado = usuario
        self.ultima_senha = senha
        self.ultimo_forcar_troca_senha = trocar_senha
        self.ultimo_container_dn = container_dn
        self._usuarios[usuario.login] = usuario
        return usuario

    def reativar_usuario(
            self,
            login: str,
            senha: Optional[str] = None,
            trocar_senha: bool = False,
            container_dn: Optional[str] = None,
    ):
        self.ultimo_login_reativado = login
        self.ultima_senha_reativacao = senha
        self.ultimo_container_reativacao = container_dn

        usuario = self._usuarios.get(login)
        if usuario:
            usuario.status = StatusUsuario.ATIVO

        return usuario

    def redefinir_senha(
            self,
            login: str,
            senha: str,
            trocar_senha: bool = False,
    ):
        self.ultimo_login_redefinicao_senha = login
        self.ultima_senha_redefinicao = senha
        self.ultimo_forcar_troca_senha_redefinicao = trocar_senha

        usuario = self._usuarios.get(login)
        if not usuario:
            raise UsuarioNaoEncontradoError(f"Usuário com login '{login}' não encontrado.")
        return usuario


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

    cn_usuario_ativo = f"{PRIMEIRO_NOME_USUARIO_ATIVO} {SEGUNDO_NOME_USUARIO_ATIVO}"

    conn.strategy.add_entry(
        f"CN={cn_usuario_ativo},OU=Users,DC=fake,DC=local",
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

    # 3. Usuário sem Matrícula
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

    # 4. Usuário sem Primeiro Nome
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

    # 5. Usuário sem Segundo Nome
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

@pytest.fixture
def fake_ldap_client(ldap_mock_conn):
    """Fixture utilitária que devolve o client pronto a ser injetado."""
    return FakeLdapClient(ldap_mock_conn)
@pytest.fixture(scope="session")
def samba_ad_container():
    container = (
        DockerContainer("diegogslomp/samba-ad-dc:latest")
        .with_env("REALM", "empresa.local")
        .with_env("DOMAIN", "EMPRESA")
        .with_env("ADMIN_PASS", "MinhaSenhaForte123")
        .with_env("DNS_FORWARDER", "8.8.8.8")
        .with_env("BIND_NETWORK_INTERFACES", "false")
        .with_exposed_ports(389, 636)
        .with_kwargs(privileged=True)
    )

    with container:
        print("Iniciando o container do Samba AD...")
        time.sleep(15)

        container.exec("samba-tool user create svc_api MinhaSenhaForte123")
        container.exec(
            'samba-tool user create victor Mudar@1234 '
            '--given-name="Victor" '
            '--surname="Milhomem" '
            '--mail-address="victor@empresa.local"'
        )

        # --- ADICIONE ESTE BLOCO PARA CRIAR E DESATIVAR UM USUÁRIO PARA OS TESTES DE REATIVAÇÃO ---
        container.exec(
            'samba-tool user create usuario.inativo Mudar@1234 '
            '--given-name="Usuario" '
            '--surname="Inativo"'
        )
        # Comando do Samba para desativar a conta logo na criação
        container.exec('samba-tool user disable usuario.inativo')
        # ---------------------------------------------------------------------------------------

        host_ip = container.get_container_host_ip()
        mapped_port_636 = int(container.get_exposed_port(636))

        yield {
            "host": host_ip,
            "port": mapped_port_636,
            "domain": "empresa.local",
            "base_dn": "DC=empresa,DC=local",
            "bind_user": "svc_api@empresa.local",
            "bind_password": "MinhaSenhaForte123",
        }

def override_verificar_api_key():
    return "chave-valida-de-teste"

#Por padrão, noa necessita de validar chave de API
@pytest.fixture
def client_com_ad(samba_ad_container):
    """Configura o FastAPI para usar o container do Samba e retorna o TestClient."""
    real_client = LdapClient(
        server=samba_ad_container["host"],
        port=samba_ad_container["port"],
        user=f"Administrator@{samba_ad_container['domain']}",
        password=samba_ad_container["bind_password"],
        use_ssl=True,
    )

    def override_get_service():
        repository = UsuarioLdapRepository(ldap_client=real_client, base_dn=samba_ad_container["base_dn"])
        return UsuarioService(usuario_repository=repository)

    app.dependency_overrides[get_usuario_service] = override_get_service

    app.dependency_overrides[verificar_api_key] = override_verificar_api_key

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()

# Fixture SEM OVERRIDE da API Key (para testar a segurança exigida no RNF01)
@pytest.fixture
def client_sem_override_api_key(samba_ad_container):
    real_client = LdapClient(
        server=samba_ad_container["host"],
        port=samba_ad_container["port"],
        user=f"Administrator@{samba_ad_container['domain']}",
        password=samba_ad_container["bind_password"],
        use_ssl=True,
    )

    def override_get_service():
        repository = UsuarioLdapRepository(ldap_client=real_client, base_dn=samba_ad_container["base_dn"])
        return UsuarioService(usuario_repository=repository)

    app.dependency_overrides[get_usuario_service] = override_get_service

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()