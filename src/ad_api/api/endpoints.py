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

@router.get("/{login}", status_code=status.HTTP_200_OK, response_model=UsuarioResponse)
def buscar_usuario_por_login(
        login: str,
        service: UsuarioService = Depends(get_usuario_service)
):
    logger.info(f"[BUSCAR_USUARIO] - Requisição recebida para buscar o login: {login}")
    return service.buscar_usuario_por_login(login)

@router.post("", status_code=status.HTTP_201_CREATED, response_model=UsuarioResponse)
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

@router.patch("/{login}/desativar", status_code=status.HTTP_200_OK, response_model=UsuarioResponse)
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

@router.patch("/{login}/redefinir-senha", status_code=status.HTTP_200_OK, response_model=UsuarioResponse)
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