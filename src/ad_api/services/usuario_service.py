from typing import Optional

from ad_api.config import settings
from ad_api.domain.model import Usuario, PoliticaSenha
from ad_api.domain.ports import UsuarioRepository
from ad_api.errors import UsuarioNaoEncontradoError, UsuarioJaExisteError


class UsuarioService:

    def __init__(self, usuario_repository: UsuarioRepository, politica_senha: Optional[PoliticaSenha] = None):
        self.repository = usuario_repository
        self.politica_senha = politica_senha or PoliticaSenha(
            tamanho_minimo=settings.tamanho_minimo_senha_ad,
            exigir_numero=settings.exigir_numero_senha_ad,
            exigir_minuscula=settings.exigir_minuscula_senha_ad,
            exigir_maiuscula=settings.exigir_maiuscula_senha_ad,
            exigir_caractere_especial=settings.exigir_caractere_especial_senha_ad,
            chars_especiais=settings.chars_especiais_senha_ad,
        )

    def buscar_usuario_por_login(self, login: str) -> Usuario:
        usuario = self.repository.buscar_por_login(login)
        if not usuario:
            raise UsuarioNaoEncontradoError(f'Usuário com login {login} não encontrado')
        return usuario

    def criar_usuario(self, usuario: Usuario, senha: str, trocar_senha: bool = False, container_dn: Optional[str] = None):
        #Validar senha

        self.politica_senha.validar(senha)

        if self.repository.buscar_por_login(usuario.login):
            raise UsuarioJaExisteError(f"Usuário com o login {usuario.login} já existe")

        container_dn = container_dn or settings.dn_padrao_ad

        self.repository.criar_usuario(
            usuario=usuario,
            senha=senha,
            trocar_senha=trocar_senha,
            container_dn=container_dn
        )

        return usuario

    def reativar_usuario(self, login: str, senha: Optional[str] = None, trocar_senha: bool = False, container_dn: Optional[str] = None) -> Usuario:

        if senha:
            self.politica_senha.validar(senha)

        usuario = self.repository.buscar_por_login(login)

        if not usuario:
            raise UsuarioNaoEncontradoError(f'Usuário com login {login} não encontrado')

        return self.repository.reativar_usuario(
            login=login,
            senha=senha,
            trocar_senha=trocar_senha,
            container_dn=container_dn
        )