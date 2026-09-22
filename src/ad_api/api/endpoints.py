import logging
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from ad_api.api.dependencies import get_usuario_service, verificar_api_key
from ad_api.api.schemas import UsuarioResponse, UsuarioRequest, UsuarioReativarRequest, UsuarioRedefinirSenhaRequest
from ad_api.domain.model import Usuario
from ad_api.errors import DomainError
from ad_api.services.usuario_service import UsuarioService

logger = logging.getLogger("ad_api")

router = APIRouter(prefix="/usuarios", tags=["Usuários"], dependencies=[Depends(verificar_api_key)])

from fastapi import APIRouter, Depends, status
from ad_api.api.schemas import UsuarioResponse, ModeloErro

@router.get(
    "/{login}",
    status_code=status.HTTP_200_OK,
    response_model=UsuarioResponse,
    summary="Consultar dados de um usuário",
    description="Busca e retorna os atributos, status da conta e status da senha do usuário no Active Directory a partir do seu login (sAMAccountName).",
    responses={
        200: {
            "description": "Usuário encontrado com sucesso.",
            "model": UsuarioResponse,
        },
        401: {
            "description": "Chave de API ausente ou inválida.",
            "model": ModeloErro,
        },
        403: {
            "description": "Acesso negado para o endereço IP de origem.",
            "model": ModeloErro,
        },
        404: {
            "description": "Usuário não encontrado no Active Directory.",
            "model": ModeloErro,
        },
        502: {
            "description": "Falha de comunicação ou timeout com o Active Directory.",
            "model": ModeloErro,
        },
    },
)
def buscar_usuario_por_login(
        login: str,
        service: UsuarioService = Depends(get_usuario_service)
):
    logger.info(f"[BUSCAR_USUARIO] - Requisição recebida para buscar o login: {login}")
    return service.buscar_usuario_por_login(login)
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=UsuarioResponse,
    summary="Cadastrar novo usuário",
    description="Permite o cadastro de um novo usuário no Active Directory, aceitando parâmetros opcionais de matrícula e container/OU de destino.",
    responses={
        201: {
            "description": "Usuário cadastrado com sucesso.",
            "model": UsuarioResponse,
        },
        400: {
            "description": "Erro de validação, dados inválidos ou violação de política de senha.",
            "model": ModeloErro,
        },
        401: {
            "description": "Chave de API ausente ou inválida.",
            "model": ModeloErro,
        },
        409: {
            "description": "Usuário já existe no Active Directory.",
            "model": ModeloErro,
        },
        502: {
            "description": "Falha de comunicação ou timeout com o Active Directory.",
            "model": ModeloErro,
        },
    },
)
def criar_usuario(
        payload: UsuarioRequest,
        service: UsuarioService = Depends(get_usuario_service)
):
    logger.info(f"[CRIAR_USUARIO] - Requisição recebida para cadastrar o login: {payload.login}")
    logger.debug(f"[CRIAR_USUARIO] - Dados recebidos para o login {payload.login}")

    usuario_dominio = Usuario.criar(
        login=payload.login,
        nome_completo=payload.nome_completo,
        primeiro_nome=payload.primeiro_nome,
        sobrenome=payload.sobrenome,
        matricula=payload.matricula,
        status=payload.status,
    )

    usuario_criado = service.criar_usuario(usuario=usuario_dominio,
                                           senha=payload.senha,
                                           trocar_senha=payload.trocar_senha,
                                           container_dn=payload.container_dn
                                           )

    logger.info(f"[CRIAR_USUARIO] - Usuário {payload.login} processado com sucesso")
    return usuario_criado

@router.patch(
    "/{login}/desativar",
    status_code=status.HTTP_200_OK,
    response_model=UsuarioResponse,
    summary="Reativar usuário",
    description="Permite a reativação de uma conta desativada no Active Directory, com opção opcional de nova senha e movimentação para uma OU específica.",
    responses={
        200: {
            "description": "Usuário reativado com sucesso.",
            "model": UsuarioResponse,
        },
        400: {
            "description": "Erro de validação ou violação de política de senha.",
            "model": ModeloErro,
        },
        401: {
            "description": "Chave de API ausente ou inválida.",
            "model": ModeloErro,
        },
        403: {
            "description": "Acesso negado para o endereço IP de origem.",
            "model": ModeloErro,
        },
        404: {
            "description": "Usuário não encontrado no Active Directory.",
            "model": ModeloErro,
        },
        502: {
            "description": "Falha de comunicação ou timeout com o Active Directory.",
            "model": ModeloErro,
        },
    },
)
def reativar_usuario(
        login: str,
        payload: UsuarioReativarRequest,
        service: UsuarioService = Depends(get_usuario_service)
):
    logger.info(f"[REATIVAR_USUARIO] - Requisição recebida para reativar o login: {login}")
    logger.debug(f"[REATIVAR_USUARIO] - Dados de reativação para o login {login}")

    usuario_reativado = service.reativar_usuario(
        login=login,
        senha=payload.senha,
        trocar_senha=payload.trocar_senha,
        container_dn=payload.container_dn
    )

    logger.info(f"[REATIVAR_USUARIO] - Usuário {login} reativado com sucesso")
    return usuario_reativado

@router.patch(
    "/{login}/redefinir-senha",
    status_code=status.HTTP_200_OK,
    response_model=UsuarioResponse,
    summary="Redefinir senha de usuário",
    description="Permite redefinir a senha de um usuário existente no Active Directory sem a necessidade de informar a senha atual.",
    responses={
        200: {
            "description": "Senha redefinida com sucesso.",
            "model": UsuarioResponse,
        },
        400: {
            "description": "Violação de política de complexidade de senha.",
            "model": ModeloErro,
        },
        401: {
            "description": "Chave de API ausente ou inválida.",
            "model": ModeloErro,
        },
        403: {
            "description": "Acesso negado para o endereço IP de origem.",
            "model": ModeloErro,
        },
        404: {
            "description": "Usuário não encontrado no Active Directory.",
            "model": ModeloErro,
        },
        502: {
            "description": "Falha de comunicação ou timeout com o Active Directory.",
            "model": ModeloErro,
        },
    },
)
def redefinir_senha(
        login: str,
        payload: UsuarioRedefinirSenhaRequest,
        service: UsuarioService = Depends(get_usuario_service)
):
    logger.info(f"[REDEFINIR_SENHA] - Requisição recebida para redefinir senha do login: {login}")

    usuario_redefinido = service.redefinir_senha(
        login=login,
        senha=payload.senha,
        trocar_senha=payload.trocar_senha,
    )

    logger.info(f"[REDEFINIR_SENHA] - Senha do usuário {login} redefinida com sucesso")
    return usuario_redefinido