from fastapi.testclient import TestClient

from ad_api.adapters.conn import LdapClient
from ad_api.adapters.usuario_ldap_repository import UsuarioLdapRepository
from ad_api.api.dependencies import get_usuario_service
from ad_api.config import settings
from ad_api.main import app
from ad_api.services.usuario_service import UsuarioService
from tests.conftest import LOGIN_INEXISTENTE, LOGIN_USUARIO_ATIVO


def test_buscar_por_login_deve_retornar_status_200_e_usuario(client_com_ad):
    response = client_com_ad.get(f"/usuarios/{LOGIN_USUARIO_ATIVO}")

    assert response.status_code == 200
    dados = response.json()
    assert dados["login"] == LOGIN_USUARIO_ATIVO
    assert dados["nome_completo"] == "Victor Milhomem"
    assert dados["status"] == "Ativo"


def test_buscar_por_login_inexistente_deve_retornar_status_404_e_usuario(
        client_com_ad,
):
    response = client_com_ad.get(f"/usuarios/{LOGIN_INEXISTENTE}")

    assert response.status_code == 404
    dados = response.json()
    assert "codigo" in dados
    assert "mensagem" in dados


def test_buscar_sem_conexao_deve_retornar_status_502():
    client_sem_rede = LdapClient(
        server="127.0.0.1",
        port=59999,
        user="svc@empresa.local",
        password="qualquer_senha",
    )

    def override_sem_conexao():
        repo = UsuarioLdapRepository(ldap_client=client_sem_rede)
        return UsuarioService(usuario_repository=repo)

    app.dependency_overrides[get_usuario_service] = override_sem_conexao

    with TestClient(app) as client:
        response = client.get("/usuarios/qualquer.usuario")

    app.dependency_overrides.clear()

    assert response.status_code == 502
    dados = response.json()
    assert dados["codigo"] == "ERRO_COMUNICACAO_AD"

    if getattr(settings, 'debug', False):
        assert "mensagem" in dados
    else:
        assert "mensagem" not in dados