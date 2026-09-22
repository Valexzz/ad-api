import logging
from typing import Optional

from ad_api.config import settings
from ad_api.domain.model import Usuario, PoliticaSenha
from ad_api.domain.ports import UsuarioRepository
from ad_api.errors import UsuarioNaoEncontradoError, UsuarioJaExisteError

logger = logging.getLogger(__name__)


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
        logger.info(f"[BUSCAR_USUARIO_SERVICE] - Iniciando busca pelo login: {login}")
        usuario = self.repository.buscar_por_login(login)
        if not usuario:
            logger.warning(f"[BUSCAR_USUARIO_SERVICE] - Usuário com login {login} não encontrado.")
            raise UsuarioNaoEncontradoError(f'Usuário com login {login} não encontrado')
        logger.info(f"[BUSCAR_USUARIO_SERVICE] - Usuário com login {login} encontrado com sucesso.")
        return usuario

    def criar_usuario(self, usuario: Usuario, senha: str, trocar_senha: bool = False, container_dn: Optional[str] = None):
        logger.info(f"[CRIAR_USUARIO_SERVICE] - Iniciando processo de criação para o login: {usuario.login}")

        self.politica_senha.validar(senha)

        if self.repository.buscar_por_login(usuario.login):
            logger.warning(f"[CRIAR_USUARIO_SERVICE] - Tentativa de criar usuário já existente com o login: {usuario.login}")
            raise UsuarioJaExisteError(f"Usuário com o login {usuario.login} já existe")

        container_dn = container_dn or settings.dn_padrao_ad
        logger.debug(f"[CRIAR_USUARIO_SERVICE] - Utilizando container DN: {container_dn} para o login: {usuario.login}")

        self.repository.criar_usuario(
            usuario=usuario,
            senha=senha,
            trocar_senha=trocar_senha,
            container_dn=container_dn
        )

        logger.info(f"[CRIAR_USUARIO_SERVICE] - Usuário com login {usuario.login} criado com sucesso no repositório.")
        return usuario

    def reativar_usuario(self, login: str, senha: Optional[str] = None, trocar_senha: bool = False, container_dn: Optional[str] = None) -> Usuario:
        logger.info(f"[REATIVAR_USUARIO_SERVICE] - Iniciando processo de reativação para o login: {login}")

        if senha:
            logger.debug(f"[REATIVAR_USUARIO_SERVICE] - Validando nova senha fornecida na reativação para o login: {login}")
            self.politica_senha.validar(senha)

        usuario = self.repository.buscar_por_login(login)

        if not usuario:
            logger.warning(f"[REATIVAR_USUARIO_SERVICE] - Tentativa de reativar usuário inexistente com o login: {login}")
            raise UsuarioNaoEncontradoError(f'Usuário com login {login} não encontrado')

        logger.info(f"[REATIVAR_USUARIO_SERVICE] - Executando reativação no repositório para o login: {login}")
        usuario_reativado = self.repository.reativar_usuario(
            login=login,
            senha=senha,
            trocar_senha=trocar_senha,
            container_dn=container_dn
        )
        logger.info(f"[REATIVAR_USUARIO_SERVICE] - Usuário com login {login} reativado com sucesso.")
        return usuario_reativado

    def redefinir_senha(
            self,
            login: str,
            senha: str,
            trocar_senha: bool = False,
    ) -> Usuario:
        logger.info(f"[REDEFINIR_SENHA_SERVICE] - Iniciando processo de redefinição de senha para o login: {login}")

        usuario = self.repository.buscar_por_login(login)
        if not usuario:
            logger.warning(f"[REDEFINIR_SENHA_SERVICE] - Tentativa de redefinir senha para usuário inexistente com o login: {login}")
            raise UsuarioNaoEncontradoError(f"Usuário com login '{login}' não encontrado.")

        self.politica_senha.validar(senha)

        logger.info(f"[REDEFINIR_SENHA_SERVICE] - Executando redefinição de senha no repositório para o login: {login}")
        usuario_redefinido = self.repository.redefinir_senha(
            login=login,
            senha=senha,
            trocar_senha=trocar_senha,
        )
        logger.info(f"[REDEFINIR_SENHA_SERVICE] - Senha redefinida com sucesso para o login: {login}")
        return usuario_redefinido