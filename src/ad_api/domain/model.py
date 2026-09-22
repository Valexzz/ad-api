from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ad_api.errors import DomainError, SenhaInvalidaError


class StatusUsuario(str, Enum):
    ATIVO = "Ativo"
    INATIVO = "Inativo"


@dataclass
class Usuario:
    login: str
    primeiro_nome: str
    sobrenome: str
    status: StatusUsuario
    matricula: Optional[str] = None

    @property
    def nome_completo(self) -> str:
        return f"{self.primeiro_nome} {self.sobrenome}".strip()

    @classmethod
    def criar(
            cls,
            login: str,
            nome_completo: Optional[str] = None,
            primeiro_nome: Optional[str] = None,
            sobrenome: Optional[str] = None,
            matricula: Optional[str] = None,
            status: StatusUsuario = StatusUsuario.ATIVO,
    ) -> "Usuario":
        """
        Factory method para instanciação com base na RN07:
        Aceita (primeiro_nome e sobrenome) OU nome_completo.
        """
        login_limpo = login.strip() if login else ""
        if not login_limpo:
            raise DomainError("O login do usuário é obrigatório.")

        if nome_completo and nome_completo.strip():
            partes = nome_completo.strip().split(maxsplit=1)
            p_nome = partes[0]
            s_nome = partes[1] if len(partes) > 1 else ""

        elif primeiro_nome is not None:
            p_nome = primeiro_nome.strip()
            s_nome = (sobrenome or "").strip()
            if not p_nome:
                raise DomainError("O primeiro nome não pode ser vazio.")

        else:
            raise DomainError(
                "É necessário informar 'nome_completo' ou 'primeiro_nome' para criar o usuário."
            )

        return cls(
            login=login_limpo,
            primeiro_nome=p_nome,
            sobrenome=s_nome,
            status=status,
            matricula=matricula.strip() if matricula else None,
        )


class PoliticaSenha:
    def __init__(
            self,
            tamanho_minimo: int = 8,
            exigir_minuscula: bool = True,
            exigir_maiuscula: bool = True,
            exigir_numero: bool = True,
            exigir_caractere_especial: bool = True,
            chars_especiais: str = r"!@#$%&*",
    ):
        self.tamanho_minimo = tamanho_minimo
        self.exigir_minuscula = exigir_minuscula
        self.exigir_maiuscula = exigir_maiuscula
        self.exigir_numero = exigir_numero
        self.exigir_caractere_especial = exigir_caractere_especial
        self.chars_especiais = chars_especiais

    def validar(self, senha: str) -> None:
        erros: list[str] = []

        if not senha or len(senha) < self.tamanho_minimo:
            erros.append(f"ter no mínimo {self.tamanho_minimo} caracteres")

        if self.exigir_minuscula and not any(c.islower() for c in (senha or "")):
            erros.append("conter ao menos uma letra minúscula")

        if self.exigir_maiuscula and not any(c.isupper() for c in (senha or "")):
            erros.append("conter ao menos uma letra maiúscula")

        if self.exigir_numero and not any(c.isdigit() for c in (senha or "")):
            erros.append("conter ao menos um número")

        if self.exigir_caractere_especial and not any(c in self.chars_especiais for c in (senha or "")):
            erros.append(f"conter ao menos um caractere especial ({self.chars_especiais})")

        if erros:
            mensagem = "A senha não atende aos requisitos: " + "; ".join(erros) + "."
            raise SenhaInvalidaError(mensagem)