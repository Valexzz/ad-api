import pytest

from ad_api.domain.model import PoliticaSenha, StatusUsuario, Usuario
from ad_api.errors import DomainError, SenhaInvalidaError


def test_deve_criar_usuario_com_primeiro_e_sobrenome_separados_ao_enviar_nome_completo():
    usuario = Usuario.criar(
        login="joao.silva",
        nome_completo="João Carlos da Silva",
    )

    assert usuario.login == "joao.silva"
    assert usuario.primeiro_nome == "João"
    assert usuario.sobrenome == "Carlos da Silva"
    assert usuario.nome_completo == "João Carlos da Silva"
    assert usuario.status == StatusUsuario.ATIVO


def test_deve_criar_usuario_com_nome_completo_com_somente_uma_palavra():
    usuario = Usuario.criar(
        login="mononimo",
        nome_completo="Platão",
    )

    assert usuario.login == "mononimo"
    assert usuario.primeiro_nome == "Platão"
    assert usuario.sobrenome == ""
    assert usuario.nome_completo == "Platão"


def test_deve_falhar_ao_criar_usuario_sem_nome():
    with pytest.raises(DomainError) as exc_info:
        Usuario.criar(login="usuario.sem.nome")

    assert "É necessário informar 'nome_completo' ou 'primeiro_nome'" in str(exc_info.value)


def test_deve_falhar_ao_criar_usuario_com_login_fazio_ou_em_branco():
    with pytest.raises(DomainError) as exc_info_vazio:
        Usuario.criar(login="", nome_completo="Teste Silva")

    assert "O login do usuário é obrigatório." in str(exc_info_vazio.value)

    with pytest.raises(DomainError) as exc_info_espacos:
        Usuario.criar(login="   ", nome_completo="Teste Silva")

    assert "O login do usuário é obrigatório." in str(exc_info_espacos.value)


def test_deve_acumular_todas_as_falhas_quando_senha_for_totalmente_nula_ou_invalida():
    politica = PoliticaSenha(
        tamanho_minimo=8,
        exigir_minuscula=True,
        exigir_maiuscula=True,
        exigir_numero=True,
        exigir_caractere_especial=True,
        chars_especiais="!@#$%&*",
    )

    with pytest.raises(SenhaInvalidaError) as exc_info:
        politica.validar("")

    mensagem = str(exc_info.value)
    assert "ter no mínimo 8 caracteres" in mensagem
    assert "conter ao menos uma letra minúscula" in mensagem
    assert "conter ao menos uma letra maiúscula" in mensagem
    assert "conter ao menos um número" in mensagem
    assert "conter ao menos um caractere especial (!@#$%&*)" in mensagem


def test_deve_respeitar_caracteres_especiais_personalizados():
    # Política aceitando apenas interrogação e ponto final como caracteres válidos
    politica = PoliticaSenha(
        tamanho_minimo=6,
        exigir_minuscula=True,
        exigir_maiuscula=True,
        exigir_numero=True,
        exigir_caractere_especial=True,
        chars_especiais="?.",
    )

    # Senha com @ (que é especial em outras políticas, mas não nesta)
    senha_invalida_nesta_politica = "Senha@123"
    with pytest.raises(SenhaInvalidaError) as exc_invalida:
        politica.validar(senha_invalida_nesta_politica)

    assert "conter ao menos um caractere especial (?.)" in str(exc_invalida.value)

    # Senha atendendo os caracteres personalizados desta política
    senha_valida = "Senha?123"
    politica.validar(senha_valida)  # Não deve lançar exceção