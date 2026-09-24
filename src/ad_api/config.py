import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    debug: bool = False
    log_level: str = "INFO"
    ad_padrao: str = "padrao"
    caminho_arquivo_yml: str = "config.yml"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

class PoliticaSenhaConfig(BaseModel):
    tamanho_minimo: int = 8
    exigir_minuscula: bool = True
    exigir_maiuscula: bool = True
    exigir_numero: bool = True
    exigir_caractere_especial: bool = True
    chars_especiais: str = r"!@#$%&*"
    dias_expiracao: int = 90


class PerfilAD(BaseModel):
    servidor: str
    dominio: str
    dominio_netbios: str
    usuario_service_account: str
    senha_service_account: str
    env_senha_service_account: str

    chave_api_hash: str
    env_chave_api_hash: str

    dn_base: str
    dn_padrao: str
    timeout_ldap: int = 5
    politica_senha: PoliticaSenhaConfig = Field(default_factory=PoliticaSenhaConfig)


class AdConfig(BaseModel):
    ads: dict[str, PerfilAD]

    @classmethod
    def carregar_de_yaml(cls, caminho_arquivo: str) -> "AdConfig":
        path = Path(caminho_arquivo)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de configuração {caminho_arquivo} não encontrado.")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            print(data)

        for nome_ad, perfil in data.get("ads", {}).items():
            env_senha = perfil.get("env_senha_service_account")
            perfil["senha_service_account"] = os.getenv(env_senha, "") if env_senha else ""

            env_chave = perfil.get("env_chave_api_hash")
            perfil["chave_api_hash"] = os.getenv(env_chave, "") if env_chave else ""

        return cls(**data)

ad_config = AdConfig.carregar_de_yaml(getattr(settings, "caminho_arquivo_yml", "config.yml"))