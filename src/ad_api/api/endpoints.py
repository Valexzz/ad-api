from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from ad_api.api.dependencies import get_usuario_service
from ad_api.api.schemas import UsuarioResponse, UsuarioRequest, UsuarioReativarRequest
from ad_api.domain.model import Usuario
from ad_api.errors import DomainError
from ad_api.services.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

@router.get("/{login}", status_code=status.HTTP_200_OK, response_model=UsuarioResponse)
def buscar_usuario_por_login(
        login: str,
        service: UsuarioService = Depends(get_usuario_service)
):
    return service.buscar_usuario_por_login(login)

@router.post("", status_code=status.HTTP_201_CREATED, response_model=UsuarioResponse)
def criar_usuario(
        payload: UsuarioRequest,
        service: UsuarioService = Depends(get_usuario_service)
):
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

    return usuario_criado

@router.put("/{login}", status_code=status.HTTP_200_OK, response_model=UsuarioResponse)
def reativar_usuario(
        login: str,
        payload: UsuarioReativarRequest,
        service: UsuarioService = Depends(get_usuario_service)
):

    usuario_reativado = service.reativar_usuario(
        login=login,
        senha=payload.senha,
        trocar_senha=payload.trocar_senha,
        container_dn=payload.container_dn
    )

    return usuario_reativado