from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    servidor_ad: str
    dominio_ad: str
    usuario_service_account_ad: str
    senha_usuario_service_account_ad: str
    dn_base_ad  : str
    timeout_ldap: int = 5

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()