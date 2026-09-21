import ssl
from contextlib import contextmanager
from typing import Generator
from ldap3 import Server, Connection, Tls

from ad_api.config import settings


class LdapClient:
    def __init__(self):
        tls_config = Tls(validate=ssl.CERT_NONE)

        self.server = Server(
            host=settings.servidor_ad,
            port=636,
            use_ssl=True,
            tls=tls_config,
            connect_timeout=settings.timeout_ldap,
        )

    @contextmanager
    def get_conn(self) -> Generator[Connection, None, None]:
        conn = Connection(
            self.server,
            user=settings.usuario_service_account_ad,
            password=settings.senha_usuario_service_account_ad,
            auto_bind=True,
            receive_timeout=settings.timeout_ldap
        )
        try:
            yield conn
        finally:
            conn.unbind()