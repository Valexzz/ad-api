import ssl
from contextlib import contextmanager
from typing import Generator, Optional
from ldap3 import Server, Connection, Tls
from ldap3.core.exceptions import LDAPException

from ad_api.config import settings
from ad_api.errors import InfraError


class LdapClient:
    def __init__(
            self,
            server: Optional[str] = None,
            port: Optional[int] = None,
            user: Optional[str] = None,
            password: Optional[str] = None,
            use_ssl: bool = True,
            timeout: Optional[int] = None,
    ):
        self._host = server or settings.servidor_ad
        self._port = port or 636
        self._user = user or settings.usuario_service_account_ad
        self._password = password or settings.senha_usuario_service_account_ad
        self._timeout = timeout or settings.timeout_ldap
        self._use_ssl = use_ssl

        tls_config = Tls(validate=ssl.CERT_NONE) if self._use_ssl else None

        self.server = Server(
            host=self._host,
            port=self._port,
            use_ssl=self._use_ssl,
            tls=tls_config,
            connect_timeout=self._timeout,
        )

    @contextmanager
    def get_conn(self) -> Generator[Connection, None, None]:
        conn: Optional[Connection] = None
        try:
            conn = Connection(
                self.server,
                user=self._user,
                password=self._password,
                auto_bind=True,
                receive_timeout=self._timeout,
            )
            yield conn
        except LDAPException as exc:
            raise InfraError(f"Falha de comunicação com o servidor LDAP: {exc}") from exc
        finally:
            if conn and conn.bound:
                conn.unbind()