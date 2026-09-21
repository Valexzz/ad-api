import pytest
from ldap3 import Server, Connection, MOCK_SYNC, OFFLINE_AD_2012_R2

@pytest.fixture
def ldap_mock_conn():
    server = Server('server_ad_fake', get_info=OFFLINE_AD_2012_R2)

    conn = Connection(
        server,
        user="cn=admin,dc=fake,dc=local",
        password="senhaSuperSegura@123",
        client_strategy=MOCK_SYNC
    )
    conn.bind()

    conn.strategy.add_entry(
        'CN=victor,OU=Users,DC=fake,DC=local',
        {
            'objectCategory': 'person',
            'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
            'sAMAccountName': 'victor',
            'givenName': 'Victor',
            'sn': 'Alexandre Borges Milhomem',
            'userAccountControl': 512,  # 512 = NORMAL_ACCOUNT (Ativo)
            'employeeID': '12345'
        }
    )

    return conn