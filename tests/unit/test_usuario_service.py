from unittest.mock import patch

import pytest
from typing import Optional

from ad_api.config import settings
from ad_api.domain.model import Usuario, StatusUsuario, PoliticaSenha
from ad_api.domain.ports import UsuarioRepository
from ad_api.services.usuario_service import UsuarioService
from ad_api.errors import (
    UsuarioNaoEncontradoError,
    UsuarioJaExisteError,
    SenhaInvalidaError,
)
from tests.conftest import FakeUsuarioRepository


# ==============================================================================
# Testes: Recuperar Usuário
# ==============================================================================

def test_deve_retornar_usuario_quando_login_existir():
    usuario_existente = Usuario(
        login="joao.silva",
        primeiro_nome="João",
        sobrenome="Silva",
        status=StatusUsuario.ATIVO,
        matricula="12345",
    )
    repo = FakeUsuarioRepository(usuarios=[usuario_existente])
    service = UsuarioService(usuario_repository=repo)

    resultado = service.buscar_usuario_por_login("joao.silva")

    assert resultado == usuario_existente
    assert resultado.nome_completo == "João Silva"


def test_deve_lancar_excecao_quando_usuario_nao_existir():
    repo = FakeUsuarioRepository(usuarios=[])
    service = UsuarioService(usuario_repository=repo)

    with pytest.raises(UsuarioNaoEncontradoError) as exc_info:
        service.buscar_usuario_por_login("login.inexistente")

    assert "Usuário com login login.inexistente não encontrado" in str(exc_info.value)


# ==============================================================================
# Testes: Inserir Usuário
# ==============================================================================

def test_deve_criar_e_retornar_usuario_com_dados_validos():
    repo = FakeUsuarioRepository(usuarios=[])
    politica = PoliticaSenha(
        tamanho_minimo=8,
        exigir_minuscula=True,
        exigir_maiuscula=True,
        exigir_numero=True,
        exigir_caractere_especial=True,
    )
    service = UsuarioService(usuario_repository=repo, politica_senha=politica)

    novo_usuario = Usuario.criar(
        login="lucas.teste",
        nome_completo="Lucas Teste",
        matricula="99887",
    )

    resultado = service.criar_usuario(
        usuario=novo_usuario,
        senha="Password@123",
        trocar_senha=False,
    )

    assert resultado == novo_usuario
    assert resultado.login == "lucas.teste"
    assert resultado.nome_completo == "Lucas Teste"
    assert resultado.status == StatusUsuario.ATIVO


def test_deve_retornar_erro_ao_criar_senha_toda_invalida():
    repo = FakeUsuarioRepository(usuarios=[])
    politica = PoliticaSenha(
        tamanho_minimo=8,
        exigir_minuscula=True,
        exigir_maiuscula=True,
        exigir_numero=True,
        exigir_caractere_especial=True,
        chars_especiais="!@#$%&*",
    )
    service = UsuarioService(usuario_repository=repo, politica_senha=politica)

    novo_usuario = Usuario.criar(login="falha.senha", nome_completo="Falha Senha")

    # Senha curta, sem maiúscula, sem número e sem caractere especial
    senha_invalida = "abc"

    with pytest.raises(SenhaInvalidaError) as exc_info:
        service.criar_usuario(usuario=novo_usuario, senha=senha_invalida)

    mensagem = str(exc_info.value)
    assert "ter no mínimo 8 caracteres" in mensagem
    assert "conter ao menos uma letra maiúscula" in mensagem
    assert "conter ao menos um número" in mensagem
    assert "conter ao menos um caractere especial (!@#$%&*)" in mensagem
    # "conter ao menos uma letra minúscula" não deve aparecer, pois 'abc' tem minúsculas
    assert "conter ao menos uma letra minúscula" not in mensagem


def test_deve_retornar_erro_senha_minina_ao_criar_senha_com_este_criterio_invalido():
    repo = FakeUsuarioRepository(usuarios=[])
    politica = PoliticaSenha(
        tamanho_minimo=8,
        exigir_minuscula=True,
        exigir_maiuscula=True,
        exigir_numero=True,
        exigir_caractere_especial=True,
    )
    service = UsuarioService(usuario_repository=repo, politica_senha=politica)

    novo_usuario = Usuario.criar(login="curta.senha", nome_completo="Curta Senha")

    # Atende a minúscula, maiúscula, número e especial, mas tem menos de 8 caracteres
    senha_curta = "Ab1@xyz"

    with pytest.raises(SenhaInvalidaError) as exc_info:
        service.criar_usuario(usuario=novo_usuario, senha=senha_curta)

    mensagem = str(exc_info.value)
    assert "ter no mínimo 8 caracteres" in mensagem
    assert "conter ao menos uma letra minúscula" not in mensagem
    assert "conter ao menos uma letra maiúscula" not in mensagem
    assert "conter ao menos um número" not in mensagem
    assert "conter ao menos um caractere especial" not in mensagem


def test_deve_retornar_erro_senha_minima_somente_com_este_criterio_definido():
    repo = FakeUsuarioRepository(usuarios=[])
    # Política configurada apenas para checar tamanho mínimo
    politica_apenas_tamanho = PoliticaSenha(
        tamanho_minimo=8,
        exigir_minuscula=False,
        exigir_maiuscula=False,
        exigir_numero=False,
        exigir_caractere_especial=False,
    )
    service = UsuarioService(usuario_repository=repo, politica_senha=politica_apenas_tamanho)

    novo_usuario = Usuario.criar(login="apenas.tamanho", nome_completo="Apenas Tamanho")

    # Senha com menos de 8 caracteres e sem maiúsculas, números ou especiais
    senha_sem_outros_criterios = "teste"

    with pytest.raises(SenhaInvalidaError) as exc_info:
        service.criar_usuario(usuario=novo_usuario, senha=senha_sem_outros_criterios)

    mensagem = str(exc_info.value)
    # Deve conter exclusivamente o erro de tamanho
    assert "ter no mínimo 8 caracteres" in mensagem
    assert "conter ao menos uma letra minúscula" not in mensagem
    assert "conter ao menos uma letra maiúscula" not in mensagem
    assert "conter ao menos um número" not in mensagem
    assert "conter ao menos um caractere especial" not in mensagem

def test_deve_ler_as_settings_caso_politica_nao_informada_e_retornar_erro_em_senha_toda_invalida():
    repo = FakeUsuarioRepository(usuarios=[])

    # Instancia o service sem passar politica_senha (deve assumir defaults via settings)
    with patch.object(settings, "tamanho_minimo_senha_ad", 8), \
            patch.object(settings, "exigir_numero_senha_ad", True), \
            patch.object(settings, "exigir_minuscula_senha_ad", True), \
            patch.object(settings, "exigir_maiuscula_senha_ad", True), \
            patch.object(settings, "exigir_caractere_especial_senha_ad", True), \
            patch.object(settings, "chars_especiais_senha_ad", "!@#$%&*"):

        service = UsuarioService(usuario_repository=repo, politica_senha=None)
        novo_usuario = Usuario.criar(login="teste.settings", nome_completo="Teste Settings")

        with pytest.raises(SenhaInvalidaError) as exc_info:
            service.criar_usuario(usuario=novo_usuario, senha="")

        mensagem = str(exc_info.value)
        assert "ter no mínimo 8 caracteres" in mensagem
        assert "conter ao menos uma letra minúscula" in mensagem
        assert "conter ao menos uma letra maiúscula" in mensagem
        assert "conter ao menos um número" in mensagem
        assert "conter ao menos um caractere especial (!@#$%&*)" in mensagem

def test_deve_lancar_exceca_ao_tentar_criar_usuario_com_login_duplicado():
    usuario_existente = Usuario.criar(login="usuario.existente", nome_completo="Usuario Existente")
    repo = FakeUsuarioRepository(usuarios=[usuario_existente])
    politica = PoliticaSenha(tamanho_minimo=4, exigir_minuscula=False, exigir_maiuscula=False, exigir_numero=False, exigir_caractere_especial=False)
    service = UsuarioService(usuario_repository=repo, politica_senha=politica)

    novo_usuario_com_mesmo_login = Usuario.criar(login="usuario.existente", nome_completo="Outro Nome")

    with pytest.raises(UsuarioJaExisteError) as exc_info:
        service.criar_usuario(usuario=novo_usuario_com_mesmo_login, senha="Password123")

    assert "Usuário com o login usuario.existente já existe" in str(exc_info.value)


def test_deve_repassar_parametro_opcional_padrao_de_dn_e_forcar_senha_ao_nao_ser_informado():
    repo = FakeUsuarioRepository(usuarios=[])
    politica = PoliticaSenha(tamanho_minimo=4, exigir_minuscula=False, exigir_maiuscula=False, exigir_numero=False, exigir_caractere_especial=False)

    with patch.object(settings, "dn_padrao_ad", "OU=Usuarios,DC=empresa,DC=local"):
        service = UsuarioService(usuario_repository=repo, politica_senha=politica)
        usuario = Usuario.criar(login="teste.default", nome_completo="Teste Default")

        # Não informa forcar_troca_senha nem container_dn
        service.criar_usuario(usuario=usuario, senha="Password123")

        assert repo.ultimo_container_dn == "OU=Usuarios,DC=empresa,DC=local"
        assert repo.ultimo_forcar_troca_senha is False

# ==============================================================================
# Testes: Reativar Usuário
# ==============================================================================

def test_deve_reativar_usuario_com_sucesso():
    usuario_inativo = Usuario(
        login="carlos.inativo",
        primeiro_nome="Carlos",
        sobrenome="Inativo",
        status=StatusUsuario.INATIVO,
    )
    repo = FakeUsuarioRepository(usuarios=[usuario_inativo])
    politica = PoliticaSenha(
        tamanho_minimo=4, exigir_minuscula=False, exigir_maiuscula=False, exigir_numero=False, exigir_caractere_especial=False
    )
    service = UsuarioService(usuario_repository=repo, politica_senha=politica)

    resultado = service.reativar_usuario(
        login="carlos.inativo",
        senha="NewPassword@123",
        trocar_senha=True,
        container_dn="OU=Ativos,DC=empresa,DC=local"
    )

    assert repo.ultimo_login_reativado == "carlos.inativo"
    assert repo.ultima_senha_reativacao == "NewPassword@123"
    assert repo.ultimo_container_reativacao == "OU=Ativos,DC=empresa,DC=local"

    # Valida o retorno
    assert resultado.login == "carlos.inativo"
    assert resultado.status == StatusUsuario.ATIVO


def test_deve_lancar_excecao_ao_tentar_reativar_usuario_inexistente():
    repo = FakeUsuarioRepository(usuarios=[])
    service = UsuarioService(usuario_repository=repo)

    with pytest.raises(UsuarioNaoEncontradoError) as exc_info:
        service.reativar_usuario(login="usuario.fantasma", senha="NewPassword@123")

    assert "Usuário com login usuario.fantasma não encontrado" in str(exc_info.value)


def test_deve_lancar_excecao_ao_reativar_usuario_com_senha_invalida():
    usuario_inativo = Usuario(
        login="carlos.inativo",
        primeiro_nome="Carlos",
        sobrenome="Inativo",
        status=StatusUsuario.INATIVO,
    )
    repo = FakeUsuarioRepository(usuarios=[usuario_inativo])
    politica = PoliticaSenha(tamanho_minimo=8, exigir_numero=True) # Exige tamanho 8 e número
    service = UsuarioService(usuario_repository=repo, politica_senha=politica)

    # Senha inválida perante a política configurada
    senha_fraca = "abc"

    with pytest.raises(SenhaInvalidaError) as exc_info:
        service.reativar_usuario(login="carlos.inativo", senha=senha_fraca)

    assert "ter no mínimo 8 caracteres" in str(exc_info.value)
    # Garante que o repositório nem foi acionado para salvar/reativar
    assert repo.ultimo_login_reativado is None


def test_deve_reativar_usuario_sem_informar_senha_nova():
    usuario_inativo = Usuario(
        login="carlos.inativo",
        primeiro_nome="Carlos",
        sobrenome="Inativo",
        status=StatusUsuario.INATIVO,
    )
    repo = FakeUsuarioRepository(usuarios=[usuario_inativo])
    service = UsuarioService(usuario_repository=repo)

    # Reativa sem passar o parâmetro de senha
    resultado = service.reativar_usuario(
        login="carlos.inativo",
        container_dn="OU=Ativos,DC=empresa,DC=local"
    )

    assert repo.ultimo_login_reativado == "carlos.inativo"
    assert repo.ultima_senha_reativacao is None
    assert repo.ultimo_container_reativacao == "OU=Ativos,DC=empresa,DC=local"
    assert resultado.status == StatusUsuario.ATIVO