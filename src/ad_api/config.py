from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    servidor_ad: str
    dominio_ad: str
    domain_ad: str
    usuario_service_account_ad: str
    senha_usuario_service_account_ad: str
    dn_base_ad: str
    timeout_ldap: int = 5

    dn_padrao_ad: str

    debug: bool = False

    tamanho_minimo_senha_ad: int = 8
    exigir_minuscula_senha_ad: bool = True
    exigir_maiuscula_senha_ad: bool = True
    exigir_numero_senha_ad: bool = True
    exigir_caractere_especial_senha_ad: bool = True
    chars_especiais_senha_ad: str = r"!@#$%&*"
    dias_expiracao_senha_ad: int = 90

    chave_api: str = "chave-api-padrao"

    log_level: str = "INFO"
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()