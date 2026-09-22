from typing import Optional

from ldap3 import MODIFY_REPLACE
from ldap3.core.exceptions import LDAPEntryAlreadyExistsResult, LDAPException
from ldap3.utils.conv import escape_filter_chars
from ldap3.utils.dn import escape_rdn

from ad_api.adapters.conn import LdapClient
from ad_api.config import settings
from ad_api.domain.model import StatusUsuario, Usuario
from ad_api.domain.ports import UsuarioRepository
from ad_api.errors import (
    InfraError,
    UsuarioJaExisteError,
    UsuarioSemLoginError, UsuarioNaoEncontradoError,
)
from ad_api.utils import obter_valor_atributo_ad


class UsuarioLdapRepository(UsuarioRepository):
    HEX_CONTA_INATIVA = 0x0002 # 514
    HEX_CONTA_NORMAL = 0x0200  # 512

    def __init__(
            self,
            ldap_client: LdapClient,
            base_dn: Optional[str] = None,
            dn_padrao: Optional[str] = None,
    ):
        self.ldap_client = ldap_client
        self.base_dn = base_dn or settings.dn_base_ad
        self.dn_padrao = dn_padrao or getattr(settings, "dn_padrao_ad", self.base_dn)

    def buscar_por_login(self, login: str) -> Optional[Usuario]:
        login_sanitizado = escape_filter_chars(login)
        filtro = f"(&(objectCategory=person)(objectClass=user)(sAMAccountName={login_sanitizado}))"
        atributos = ["sAMAccountName", "givenName", "sn", "userAccountControl", "employeeID"]

        with self.ldap_client.get_conn() as conn:
            conn.search(
                search_base=self.base_dn,
                search_filter=filtro,
                attributes=atributos,
            )

            if not conn.entries:
                return None

            registro = conn.entries[0]

            raw_uac = registro["userAccountControl"].value if "userAccountControl" in registro else 0
            account_control = int(raw_uac or 0)

            status_usuario = (
                StatusUsuario.INATIVO if account_control & self.HEX_CONTA_INATIVA
                else StatusUsuario.ATIVO
            )

            login_ad = obter_valor_atributo_ad(registro, "sAMAccountName")
            if login_ad is None:
                raise UsuarioSemLoginError("Usuário não possui login no AD")

            return Usuario(
                login=obter_valor_atributo_ad(registro, "sAMAccountName", login_sanitizado),
                primeiro_nome=obter_valor_atributo_ad(registro, "givenName", ""),
                sobrenome=obter_valor_atributo_ad(registro, "sn", ""),
                status=status_usuario,
                matricula=obter_valor_atributo_ad(registro, "employeeID", None),
            )

    def criar_usuario(
            self,
            usuario: Usuario,
            senha: str,
            trocar_senha: bool = False,
            container_dn: Optional[str] = None,
    ) -> Usuario:
        user_dn, atributos = self._preparar_dados_criacao(usuario, senha, trocar_senha, container_dn)

        self._executar_criacao_no_ad(usuario.login, user_dn, atributos)

        return usuario

    def _preparar_dados_criacao(
            self, usuario: Usuario, senha: str, trocar_senha: bool, container_dn: Optional[str]
    ) -> tuple[str, dict]:
        target_container = container_dn or self.dn_padrao
        cn_valor = usuario.nome_completo if usuario.nome_completo else usuario.login
        rdn = f"CN={escape_rdn(cn_valor)}"
        user_dn = f"{rdn},{target_container}"

        uac = self.HEX_CONTA_NORMAL
        if usuario.status == StatusUsuario.INATIVO:
            uac |= self.HEX_CONTA_INATIVA

        senha_codificada = f'"{senha}"'.encode("utf-16le")

        atributos = {
            "sAMAccountName": usuario.login,
            "userPrincipalName": f"{usuario.login}@{getattr(settings, 'dominio_ad', 'empresa.local')}",
            "unicodePwd": senha_codificada,
            "userAccountControl": uac,
        }

        if usuario.primeiro_nome:
            atributos["givenName"] = usuario.primeiro_nome
        if usuario.sobrenome:
            atributos["sn"] = usuario.sobrenome
        if usuario.nome_completo:
            atributos["displayName"] = usuario.nome_completo
        if usuario.matricula:
            atributos["employeeID"] = usuario.matricula
        if trocar_senha:
            atributos["pwdLastSet"] = 0

        return user_dn, atributos

    def _executar_criacao_no_ad(self, login: str, user_dn: str, atributos: dict) -> None:
        with self.ldap_client.get_conn() as conn:
            try:
                sucesso = conn.add(
                    dn=user_dn,
                    object_class=["top", "person", "organizationalPerson", "user"],
                    attributes=atributos,
                )

                if not sucesso:
                    resultado = conn.result
                    if resultado.get("result") == 68 or resultado.get("description") == "entryAlreadyExists":
                        raise UsuarioJaExisteError(f"Usuário com login '{login}' já existe no AD.")
                    raise InfraError(
                        f"Falha ao criar usuário no AD: {resultado.get('description')} - {resultado.get('message')}"
                    )

            except LDAPEntryAlreadyExistsResult as exc:
                raise UsuarioJaExisteError(f"Usuário com login '{login}' já existe no AD.") from exc

    def reativar_usuario(
            self,
            login: str,
            senha: Optional[str] = None,
            trocar_senha: bool = False,
            container_dn: Optional[str] = None,
    ) -> Usuario:
        with self.ldap_client.get_conn() as conn:
            try:
                dn_atual, uac_atual = self._obter_dados_iniciais(conn, login)

                if container_dn:
                    dn_atual = self._mover_usuario(conn, dn_atual, container_dn)

                self._aplicar_reativacao_e_senha(conn, dn_atual, uac_atual, senha, trocar_senha)

            except LDAPException as exc:
                raise InfraError(f"Erro de comunicação com o AD ao reativar usuário: {exc}") from exc

        return self.buscar_por_login(login)

    def _obter_dados_iniciais(self, conn, login: str) -> tuple[str, int]:
        conn.search(
            search_base=self.base_dn,
            search_filter=f"(sAMAccountName={login})",
            attributes=["userAccountControl"]
        )
        if not conn.entries:
            raise UsuarioNaoEncontradoError(f"Usuário com login '{login}' não encontrado no AD.")

        entry = conn.entries[0]
        dn = entry.entry_dn
        uac = int(entry.userAccountControl.value) if "userAccountControl" in entry else self.HEX_CONTA_NORMAL

        return dn, uac

    def _mover_usuario(self, conn, dn_atual: str, container_dn: str) -> str:
        rdn = dn_atual.split(",")[0]
        sucesso_movimento = conn.modify_dn(
            dn=dn_atual,
            relative_dn=rdn,
            new_superior=container_dn
        )
        if not sucesso_movimento:
            resultado = conn.result
            raise InfraError(
                f"Falha ao mover usuário no AD: {resultado.get('description')} - {resultado.get('message')}"
            )
        return f"{rdn},{container_dn}"

    def _aplicar_reativacao_e_senha(self, conn, dn_atual: str, uac_atual: int, senha: Optional[str], trocar_senha: bool) -> None:
        uac_novo = uac_atual & ~self.HEX_CONTA_INATIVA

        changes = {
            "userAccountControl": [(MODIFY_REPLACE, [uac_novo])]
        }

        if senha:
            senha_codificada = f'"{senha}"'.encode("utf-16le")
            changes["unicodePwd"] = [(MODIFY_REPLACE, [senha_codificada])]
            if trocar_senha:
                changes["pwdLastSet"] = [(MODIFY_REPLACE, [0])]

        sucesso = conn.modify(dn=dn_atual, changes=changes)
        if not sucesso:
            resultado = conn.result
            raise InfraError(
                f"Falha ao reativar usuário no AD: {resultado.get('description')} - {resultado.get('message')}"
            )