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

    @abstractmethod
    def reativar_usuario(
            self,
            login: str,
            senha: Optional[str] = None,
            trocar_senha: bool = False,
            container_dn: Optional[str] = None,
    ) -> Usuario:
        """
        Reativa uma conta desativada no AD, permitindo opcionalmente redefinir a senha
        e/ou movê-la para uma nova OU/Container (RF02).

        :param login: Login (sAMAccountName) do usuário a ser reativado.
        :param senha: Opcional. Se informada, redefine a senha durante a reativação.
        :param trocar_senha: Se True e houver senha, seta pwdLastSet = 0 (RN02).
        :param container_dn: Opcional. Nova OU/Container de destino para mover o usuário.
        """
        raise NotImplementedError