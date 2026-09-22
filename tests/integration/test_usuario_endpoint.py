from fastapi.testclient import TestClient

from ad_api.adapters.conn import LdapClient
from ad_api.adapters.usuario_ldap_repository import UsuarioLdapRepository
from ad_api.api.dependencies import get_usuario_service, verificar_api_key
from ad_api.config import settings
from ad_api.main import app
from ad_api.services.usuario_service import UsuarioService
from tests.conftest import LOGIN_INEXISTENTE, LOGIN_USUARIO_ATIVO, LOGIN_USUARIO_INATIVO_INTEGRACAO


# ==============================================================================
# Testes de Integração: Leitura / Consulta de Usuário (GET /usuarios/{login})
# ==============================================================================

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

    app.dependency_overrides[verificar_api_key] = lambda: "token-valido-fake"

    with TestClient(app) as client:
        response = client.get("/usuarios/qualquer.usuario")

    app.dependency_overrides.clear()

    assert response.status_code == 502
    dados = response.json()
    assert dados["codigo"] == "ERRO_COMUNICACAO_AD"
    assert "mensagem" in dados

    if getattr(settings, 'debug', False):
        assert "detalhe" in dados
    else:
        assert "detalhe" not in dados


# ==============================================================================
# Testes de Integração: Criação de Usuário (POST /usuarios)
# ==============================================================================

def test_criar_usuario_deve_retornar_status_201_e_dados_do_usuario(client_com_ad):
    payload = {
        "login": "novo.usuario.teste",
        "senha": "Password@123",
        "trocar_senha": False,
        "status": "Ativo",
        "primeiro_nome": "Novo",
        "sobrenome": "Usuario Teste",
        "matricula": "98765",
        "container_dn": "CN=Users,DC=empresa,DC=local"
    }

    response = client_com_ad.post("/usuarios", json=payload)

    assert response.status_code == 201
    dados = response.json()
    assert dados["login"] == payload["login"]
    assert dados["nome_completo"] == "Novo Usuario Teste"
    assert dados["status"] == "Ativo"
    assert dados["matricula"] == "98765"


def test_criar_usuario_com_dados_invalidos_deve_retornar_status_400(client_com_ad):
    # Violando a regra de domínio: sem informar nem nome_completo nem primeiro_nome
    payload = {
        "login": "usuario.invalido",
        "senha": "Password@123",
        "status": "Ativo",
        "matricula": "11111"
    }

    response = client_com_ad.post("/usuarios", json=payload)

    assert response.status_code == 400
    dados = response.json()
    assert dados["codigo"] == "ERRO_REGRA_DE_NEGOCIO"
    assert "mensagem" in dados


def test_criar_usuario_duplicado_deve_retornar_status_409(client_com_ad):
    # LOGIN_USUARIO_ATIVO ("victor") já é criado estaticamente na fixture do Samba AD
    payload = {
        "login": LOGIN_USUARIO_ATIVO,
        "senha": "Password@123",
        "status": "Ativo",
        "primeiro_nome": "Victor",
        "sobrenome": "Duplicado"
    }

    response = client_com_ad.post("/usuarios", json=payload)

    assert response.status_code == 409
    dados = response.json()
    assert dados["codigo"] == "USUARIO_JA_EXISTE"
    assert "mensagem" in dados


def test_criar_usuario_com_senha_fora_da_politica_deve_retornar_status_400(client_com_ad):
    # Senha que viola várias regras: curta, sem maiúscula, sem número e sem caractere especial
    payload = {
        "login": "senha.invalida.politica",
        "senha": "abc",
        "status": "Ativo",
        "primeiro_nome": "Senha",
        "sobrenome": "Invalida"
    }

    response = client_com_ad.post("/usuarios", json=payload)

    assert response.status_code == 400
    dados = response.json()
    assert dados["codigo"] == "SENHA_INVALIDA"
    assert "mensagem" in dados
    assert "A senha não atende aos requisitos" in dados["mensagem"]

# ==============================================================================
# Testes de Integração: Reativação de Usuário (PUT /usuarios/{login})
# ==============================================================================

def test_reativar_usuario_deve_retornar_status_200_e_usuario_atualizado(client_com_ad):
    payload_reativacao = {
        "senha": "NewPassword@123",
        "trocar_senha": False,
        "container_dn": "CN=Users,DC=empresa,DC=local"
    }

    response = client_com_ad.patch(f"/usuarios/{LOGIN_USUARIO_INATIVO_INTEGRACAO}/desativar", json=payload_reativacao)

    assert response.status_code == 200
    dados = response.json()
    assert dados["login"] == LOGIN_USUARIO_INATIVO_INTEGRACAO
    assert dados["status"] == "Ativo"


def test_reativar_usuario_inexistente_deve_retornar_status_404(client_com_ad):
    payload = {
        "senha": "Password@123",
        "trocar_senha": False
    }

    response = client_com_ad.patch(f"/usuarios/{LOGIN_INEXISTENTE}/desativar", json=payload)

    assert response.status_code == 404
    dados = response.json()
    assert dados["codigo"] == "USUARIO_NAO_ENCONTRADO"
    assert "mensagem" in dados


def test_reativar_usuario_com_senha_fora_da_politica_deve_retornar_status_400(client_com_ad):

    payload = {
        "senha": "abc", # Senha fraca que viola a política
        "trocar_senha": False
    }

    response = client_com_ad.patch(f"/usuarios/{LOGIN_USUARIO_INATIVO_INTEGRACAO}/desativar", json=payload)

    assert response.status_code == 400
    dados = response.json()
    assert dados["codigo"] == "SENHA_INVALIDA"
    assert "A senha não atende aos requisitos" in dados["mensagem"]

# ==============================================================================
# Testes de Integração: Redefinição de Senha (PATCH /usuarios/{login}/redefinir-senha)
# ==============================================================================

def test_redefinir_senha_deve_retornar_status_200_e_usuario(client_com_ad):
    payload = {
        "senha": "NewSecurePassword@123",
        "trocar_senha": False
    }

    response = client_com_ad.patch(f"/usuarios/{LOGIN_USUARIO_ATIVO}/redefinir-senha", json=payload)

    assert response.status_code == 200
    dados = response.json()
    assert dados["login"] == LOGIN_USUARIO_ATIVO
    assert dados["status"] == "Ativo"


def test_redefinir_senha_usuario_inexistente_deve_retornar_status_404(client_com_ad):
    payload = {
        "senha": "NewSecurePassword@123",
        "trocar_senha": False
    }

    response = client_com_ad.patch(f"/usuarios/{LOGIN_INEXISTENTE}/redefinir-senha", json=payload)

    assert response.status_code == 404
    dados = response.json()
    assert dados["codigo"] == "USUARIO_NAO_ENCONTRADO"
    assert "mensagem" in dados


def test_redefinir_senha_com_senha_fraca_deve_retornar_status_400(client_com_ad):
    payload = {
        "senha": "abc",
        "trocar_senha": False
    }

    response = client_com_ad.patch(f"/usuarios/{LOGIN_USUARIO_ATIVO}/redefinir-senha", json=payload)

    assert response.status_code == 400
    dados = response.json()
    assert dados["codigo"] == "SENHA_INVALIDA"
    assert "A senha não atende aos requisitos" in dados["mensagem"]


def test_deve_permitir_acesso_com_api_key_valida(client_sem_override_api_key):
    # Envia o header "x-api-key" com a chave correta configurada nas settings
    headers = {"x-api-key": "chave-api-padrao"}

    response = client_sem_override_api_key.get(
        f"/usuarios/{LOGIN_USUARIO_ATIVO}",
        headers=headers
    )

    assert response.status_code == 200
    dados = response.json()
    assert dados["login"] == LOGIN_USUARIO_ATIVO


def test_deve_retornar_401_ao_tentar_acessar_sem_api_key_ou_com_chave_invalida(client_sem_override_api_key):
    # 1. Tentativa sem mandar o header x-api-key
    response_sem_chave = client_sem_override_api_key.get(f"/usuarios/{LOGIN_USUARIO_ATIVO}")
    assert response_sem_chave.status_code == 401
    assert response_sem_chave.json()["codigo"] == "CHAVE_API_INVALIDA" # (ou o código que seu handler de 401 retorna)

    # 2. Tentativa mandando uma chave incorreta
    headers = {"x-api-key": "chave-errada-123"}
    response_chave_errada = client_sem_override_api_key.get(
        f"/usuarios/{LOGIN_USUARIO_ATIVO}",
        headers=headers
    )
    assert response_chave_errada.status_code == 401