from ad_api.adapters.usuario_ldap_repository import UsuarioLdapRepository
from tests.conftest import (
    LOGIN_SEM_MATRICULA,
    PRIMEIRO_NOME_SEM_MATRICULA,
    SEGUNDO_NOME_SEM_MATRICULA,
    LOGIN_SEM_PRIMEIRO_NOME,
    SEGUNDO_NOME_SEM_PRIMEIRO_NOME,
    MATRICULA_SEM_PRIMEIRO_NOME,
    LOGIN_SEM_SEGUNDO_NOME,
    PRIMEIRO_NOME_SEM_SEGUNDO_NOME,
    MATRICULA_SEM_SEGUNDO_NOME,
)


def test_buscar_por_login_deve_retornar_usuario_sem_matricula(fake_ldap_client):
    repo = UsuarioLdapRepository(ldap_client=fake_ldap_client)

    usuario = repo.buscar_por_login(LOGIN_SEM_MATRICULA)

    assert usuario is not None
    assert usuario.login == LOGIN_SEM_MATRICULA
    assert usuario.primeiro_nome == PRIMEIRO_NOME_SEM_MATRICULA
    assert usuario.sobrenome == SEGUNDO_NOME_SEM_MATRICULA
    assert usuario.matricula is None
    assert usuario.nome_completo == f"{PRIMEIRO_NOME_SEM_MATRICULA} {SEGUNDO_NOME_SEM_MATRICULA}"


def test_buscar_por_login_deve_retornar_usuario_sem_primeiro_nome(fake_ldap_client):
    repo = UsuarioLdapRepository(ldap_client=fake_ldap_client)

    usuario = repo.buscar_por_login(LOGIN_SEM_PRIMEIRO_NOME)

    assert usuario is not None
    assert usuario.login == LOGIN_SEM_PRIMEIRO_NOME
    assert usuario.primeiro_nome == ""
    assert usuario.sobrenome == SEGUNDO_NOME_SEM_PRIMEIRO_NOME
    assert usuario.matricula == MATRICULA_SEM_PRIMEIRO_NOME
    assert usuario.nome_completo == f"{SEGUNDO_NOME_SEM_PRIMEIRO_NOME}"


def test_buscar_por_login_deve_retornar_usuario_sem_segundo_nome(fake_ldap_client):
    repo = UsuarioLdapRepository(ldap_client=fake_ldap_client)

    usuario = repo.buscar_por_login(LOGIN_SEM_SEGUNDO_NOME)

    assert usuario is not None
    assert usuario.login == LOGIN_SEM_SEGUNDO_NOME
    assert usuario.primeiro_nome == PRIMEIRO_NOME_SEM_SEGUNDO_NOME
    assert usuario.sobrenome == ""
    assert usuario.matricula == MATRICULA_SEM_SEGUNDO_NOME
    assert usuario.nome_completo == f"{PRIMEIRO_NOME_SEM_SEGUNDO_NOME}"