import pytest
from pydantic import ValidationError

from ad_api import config

def test_deve_carregar_configuracao_yaml_com_sucesso():

    from ad_api.config import ad_config

    assert "ad_fake" in ad_config.ads
    perfil = ad_config.ads["ad_fake"]

    assert perfil.servidor == "server_ad_fake"
    assert perfil.dominio == "fake.local"
    # Valida se a senha e a chave foram resgatadas direto do .env.test
    assert perfil.senha_service_account is not None
    assert perfil.senha_service_account != ""
    assert perfil.chave_api_hash is not None
    assert perfil.chave_api_hash != ""


def test_deve_lancar_file_not_found_ao_carregar_arquivo_inexistente(monkeypatch):

    with pytest.raises(FileNotFoundError):
        from ad_api.config import ad_config
        ad_config.carregar_de_yaml(caminho_arquivo="config-nao-existe.yml")

def test_deve_lancar_erro_de_validacao_se_faltar_campo_obrigatorio(tmp_path):
    yaml_incompleto = tmp_path / "config_incompleta.yaml"
    yaml_incompleto.write_text("""
ads:
  invalido:
    servidor: "apenas.o.servidor"
""")

    with pytest.raises(ValidationError):
        from ad_api.config import ad_config
        ad_config.carregar_de_yaml(str(yaml_incompleto))