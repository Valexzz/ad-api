import ssl
from contextlib import contextmanager
from typing import Generator
from ldap3 import Server, Connection, Tls
from ldap3.core.exceptions import LDAPException

from ad_api.errors import InfraError


class LdapClient:
    def __init__(
            self,
            servidor: str,
            usuario: str,
            senha: str,
            porta: int = 636,
            use_ssl: bool = True,
            timeout: int = 5,
    ):
        self._host = servidor
        self._port = porta
        self._user = usuario
        self._password = senha
        self._timeout = timeout
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
        conn: None | Connection = None
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