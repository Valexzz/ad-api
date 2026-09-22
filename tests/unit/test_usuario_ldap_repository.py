import pytest
from ldap3 import MODIFY_REPLACE

from ad_api.adapters.usuario_ldap_repository import UsuarioLdapRepository
from ad_api.domain.model import StatusUsuario, Usuario
from ad_api.errors import UsuarioJaExisteError
from ad_api.utils import obter_datetime_ad_nunca
from tests.conftest import (
    LOGIN_INEXISTENTE,
    LOGIN_SEM_MATRICULA,
    LOGIN_SEM_PRIMEIRO_NOME,
    LOGIN_SEM_SEGUNDO_NOME,
    LOGIN_USUARIO_ATIVO,
    LOGIN_USUARIO_INATIVO,
    MATRICULA_SEM_PRIMEIRO_NOME,
    MATRICULA_SEM_SEGUNDO_NOME,
    MATRICULA_USUARIO_ATIVO,
    MATRICULA_USUARIO_INATIVO,
    PRIMEIRO_NOME_SEM_MATRICULA,
    PRIMEIRO_NOME_SEM_SEGUNDO_NOME,
    PRIMEIRO_NOME_USUARIO_ATIVO,
    PRIMEIRO_NOME_USUARIO_INATIVO,
    SEGUNDO_NOME_SEM_MATRICULA,
    SEGUNDO_NOME_SEM_PRIMEIRO_NOME,
    SEGUNDO_NOME_USUARIO_ATIVO,
    SEGUNDO_NOME_USUARIO_INATIVO,
)


# ==============================================================================
# Testes: buscar_por_login
# ==============================================================================

def test_deve_retornar_usuario_ativo_completo_ao_buscar_por_login(fake_ldap_client):
    repo = UsuarioLdapRepository(ldap_client=fake_ldap_client, base_dn="DC=fake,DC=local")

    usuario = repo.buscar_por_login(LOGIN_USUARIO_ATIVO)

    assert usuario is not None
    assert usuario.login == LOGIN_USUARIO_ATIVO
    assert usuario.primeiro_nome == PRIMEIRO_NOME_USUARIO_ATIVO
    assert usuario.sobrenome == SEGUNDO_NOME_USUARIO_ATIVO
    assert usuario.matricula == MATRICULA_USUARIO_ATIVO
    assert usuario.status == StatusUsuario.ATIVO


def test_deve_retornar_usuario_inativo_ao_buscar_por_login(fake_ldap_client):
    repo = UsuarioLdapRepository(ldap_client=fake_ldap_client, base_dn="DC=fake,DC=local")

    usuario = repo.buscar_por_login(LOGIN_USUARIO_INATIVO)

    assert usuario is not None
    assert usuario.login == LOGIN_USUARIO_INATIVO
    assert usuario.status == StatusUsuario.INATIVO


def test_deve_retornar_none_ao_buscar_login_inexistente(fake_ldap_client):
    repo = UsuarioLdapRepository(ldap_client=fake_ldap_client, base_dn="DC=fake,DC=local")

    usuario = repo.buscar_por_login(LOGIN_INEXISTENTE)

    assert usuario is None


def test_deve_retornar_usuario_sem_matricula_ao_buscar_por_login(fake_ldap_client):
    repo = UsuarioLdapRepository(ldap_client=fake_ldap_client, base_dn="DC=fake,DC=local")

    usuario = repo.buscar_por_login(LOGIN_SEM_MATRICULA)

    assert usuario is not None
    assert usuario.login == LOGIN_SEM_MATRICULA
    assert usuario.primeiro_nome == PRIMEIRO_NOME_SEM_MATRICULA
    assert usuario.sobrenome == SEGUNDO_NOME_SEM_MATRICULA
    assert usuario.matricula is None
    assert usuario.nome_completo == f"{PRIMEIRO_NOME_SEM_MATRICULA} {SEGUNDO_NOME_SEM_MATRICULA}"


def test_deve_retornar_usuario_sem_primeiro_nome_ao_buscar_por_login(fake_ldap_client):
    repo = UsuarioLdapRepository(ldap_client=fake_ldap_client, base_dn="DC=fake,DC=local")

    usuario = repo.buscar_por_login(LOGIN_SEM_PRIMEIRO_NOME)

    assert usuario is not None
    assert usuario.login == LOGIN_SEM_PRIMEIRO_NOME
    assert usuario.primeiro_nome == ""
    assert usuario.sobrenome == SEGUNDO_NOME_SEM_PRIMEIRO_NOME
    assert usuario.matricula == MATRICULA_SEM_PRIMEIRO_NOME
    assert usuario.nome_completo == f"{SEGUNDO_NOME_SEM_PRIMEIRO_NOME}"


def test_deve_retornar_usuario_sem_segundo_nome_ao_buscar_por_login(fake_ldap_client):
    repo = UsuarioLdapRepository(ldap_client=fake_ldap_client, base_dn="DC=fake,DC=local")

    usuario = repo.buscar_por_login(LOGIN_SEM_SEGUNDO_NOME)

    assert usuario is not None
    assert usuario.login == LOGIN_SEM_SEGUNDO_NOME
    assert usuario.primeiro_nome == PRIMEIRO_NOME_SEM_SEGUNDO_NOME
    assert usuario.sobrenome == ""
    assert usuario.matricula == MATRICULA_SEM_SEGUNDO_NOME
    assert usuario.nome_completo == f"{PRIMEIRO_NOME_SEM_SEGUNDO_NOME}"


# ==============================================================================
# Testes: criar_usuario
# ==============================================================================

def test_deve_criar_usuario_ativo_com_sucesso_no_ad(fake_ldap_client):
    base_dn = "DC=fake,DC=local"
    repo = UsuarioLdapRepository(ldap_client=fake_ldap_client, base_dn=base_dn, dn_padrao=f"OU=Users,{base_dn}")

    novo_usuario = Usuario.criar(
        login="novo.usuario",
        nome_completo="Novo Usuario",
        matricula="55443",
        status=StatusUsuario.ATIVO,
    )

    resultado = repo.criar_usuario(
        usuario=novo_usuario,
        senha="Password@123",
        trocar_senha=False,
    )

    assert resultado == novo_usuario

    # Valida se a entrada realmente foi persistida na árvore mock do LDAP
    with fake_ldap_client.get_conn() as conn:
        conn.search(
            search_base=base_dn,
            search_filter="(sAMAccountName=novo.usuario)",
            attributes=["sAMAccountName", "userAccountControl", "employeeID", "unicodePwd"],
        )
        assert len(conn.entries) == 1
        entry = conn.entries[0]
        assert entry["sAMAccountName"].value == "novo.usuario"
        assert int(entry["userAccountControl"].value) == 512
        assert entry["employeeID"].value == "55443"
        assert entry["unicodePwd"].raw_values == [f'"Password@123"'.encode("utf-16le")]


def test_deve_criar_usuario_com_status_inativo(fake_ldap_client):
    base_dn = "DC=fake,DC=local"
    repo = UsuarioLdapRepository(ldap_client=fake_ldap_client, base_dn=base_dn, dn_padrao=f"OU=Users,{base_dn}")

    usuario_inativo = Usuario.criar(
        login="inativo.teste",
        nome_completo="Inativo Teste",
        status=StatusUsuario.INATIVO,
    )

    repo.criar_usuario(
        usuario=usuario_inativo,
        senha="Password@123",
    )

    with fake_ldap_client.get_conn() as conn:
        conn.search(
            search_base=base_dn,
            search_filter="(sAMAccountName=inativo.teste)",
            attributes=["userAccountControl"],
        )
        assert len(conn.entries) == 1
        # 512 (NORMAL_ACCOUNT) | 2 (ACCOUNTDISABLE) = 514
        assert int(conn.entries[0]["userAccountControl"].value) == 514


def test_deve_definir_pwdlastset_zero_quando_forcar_troca_senha_for_true(fake_ldap_client):
    base_dn = "DC=fake,DC=local"
    repo = UsuarioLdapRepository(ldap_client=fake_ldap_client, base_dn=base_dn, dn_padrao=f"OU=Users,{base_dn}")

    usuario = Usuario.criar(
        login="forcar.senha",
        nome_completo="Forcar Senha",
    )

    repo.criar_usuario(
        usuario=usuario,
        senha="Password@123",
        trocar_senha=True,
    )

    with fake_ldap_client.get_conn() as conn:
        conn.search(
            search_base=base_dn,
            search_filter="(sAMAccountName=forcar.senha)",
            attributes=["pwdLastSet"],
        )
        assert len(conn.entries) == 1

        assert conn.entries[0]["pwdLastSet"].value == obter_datetime_ad_nunca()


def test_deve_lancar_excecao_ao_tentar_criar_usuario_com_dn_duplicado(fake_ldap_client):
    base_dn = "DC=fake,DC=local"
    repo = UsuarioLdapRepository(ldap_client=fake_ldap_client, base_dn=base_dn, dn_padrao=f"OU=Users,{base_dn}")

    # LOGIN_USUARIO_ATIVO já foi inserido na fixture ldap_mock_conn
    usuario_duplicado = Usuario(
        login=LOGIN_USUARIO_ATIVO,
        primeiro_nome=PRIMEIRO_NOME_USUARIO_ATIVO,
        sobrenome=SEGUNDO_NOME_USUARIO_ATIVO,
        status=StatusUsuario.ATIVO,
    )

    with pytest.raises(UsuarioJaExisteError) as exc_info:
        repo.criar_usuario(usuario=usuario_duplicado, senha="Password@123")

    assert f"Usuário com login '{LOGIN_USUARIO_ATIVO}' já existe no AD." in str(exc_info.value)

def test_deve_criar_usuario_em_container_customizado(fake_ldap_client):
    base_dn = "DC=fake,DC=local"
    repo = UsuarioLdapRepository(ldap_client=fake_ldap_client, base_dn=base_dn, dn_padrao=f"OU=Users,{base_dn}")

    container_customizado = f"OU=OutraOU,{base_dn}"
    usuario = Usuario.criar(login="usuario.ou", nome_completo="Usuario OU")

    repo.criar_usuario(usuario=usuario, senha="Password@123", container_dn=container_customizado)

    with fake_ldap_client.get_conn() as conn:
        conn.search(
            search_base=container_customizado,
            search_filter="(sAMAccountName=usuario.ou)",
            attributes=["sAMAccountName"]
        )
        assert len(conn.entries) == 1

from ad_api.errors import InfraError

def test_deve_lancar_infra_error_quando_falha_criar_usuario_por_outro_motivo(fake_ldap_client, monkeypatch):
    base_dn = "DC=fake,DC=local"
    repo = UsuarioLdapRepository(ldap_client=fake_ldap_client, base_dn=base_dn, dn_padrao=f"OU=Users,{base_dn}")

    usuario = Usuario.criar(login="usuario.erro", nome_completo="Usuario Erro")

    # Mocka o metdo conn.add para retornar Falso e simular um erro genérico do LDAP (ex: código 50 - Insufficient Access)
    class ConnMockFALHADO:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def add(self, *args, **kwargs):
            return False
        @property
        def result(self):
            return {"result": 50, "description": "insufficientAccessRights", "message": "Sem permissão"}

    monkeypatch.setattr(repo.ldap_client, "get_conn", lambda: ConnMockFALHADO())

    with pytest.raises(InfraError) as exc_info:
        repo.criar_usuario(usuario=usuario, senha="Password@123")

    assert "Falha ao criar usuário no AD" in str(exc_info.value)