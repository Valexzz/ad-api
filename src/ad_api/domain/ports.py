from abc import ABC, abstractmethod
from typing import Optional

from ad_api.domain.model import Usuario


class UsuarioRepository(ABC):

    @abstractmethod
    def buscar_por_login(self, login: str) -> Optional[Usuario]:
        raise NotImplementedError

    @abstractmethod
    def criar_usuario(
            self,
            usuario: Usuario,
            senha: str,
            trocar_senha: bool = False,
            container_dn: Optional[str] = None,
    ) -> Usuario:
        """
        Cria um novo usuário no AD.

        :param usuario: Entidade Usuario contendo login, nomes, status e matrícula.
        :param senha: Senha em texto claro (já validada pelas regras de complexidade).
        :param trocar_senha: Se True, seta pwdLastSet = 0 (RN02).
        :param container_dn: OU ou container de destino. Se None, o repositório usa o padrão.
        """
        raise NotImplementedError