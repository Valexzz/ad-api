import time
from contextlib import contextmanager
from copy import deepcopy
from typing import Optional

import pytest
from fastapi.testclient import TestClient
from ldap3 import MOCK_SYNC, OFFLINE_AD_2012_R2, Connection, Server
from testcontainers.core.container import DockerContainer

from ad_api.adapters.conn import LdapClient
from ad_api.adapters.usuario_ldap_repository import UsuarioLdapRepository
from ad_api.api.dependencies import get_perfil_ad_autenticado, get_usuario_service
from ad_api.config import PerfilAD, settings, ad_config
from ad_api.domain.model import PoliticaSenha, StatusUsuario, Usuario
from ad_api.domain.ports import UsuarioRepository
from ad_api.errors import UsuarioNaoEncontradoError
from ad_api.main import app
from ad_api.services.usuario_service import UsuarioService

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
        self._timeout = 5
        self._use_ssl = False

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
            mover_para_container_padrao: bool = False,
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


# ==============================================================================
# Fixtures Base / Domínio
# ==============================================================================

@pytest.fixture
def politica_padrao():
    return PoliticaSenha(
        tamanho_minimo=4,
        exigir_minuscula=False,
        exigir_maiuscula=False,
        exigir_numero=False,
        exigir_caractere_especial=False,
    )


# ==============================================================================
# Fixtures Mock LDAP (Testes Rápidos de Repositório)
# ==============================================================================

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
    return FakeLdapClient(ldap_mock_conn)


@pytest.fixture
def repo(fake_ldap_client):
    dn_base = "DC=fake,DC=local"
    return UsuarioLdapRepository(
        ldap_client=fake_ldap_client,
        dn_base=dn_base,
        dn_padrao=f"OU=Users,{dn_base}",
        dominio="fake.local",
        dias_expiracao_senha_ad=90,
    )


# ==============================================================================
# Fixtures Samba Container & FastAPI TestClient
# ==============================================================================

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
        container.exec(
            'samba-tool user create usuario.inativo Mudar@1234 '
            '--given-name="Usuario" '
            '--surname="Inativo"'
        )
        container.exec("samba-tool user disable usuario.inativo")

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


@pytest.fixture
def client_com_ad(samba_ad_container, politica_padrao):
    """Configura o FastAPI ignorando a autenticação e apontando para o Samba AD."""
    real_client = LdapClient(
        servidor=samba_ad_container["host"],
        porta=samba_ad_container["port"],
        usuario=f"Administrator@{samba_ad_container['domain']}",
        senha=samba_ad_container["bind_password"],
        use_ssl=True,
    )

    def override_get_service():
        repository = UsuarioLdapRepository(
            ldap_client=real_client,
            dn_base=samba_ad_container["base_dn"],
            dn_padrao=f"CN=Users,{samba_ad_container['base_dn']}",
            dominio=samba_ad_container["domain"],
            dias_expiracao_senha_ad=90,
        )
        # Usa a política completa necessária para validação de senha nos testes de integração
        politica_integracao = PoliticaSenha(
            tamanho_minimo=8,
            exigir_minuscula=True,
            exigir_maiuscula=True,
            exigir_numero=True,
            exigir_caractere_especial=True,
            chars_especiais=r"!@#$%&*",
        )
        return UsuarioService(
            usuario_repository=repository,
            politica_senha=politica_integracao,
        )

    perfil_fake = PerfilAD(
        servidor=samba_ad_container["host"],
        dominio=samba_ad_container["domain"],
        dominio_netbios="FAKE",
        usuario_service_account="admin",
        senha_service_account="pass",
        env_senha_service_account="",
        chave_api_hash="fake-key",
        env_chave_api_hash="",
        dn_base=samba_ad_container["base_dn"],
        dn_padrao=f"CN=Users,{samba_ad_container['base_dn']}",
    )

    app.dependency_overrides[get_usuario_service] = override_get_service
    app.dependency_overrides[get_perfil_ad_autenticado] = lambda: perfil_fake

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def client_sem_override_api_key(samba_ad_container):
    """Mantém a validação real de API Key ativa."""
    real_client = LdapClient(
        servidor=samba_ad_container["host"],
        porta=samba_ad_container["port"],
        usuario=f"Administrator@{samba_ad_container['domain']}",
        senha=samba_ad_container["bind_password"],
        use_ssl=True,
    )

    def override_get_service():
        repository = UsuarioLdapRepository(
            ldap_client=real_client,
            dn_base=samba_ad_container["base_dn"],
            dn_padrao=f"CN=Users,{samba_ad_container['base_dn']}",
            dominio=samba_ad_container["domain"],
            dias_expiracao_senha_ad=90,
        )
        politica_integracao = PoliticaSenha(
            tamanho_minimo=8,
            exigir_minuscula=True,
            exigir_maiuscula=True,
            exigir_numero=True,
            exigir_caractere_especial=True,
            chars_especiais=r"!@#$%&*",
        )
        return UsuarioService(
            usuario_repository=repository,
            politica_senha=politica_integracao,
        )

    app.dependency_overrides[get_usuario_service] = override_get_service

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()

@pytest.fixture
def mock_multiplos_ads(monkeypatch):
    """
    Garante que existam ao menos dois perfis configurados em ad_config.ads:
    - O padrão (apontando para o container real do Samba).
    - Um secundário 'ad2' com uma chave de API distinta.
    """
    nome_padrao = settings.ad_padrao
    perfil_original = ad_config.ads[nome_padrao]

    # Clona o perfil original mudando o identificador e a chave
    perfil_ad2 = deepcopy(perfil_original)
    perfil_ad2.chave_api_hash = "chave-secreta-ad2"

    novos_ads = {
        nome_padrao: perfil_original,
        "ad2": perfil_ad2,
    }

    monkeypatch.setattr(ad_config, "ads", novos_ads)
    return nome_padrao, "ad2"