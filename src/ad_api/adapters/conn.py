import ssl
from contextlib import contextmanager
from typing import Generator
from ldap3 import Server, Connection, Tls

from ad_api.config import settings


class LdapClient:
    def __init__(self):
        # RNF04: LDAPS
        tls_config = Tls(validate=ssl.CERT_REQUIRED)

        # RNF06: Timeout de conexão de 5s
        self.server = Server(
            host=settings.ad_server,
            port=636,
            use_ssl=True,
            tls=tls_config,
            connect_timeout=5,
        )

    @contextmanager
    def get_connection(self) -> Generator[Connection, None, None]:
        # RNF03: Service Account
        # RNF06: Timeout de resposta de 5s
        conn = Connection(
            self.server,
            user=settings.ad_user,
            password=settings.ad_password,
            auto_bind=True,
            receive_timeout=5,
        )
        try:
            yield conn
        finally:
            conn.unbind()