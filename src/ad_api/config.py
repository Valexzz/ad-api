from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    servidor_ad: str
    dominio_ad: str
    usuario_service_account_ad: str
    senha_ad: str
    dn_base_ad  : str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()