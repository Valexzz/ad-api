# src/ad_api/api/exception_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse

from ad_api.config import settings
from ad_api.errors import (
    DomainError,
    InfraError,
    UsuarioNaoEncontradoError,
)


def usuario_nao_encontrado_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "codigo": "USUARIO_NAO_ENCONTRADO",
            "mensagem": str(exc),
        },
    )

def senha_invalida_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "codigo": "SENHA_INVALIDA",
            "mensagem": str(exc)
        }
    )

def usuario_ja_existe_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "codigo": "USUARIO_JA_EXISTE",
            "mensagem": str(exc)
        }
    )


def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Captura qualquer outro erro de regra de negócio/domínio (regra violada)."""
    return JSONResponse(
        status_code=400,
        content={
            "codigo": "ERRO_REGRA_DE_NEGOCIO",
            "mensagem": str(exc),
        },
    )


def infra_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Captura falhas de infraestrutura (timeout LDAP, dados corrompidos no AD, conexão)."""
    resposta = {
        "codigo": "ERRO_COMUNICACAO_AD",
        "mensagem": "Serviço temporariamente indisponível devido a falha de comunicação com o diretório.",
    }
    if getattr(settings, "debug", False):
        resposta["detalhe"] = str(exc)

    return JSONResponse(
        status_code=502,
        content=resposta,
    )

