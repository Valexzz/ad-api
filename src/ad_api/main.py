import logging

from fastapi import FastAPI

from ad_api.api.endpoints import router
from ad_api.api.exception_handlers import (
    domain_error_handler,
    infra_error_handler,
    usuario_nao_encontrado_handler, senha_invalida_handler, usuario_ja_existe_handler, chave_api_invalida_handler,
    ad_nao_encontrado_handler,
)
from ad_api.config import settings
from ad_api.errors import DomainError, InfraError, UsuarioNaoEncontradoError, SenhaInvalidaError, UsuarioSemLoginError, \
    UsuarioJaExisteError, ChaveApiInvalidaError, ADNaoEncontrado

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("ad_api")
app = FastAPI(

    title="AD API",
    version="0.1.0",
    description="API para gerenciamento de identidades no Active Directory",
)

# Registra os handlers de erro (ordem: específicos primeiro, depois genéricos)
app.add_exception_handler(UsuarioNaoEncontradoError, usuario_nao_encontrado_handler)
app.add_exception_handler(SenhaInvalidaError, senha_invalida_handler)
app.add_exception_handler(UsuarioJaExisteError, usuario_ja_existe_handler)
app.add_exception_handler(ChaveApiInvalidaError, chave_api_invalida_handler)
app.add_exception_handler(ADNaoEncontrado, ad_nao_encontrado_handler)
app.add_exception_handler(DomainError, domain_error_handler)
app.add_exception_handler(InfraError, infra_error_handler)

# Registra as rotas
app.include_router(router)