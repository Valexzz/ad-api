from datetime import datetime, timezone
from typing import Optional, Any


def obter_valor_atributo_ad(registro: Any, nome_atributo: str, valor_padrao: Optional[str] = None) -> Optional[str]:
    if nome_atributo not in registro:
        return valor_padrao

    atributo = registro[nome_atributo]
    if atributo is None or atributo.value is None:
        return valor_padrao

    valor = atributo.value
    if isinstance(valor, (list, tuple)):
        valor = valor[0] if valor else valor_padrao

    return str(valor) if valor is not None else valor_padrao

def obter_datetime_ad_nunca() -> datetime:
    return datetime(1601, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def datetime_para_ad_filetime(dt: datetime) -> int:
    """Converte um datetime do Python para o formato inteiro FILETIME do Active Directory."""
    epoch_windows = datetime(1601, 1, 1, tzinfo=timezone.utc)
    # Diferença em segundos multiplicada por 10 milhões (intervalos de 100 nanossegundos)
    return int((dt - epoch_windows).total_seconds() * 10000000)