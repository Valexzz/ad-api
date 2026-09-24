from typing import Optional

from fastapi import Security, HTTPException, Query, Depends
from fastapi.security import APIKeyHeader
from starlette import status

from ad_api.adapters.conn import LdapClient
from ad_api.adapters.usuario_ldap_repository import UsuarioLdapRepository
from ad_api.config import settings, PerfilAD, ad_config
from ad_api.domain.model import PoliticaSenha
from ad_api.errors import InfraError, ChaveApiInvalidaError, ADNaoEncontrado
from ad_api.services.usuario_service import UsuarioService
import hmac

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def get_perfil_ad_autenticado(
        ad: Optional[str] = Query(
            default=None,
            description="Identificador do AD (ex: ad1, ad2). Se omitido, usa o padrão.",
        ),
        api_key: str = Security(api_key_header),
) -> PerfilAD:
    if not api_key:
        raise ChaveApiInvalidaError("Chave de API ausente")

    nome_ad = ad or settings.ad_padrao

    perfil = ad_config.ads.get(nome_ad)
    if not perfil:
        raise ADNaoEncontrado(
            f"Perfil de AD '{nome_ad}' não encontrado",
        )

    if not hmac.compare_digest(api_key, perfil.chave_api_hash):
        raise ChaveApiInvalidaError(f"Chave de API inválida para o AD '{nome_ad}'")

    return perfil

def get_usuario_service(
        perfil: PerfilAD = Depends(get_perfil_ad_autenticado)
) -> UsuarioService:
    ldap_client = LdapClient(
        servidor=perfil.servidor,
        usuario=perfil.usuario_service_account,
        senha=perfil.senha_service_account,
        timeout=perfil.timeout_ldap,
    )

    repository = UsuarioLdapRepository(
        ldap_client=ldap_client,
        dn_base=perfil.dn_base,
        dn_padrao=perfil.dn_padrao,
        dominio=perfil.dominio,
        dias_expiracao_senha_ad=perfil.politica_senha.dias_expiracao,
    )

    # Converte o modelo Pydantic do perfil para a entidade esperada pelo serviço
    politica = PoliticaSenha(
        tamanho_minimo=perfil.politica_senha.tamanho_minimo,
        exigir_numero=perfil.politica_senha.exigir_numero,
        exigir_minuscula=perfil.politica_senha.exigir_minuscula,
        exigir_maiuscula=perfil.politica_senha.exigir_maiuscula,
        exigir_caractere_especial=perfil.politica_senha.exigir_caractere_especial,
        chars_especiais=perfil.politica_senha.chars_especiais,
    )

    return UsuarioService(
        usuario_repository=repository,
        politica_senha=politica,
    )

