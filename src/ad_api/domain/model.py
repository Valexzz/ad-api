from dataclasses import dataclass
from enum import Enum
from typing import Optional

class StatusUsuario(str, Enum):
    ATIVO = 'Ativo'
    INATIVO = 'Inativo'

@dataclass
class Usuario:
    login: str
    primeiro_nome: str
    sobrenome: str
    status: StatusUsuario
    matricula: Optional[str] = None

    @property
    def nome_completo(self) -> str:
        return f"{self.primeiro_nome} {self.sobrenome}".strip()