from typing import Optional

from ldap3.utils.conv import escape_filter_chars

from ad_api.adapters.conn import LdapClient
from ad_api.config import settings
from ad_api.domain.model import Usuario, StatusUsuario
from ad_api.domain.ports import UsuarioRepository
from ad_api.errors import UsuarioSemLoginError
from ad_api.utils import obter_valor_atributo_ad


class UsuarioLdapRepository(UsuarioRepository):
    HEX_CONTA_INATIVA = 0x0002

    def __init__(
            self,
            ldap_client: LdapClient,
            base_dn: Optional[str] = None
    ):
        self.ldap_client = ldap_client
        self.base_dn = base_dn or settings.dn_base_ad


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
                StatusUsuario.INATIVO if account_control
                & self.HEX_CONTA_INATIVA
                else StatusUsuario.ATIVO
            )

            login_ad = obter_valor_atributo_ad(registro,"sAMAccountName")
            if login_ad is None:
                raise UsuarioSemLoginError("Usuário não possui login no AD")
            return Usuario(
                login=obter_valor_atributo_ad(registro,"sAMAccountName", login_sanitizado),
                primeiro_nome=obter_valor_atributo_ad(registro,"givenName", ""),
                sobrenome=obter_valor_atributo_ad(registro,"sn", ""),
                status=status_usuario,
                matricula=obter_valor_atributo_ad(registro,"employeeID", None)
            )
