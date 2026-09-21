from fastapi import FastAPI

from ad_api.api.endpoints import router
from ad_api.api.exception_handlers import (
    domain_error_handler,
    infra_error_handler,
    usuario_nao_encontrado_handler,
)
from ad_api.errors import DomainError, InfraError, UsuarioNaoEncontradoError

app = FastAPI(title="API para comunicação com AD")

# Registra os handlers de erro (ordem: específicos primeiro, depois genéricos)
app.add_exception_handler(UsuarioNaoEncontradoError, usuario_nao_encontrado_handler)
app.add_exception_handler(DomainError, domain_error_handler)
app.add_exception_handler(InfraError, infra_error_handler)

# Registra as rotas
app.include_router(router)