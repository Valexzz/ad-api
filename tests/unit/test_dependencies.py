import pytest
from fastapi import HTTPException
from ad_api.api.dependencies import get_perfil_ad_autenticado, get_usuario_service
from ad_api.config import ad_config, settings, PerfilAD, PoliticaSenhaConfig
from ad_api.errors import ChaveApiInvalidaError

@pytest.fixture(autouse=True)
def mock_perfis_ad(monkeypatch):
    perfis = {
        "ad1": PerfilAD(
            servidor="ldap.ad1.local",
            dominio="ad1.local",
            dominio_netbios="AD1",
            usuario_service_account="svc1",
            senha_service_account="pwd1",
            env_senha_service_account="",
            chave_api_hash="hash_ad1",
            env_chave_api_hash="",
            dn_base="DC=ad1,DC=local",
            dn_padrao="OU=Users,DC=ad1,DC=local",
        ),
        "ad2": PerfilAD(
            servidor="ldap.ad2.local",
            dominio="ad2.local",
            dominio_netbios="AD2",
            usuario_service_account="svc2",
            senha_service_account="pwd2",
            env_senha_service_account="",
            chave_api_hash="hash_ad2",
            env_chave_api_hash="",
            dn_base="DC=ad2,DC=local",
            dn_padrao="OU=Users,DC=ad2,DC=local",
        )
    }
    monkeypatch.setattr(ad_config, "ads", perfis)
    monkeypatch.setattr(settings, "ad_padrao", "ad1")

def test_deve_selecionar_ad_padrao_quando_ad_for_omitido():
    perfil = get_perfil_ad_autenticado(ad=None, api_key="hash_ad1")
    assert perfil.dominio == "ad1.local"

def test_deve_selecionar_ad_especificado():
    perfil = get_perfil_ad_autenticado(ad="ad2", api_key="hash_ad2")
    assert perfil.dominio == "ad2.local"

def test_deve_rejeitar_chave_do_ad1_ao_solicitar_ad2():
    with pytest.raises(ChaveApiInvalidaError):
        get_perfil_ad_autenticado(ad="ad2", api_key="hash_ad1")

def test_deve_lancar_404_para_ad_inexistente():
    with pytest.raises(HTTPException) as exc_info:
        get_perfil_ad_autenticado(ad="fantasma", api_key="hash_ad1")
    assert exc_info.value.status_code == 404

def test_deve_instanciar_service_com_politica_e_repositorio_do_perfil():
    perfil = PerfilAD(
        servidor="ldap.ad2.local",
        dominio="ad2.local",
        dominio_netbios="AD2",
        usuario_service_account="svc2",
        senha_service_account="pwd2",
        env_senha_service_account="",
        chave_api_hash="hash_ad2",
        env_chave_api_hash="",
        dn_base="DC=ad2,DC=local",
        dn_padrao="OU=Users,DC=ad2,DC=local",
        politica_senha=PoliticaSenhaConfig(tamanho_minimo=14, exigir_numero=True)
    )

    service = get_usuario_service(perfil=perfil)

    assert service.repository.dn_base == "DC=ad2,DC=local"
    assert service.repository.dominio == "ad2.local"
    assert service.politica_senha.tamanho_minimo == 14