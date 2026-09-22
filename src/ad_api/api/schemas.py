from typing import Optional

from pydantic import BaseModel, ConfigDict

from ad_api.domain.model import StatusUsuario


class UsuarioResponse(BaseModel):
    login: str
    nome_completo: str
    matricula: Optional[str] = None
    status: StatusUsuario

    model_config = ConfigDict(from_attributes=True)

class UsuarioRequest(BaseModel):
    login: str
    senha: str
    trocar_senha: bool = False
    status: StatusUsuario
    nome_completo: Optional[str] = None
    primeiro_nome: Optional[str] = None
    sobrenome: Optional[str] = None
    matricula: Optional[str] = None
    container_dn: Optional[str] = None

class UsuarioReativarRequest(BaseModel):
    senha: str
    trocar_senha: bool = False
    container_dn: Optional[str] = None