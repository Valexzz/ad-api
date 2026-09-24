from datetime import datetime, timedelta, timezone

import pytest

from ad_api.adapters.usuario_ldap_repository import UsuarioLdapRepository
from ad_api.domain.model import StatusSenha, StatusUsuario, Usuario
from ad_api.errors import (
    InfraError,
    UsuarioJaExisteError,
    UsuarioNaoEncontradoError,
)
from ad_api.utils import datetime_para_ad_filetime, obter_datetime_ad_nunca
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

def test_deve_retornar_usuario_ativo_completo_ao_buscar_por_login(repo):
    usuario = repo.buscar_por_login(LOGIN_USUARIO_ATIVO)

    assert usuario is not None
    assert usuario.login == LOGIN_USUARIO_ATIVO
    assert usuario.primeiro_nome == PRIMEIRO_NOME_USUARIO_ATIVO
    assert usuario.sobrenome == SEGUNDO_NOME_USUARIO_ATIVO
    assert usuario.matricula == MATRICULA_USUARIO_ATIVO
    assert usuario.status == StatusUsuario.ATIVO


def test_deve_retornar_usuario_inativo_ao_buscar_por_login(repo):
    usuario = repo.buscar_por_login(LOGIN_USUARIO_INATIVO)

    assert usuario is not None
    assert usuario.login == LOGIN_USUARIO_INATIVO
    assert usuario.status == StatusUsuario.INATIVO


def test_deve_retornar_none_ao_buscar_login_inexistente(repo):
    usuario = repo.buscar_por_login(LOGIN_INEXISTENTE)

    assert usuario is None


def test_deve_retornar_usuario_sem_matricula_ao_buscar_por_login(repo):
    usuario = repo.buscar_por_login(LOGIN_SEM_MATRICULA)

    assert usuario is not None
    assert usuario.login == LOGIN_SEM_MATRICULA
    assert usuario.primeiro_nome == PRIMEIRO_NOME_SEM_MATRICULA
    assert usuario.sobrenome == SEGUNDO_NOME_SEM_MATRICULA
    assert usuario.matricula is None
    assert usuario.nome_completo == f"{PRIMEIRO_NOME_SEM_MATRICULA} {SEGUNDO_NOME_SEM_MATRICULA}"


def test_deve_retornar_usuario_sem_primeiro_nome_ao_buscar_por_login(repo):
    usuario = repo.buscar_por_login(LOGIN_SEM_PRIMEIRO_NOME)

    assert usuario is not None
    assert usuario.login == LOGIN_SEM_PRIMEIRO_NOME
    assert usuario.primeiro_nome == ""
    assert usuario.sobrenome == SEGUNDO_NOME_SEM_PRIMEIRO_NOME
    assert usuario.matricula == MATRICULA_SEM_PRIMEIRO_NOME
    assert usuario.nome_completo == f"{SEGUNDO_NOME_SEM_PRIMEIRO_NOME}"


def test_deve_retornar_usuario_sem_segundo_nome_ao_buscar_por_login(repo):
    usuario = repo.buscar_por_login(LOGIN_SEM_SEGUNDO_NOME)

    assert usuario is not None
    assert usuario.login == LOGIN_SEM_SEGUNDO_NOME
    assert usuario.primeiro_nome == PRIMEIRO_NOME_SEM_SEGUNDO_NOME
    assert usuario.sobrenome == ""
    assert usuario.matricula == MATRICULA_SEM_SEGUNDO_NOME
    assert usuario.nome_completo == f"{PRIMEIRO_NOME_SEM_SEGUNDO_NOME}"


def test_deve_retornar_status_senha_para_redefinir_quando_pwdlastset_for_zero(repo, fake_ldap_client):
    with fake_ldap_client.get_conn() as conn:
        conn.strategy.add_entry(
            f"CN=usuario.redefinir,OU=Users,{repo.dn_base}",
            {
                "objectCategory": "person",
                "objectClass": ["top", "person", "organizationalPerson", "user"],
                "sAMAccountName": "usuario.redefinir",
                "givenName": "User",
                "sn": "Redefinir",
                "userAccountControl": 512,
                "pwdLastSet": 0,
            },
        )

    usuario = repo.buscar_por_login("usuario.redefinir")

    assert usuario is not None
    assert usuario.status_senha == StatusSenha.PARA_REDEFINIR


def test_deve_retornar_status_senha_expirada_quando_passar_dos_dias_limite(repo, fake_ldap_client):
    data_antiga = datetime_para_ad_filetime(datetime.now(timezone.utc) - timedelta(days=120))

    with fake_ldap_client.get_conn() as conn:
        conn.strategy.add_entry(
            f"CN=usuario.expirado,OU=Users,{repo.dn_base}",
            {
                "objectCategory": "person",
                "objectClass": ["top", "person", "organizationalPerson", "user"],
                "sAMAccountName": "usuario.expirado",
                "givenName": "User",
                "sn": "Expirado",
                "userAccountControl": 512,
                "pwdLastSet": data_antiga,
            },
        )

    usuario = repo.buscar_por_login("usuario.expirado")

    assert usuario is not None
    assert usuario.status_senha == StatusSenha.EXPIRADA


def test_deve_retornar_status_senha_ativa_quando_pwdlastset_for_recente(repo, fake_ldap_client):
    data_recente = datetime_para_ad_filetime(datetime.now(timezone.utc) - timedelta(days=5))

    with fake_ldap_client.get_conn() as conn:
        conn.strategy.add_entry(
            f"CN=usuario.ativo.senha,OU=Users,{repo.dn_base}",
            {
                "objectCategory": "person",
                "objectClass": ["top", "person", "organizationalPerson", "user"],
                "sAMAccountName": "usuario.ativo.senha",
                "givenName": "User",
                "sn": "AtivoSenha",
                "userAccountControl": 512,
                "pwdLastSet": data_recente,
            },
        )

    usuario = repo.buscar_por_login("usuario.ativo.senha")

    assert usuario is not None
    assert usuario.status_senha == StatusSenha.ATIVA


# ==============================================================================
# Testes: criar_usuario
# ==============================================================================

def test_deve_criar_usuario_ativo_com_sucesso_no_ad(repo, fake_ldap_client):
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

    with fake_ldap_client.get_conn() as conn:
        conn.search(
            search_base=repo.dn_base,
            search_filter="(sAMAccountName=novo.usuario)",
            attributes=["sAMAccountName", "userAccountControl", "employeeID", "unicodePwd", "userPrincipalName"],
        )
        assert len(conn.entries) == 1
        entry = conn.entries[0]
        assert entry["sAMAccountName"].value == "novo.usuario"
        assert entry["userPrincipalName"].value == f"novo.usuario@{repo.dominio}"
        assert int(entry["userAccountControl"].value) == 512
        assert entry["employeeID"].value == "55443"
        assert entry["unicodePwd"].raw_values == [f'"Password@123"'.encode("utf-16le")]


def test_deve_criar_usuario_com_status_inativo(repo, fake_ldap_client):
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
            search_base=repo.dn_base,
            search_filter="(sAMAccountName=inativo.teste)",
            attributes=["userAccountControl"],
        )
        assert len(conn.entries) == 1
        assert int(conn.entries[0]["userAccountControl"].value) == 514


def test_deve_definir_pwdlastset_zero_quando_forcar_troca_senha_for_true(repo, fake_ldap_client):
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
            search_base=repo.dn_base,
            search_filter="(sAMAccountName=forcar.senha)",
            attributes=["pwdLastSet"],
        )
        assert len(conn.entries) == 1
        assert conn.entries[0]["pwdLastSet"].value == obter_datetime_ad_nunca()


def test_deve_garantir_que_pwdlastset_nao_e_zero_quando_trocar_senha_for_false(repo, fake_ldap_client):
    usuario = Usuario.criar(
        login="nao.forcar.senha",
        nome_completo="Nao Forcar Senha",
    )

    repo.criar_usuario(
        usuario=usuario,
        senha="Password@123",
        trocar_senha=False,
    )

    with fake_ldap_client.get_conn() as conn:
        conn.search(
            search_base=repo.dn_base,
            search_filter="(sAMAccountName=nao.forcar.senha)",
            attributes=["pwdLastSet"],
        )
        assert len(conn.entries) == 1
        assert conn.entries[0]["pwdLastSet"].value != obter_datetime_ad_nunca()


def test_deve_lancar_excecao_ao_tentar_criar_usuario_com_dn_duplicado(repo):
    usuario_duplicado = Usuario(
        login=LOGIN_USUARIO_ATIVO,
        primeiro_nome=PRIMEIRO_NOME_USUARIO_ATIVO,
        sobrenome=SEGUNDO_NOME_USUARIO_ATIVO,
        status=StatusUsuario.ATIVO,
    )

    with pytest.raises(UsuarioJaExisteError) as exc_info:
        repo.criar_usuario(usuario=usuario_duplicado, senha="Password@123")

    assert f"Usuário com login '{LOGIN_USUARIO_ATIVO}' já existe no AD." in str(exc_info.value)


def test_deve_criar_usuario_em_container_customizado(repo, fake_ldap_client):
    container_customizado = f"OU=OutraOU,{repo.dn_base}"
    usuario = Usuario.criar(login="usuario.ou", nome_completo="Usuario OU")

    repo.criar_usuario(usuario=usuario, senha="Password@123", container_dn=container_customizado)

    with fake_ldap_client.get_conn() as conn:
        conn.search(
            search_base=container_customizado,
            search_filter="(sAMAccountName=usuario.ou)",
            attributes=["sAMAccountName"],
        )
        assert len(conn.entries) == 1


def test_deve_lancar_infra_error_quando_falha_criar_usuario_por_outro_motivo(repo, monkeypatch):
    usuario = Usuario.criar(login="usuario.erro", nome_completo="Usuario Erro")

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


# ==============================================================================
# Testes: reativar_usuario
# ==============================================================================

def test_deve_reativar_usuario_com_sucesso_no_ad(repo, fake_ldap_client):
    resultado = repo.reativar_usuario(
        login=LOGIN_USUARIO_INATIVO,
        senha="NewPassword@123",
        trocar_senha=False,
    )

    assert resultado.status == StatusUsuario.ATIVO

    with fake_ldap_client.get_conn() as conn:
        conn.search(
            search_base=repo.dn_base,
            search_filter=f"(sAMAccountName={LOGIN_USUARIO_INATIVO})",
            attributes=["userAccountControl", "unicodePwd"],
        )
        assert len(conn.entries) == 1
        entry = conn.entries[0]
        assert int(entry["userAccountControl"].value) == 512
        assert entry["unicodePwd"].raw_values == [f'"NewPassword@123"'.encode("utf-16le")]


def test_deve_reativar_usuario_e_mover_para_container_customizado(repo, fake_ldap_client):
    container_customizado = f"OU=OutraOU,{repo.dn_base}"

    repo.reativar_usuario(
        login=LOGIN_USUARIO_INATIVO,
        container_dn=container_customizado,
    )

    with fake_ldap_client.get_conn() as conn:
        conn.search(
            search_base=container_customizado,
            search_filter=f"(sAMAccountName={LOGIN_USUARIO_INATIVO})",
            attributes=["sAMAccountName", "userAccountControl"],
        )
        assert len(conn.entries) == 1
        assert int(conn.entries[0]["userAccountControl"].value) == 512


def test_deve_lancar_excecao_ao_tentar_reativar_usuario_inexistente_no_ad(repo):
    with pytest.raises(UsuarioNaoEncontradoError) as exc_info:
        repo.reativar_usuario(login=LOGIN_INEXISTENTE, senha="Password@123")

    assert f"Usuário com login '{LOGIN_INEXISTENTE}' não encontrado no AD." in str(exc_info.value)


def test_deve_definir_pwdlastset_zero_na_reativacao_quando_forcar_troca_senha_for_true(repo, fake_ldap_client):
    repo.reativar_usuario(
        login=LOGIN_USUARIO_INATIVO,
        senha="NewPassword@123",
        trocar_senha=True,
    )

    with fake_ldap_client.get_conn() as conn:
        conn.search(
            search_base=repo.dn_base,
            search_filter=f"(sAMAccountName={LOGIN_USUARIO_INATIVO})",
            attributes=["pwdLastSet"],
        )
        assert len(conn.entries) == 1
        assert conn.entries[0]["pwdLastSet"].value == obter_datetime_ad_nunca()


# ==============================================================================
# Testes: redefinir_senha (Repository)
# ==============================================================================

def test_deve_redefinir_senha_com_sucesso_no_ad(repo, fake_ldap_client):
    repo.redefinir_senha(
        login=LOGIN_USUARIO_ATIVO,
        senha="SuperNewPassword@123",
        trocar_senha=False,
    )

    with fake_ldap_client.get_conn() as conn:
        conn.search(
            search_base=repo.dn_base,
            search_filter=f"(sAMAccountName={LOGIN_USUARIO_ATIVO})",
            attributes=["unicodePwd"],
        )
        assert len(conn.entries) == 1
        entry = conn.entries[0]
        assert entry["unicodePwd"].raw_values == [f'"SuperNewPassword@123"'.encode("utf-16le")]


def test_deve_definir_pwdlastset_zero_ao_redefinir_senha_com_trocar_senha_true(repo, fake_ldap_client):
    repo.redefinir_senha(
        login=LOGIN_USUARIO_ATIVO,
        senha="SuperNewPassword@123",
        trocar_senha=True,
    )

    with fake_ldap_client.get_conn() as conn:
        conn.search(
            search_base=repo.dn_base,
            search_filter=f"(sAMAccountName={LOGIN_USUARIO_ATIVO})",
            attributes=["pwdLastSet"],
        )
        assert len(conn.entries) == 1
        assert conn.entries[0]["pwdLastSet"].value == obter_datetime_ad_nunca()


def test_deve_lancar_excecao_ao_tentar_redefinir_senha_de_usuario_inexistente_no_ad(repo):
    with pytest.raises(UsuarioNaoEncontradoError) as exc_info:
        repo.redefinir_senha(login=LOGIN_INEXISTENTE, senha="Password@123")

    assert f"Usuário com login '{LOGIN_INEXISTENTE}' não encontrado no AD." in str(exc_info.value)