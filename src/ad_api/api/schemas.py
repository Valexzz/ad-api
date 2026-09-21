from typing import Optional

from pydantic import BaseModel, ConfigDict

from ad_api.domain.model import StatusUsuario


class UsuarioResponse(BaseModel):
    login: str
    nome_completo: str
    matricula: Optional[str] = None
    status: StatusUsuario

    model_config = ConfigDict(from_attributes=True)