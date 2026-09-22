# src/ad_api/api/exception_handlers.py
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

from ad_api.config import settings

logger = logging.getLogger("ad_api")

def usuario_nao_encontrado_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.warning(f"[USUARIO_NAO_ENCONTRADO] - O usuário solicitado não foi localizado no AD. Detalhes: {str(exc)}")
    return JSONResponse(
        status_code=404,
        content={
            "codigo": "USUARIO_NAO_ENCONTRADO",
            "mensagem": str(exc),
        },
    )

def senha_invalida_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.warning(f"[SENHA_INVALIDA] - Tentativa de operação com senha inválida ou fora dos padrões. Detalhes: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={
            "codigo": "SENHA_INVALIDA",
            "mensagem": str(exc)
        }
    )

def usuario_ja_existe_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.warning(f"[USUARIO_JA_EXISTE] - Tentativa de cadastro de usuário que já existe no AD. Detalhes: {str(exc)}")
    return JSONResponse(
        status_code=409,
        content={
            "codigo": "USUARIO_JA_EXISTE",
            "mensagem": str(exc)
        }
    )


def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Captura qualquer outro erro de regra de negócio/domínio (regra violada)."""
    logger.warning(f"[ERRO_REGRA_DE_NEGOCIO] - Violação de regra de negócio detectada. Detalhes: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={
            "codigo": "ERRO_REGRA_DE_NEGOCIO",
            "mensagem": str(exc),
        },
    )


def infra_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Captura falhas de infraestrutura (timeout LDAP, dados corrompidos no AD, conexão)."""
    logger.error(f"[ERRO_COMUNICACAO_AD] - Falha de infraestrutura com o AD. Detalhes técnicos: {str(exc)}", exc_info=True)

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

def chave_api_invalida_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.warning(f"[CHAVE_API_INVALIDA] - Tentativa de acesso à API com chave inválida ou ausente. Detalhes: {str(exc)}")
    return JSONResponse(
        status_code=401,
        content={
            "codigo": "CHAVE_API_INVALIDA",
            "mensagem": str(exc)
        }
    )