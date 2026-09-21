from fastapi import APIRouter, Depends

from ad_api.api.dependencies import get_usuario_service
from ad_api.api.schemas import UsuarioResponse
from ad_api.domain.model import Usuario
from ad_api.services.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

@router.get("/{login}", response_model=UsuarioResponse)
def buscar_usuario_por_login(
        login: str,
        service: UsuarioService = Depends(get_usuario_service)
) -> Usuario:
    return service.buscar_usuario_por_login(login)