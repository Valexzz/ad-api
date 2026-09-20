import abc
from typing import Optional

from ad_api.domain.model import Usuario


class UsuarioRepository(abc.ABC):

    @abc.abstractmethod
    def buscar_por_login(self, login: str) -> Optional[Usuario]:
        pass
