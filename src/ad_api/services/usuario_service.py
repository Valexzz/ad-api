from typing import Optional

from ad_api.domain.model import Usuario
from ad_api.domain.ports import UsuarioRepository
from ad_api.errors import UsuarioNaoEncontradoError


class UsuarioService:

    def __init__(self, usuario_repository: UsuarioRepository):
        self.repository = usuario_repository

    def buscar_usuario_por_login(self, login: str) -> Usuario:
        usuario = self.repository.buscar_por_login(login)
        if not usuario:
            raise UsuarioNaoEncontradoError(f'Usuário com login {login} não encontrado')
        return usuario