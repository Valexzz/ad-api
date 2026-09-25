from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from ad_api.domain.model import StatusUsuario


class UsuarioResponse(BaseModel):
    login: str = Field(
        ...,
        description="Identificador de logon único da conta no Active Directory (sAMAccountName).",
        examples=["victor.milhomem"],
    )
    nome_completo: str = Field(
        ...,
        description="Nome de exibição completo do colaborador (displayName/cn).",
        examples=["Victor Alexandre Borges Milhomem"],
    )
    matricula: Optional[str] = Field(
        default=None,
        description="Identificação funcional ou matrícula do colaborador mapeada no atributo employeeID.",
        examples=["12345"],
    )
    status: StatusUsuario = Field(
        ...,
        description="Estado atual da conta no Active Directory derivado do userAccountControl (Ativo ou Inativo).",
        examples=[StatusUsuario.ATIVO],
    )
    status_senha: Optional[str] = Field(
        default=None,
        description="Situação de validade da senha calculada via pwdLastSet (ATIVA, EXPIRADA ou PARA_REDEFINIR).",
        examples=["ATIVA"],
    )

    model_config = ConfigDict(from_attributes=True)


class UsuarioRequest(BaseModel):
    login: str = Field(
        ...,
        description="Login único desejado para a conta (sAMAccountName e prefixo do userPrincipalName).",
        examples=["novo.usuario"],
    )
    senha: str = Field(
        ...,
        description="Senha inicial da conta. Deve obrigatoriamente cumprir a política de complexidade configurada para o AD de destino.",
        examples=["SenhaSegura@2026"],
    )
    trocar_senha: bool = Field(
        default=False,
        description="Quando True, define o pwdLastSet como 0, obrigando o usuário a alterar a credencial no próximo logon.",
    )
    status: StatusUsuario = Field(
        default=StatusUsuario.ATIVO,
        description="Status operacional inicial da conta (Ativo cria como conta normal; Inativo aplica a flag ACCOUNTDISABLE no userAccountControl).",
        examples=[StatusUsuario.ATIVO],
    )
    nome_completo: Optional[str] = Field(
        default=None,
        description="Nome completo para exibição no diretório (displayName/CN). Se omitido, pode ser derivado da junção de primeiro_nome e sobrenome.",
        examples=["Novo Usuario da Silva"],
    )
    primeiro_nome: Optional[str] = Field(
        default=None,
        description="Primeiro nome do usuário persistido no atributo givenName.",
        examples=["Novo"],
    )
    sobrenome: Optional[str] = Field(
        default=None,
        description="Sobrenome do usuário persistido no atributo sn.",
        examples=["Usuario da Silva"],
    )
    matricula: Optional[str] = Field(
        default=None,
        description="Código funcional persistido no atributo employeeID do Active Directory.",
        examples=["99887"],
    )
    container_dn: Optional[str] = Field(
        default=None,
        description="Distinguished Name (DN) da Unidade Organizacional (OU) de destino. Se omitido, será utilizado o dn_padrao configurado no perfil do AD.",
        examples=["OU=Usuarios,DC=empresa,DC=local"],
    )


class UsuarioReativarRequest(BaseModel):
    senha: str = Field(
        ...,
        description="Nova senha atribuída durante a reativação da conta, validada contra a política de complexidade do AD.",
        examples=["NovaSenha@2026"],
    )
    trocar_senha: bool = Field(
        default=False,
        description="Quando True, força a redefinição de senha logo no primeiro acesso após a reativação da conta.",
    )
    mover_para_container_padrao: bool = Field(
        default=False,
        description="Quando True, indica a intenção de transferir a conta para a OU padrão configurada no perfil do AD.",
    )
    container_dn: Optional[str] = Field(
        default=None,
        description="Distinguished Name (DN) de uma OU customizada para onde a conta deve ser movida ao ser reativada. Sobrescreve a OU padrão caso informado.",
        examples=["OU=Ativos,DC=empresa,DC=local"],
    )


class UsuarioRedefinirSenhaRequest(BaseModel):
    senha: str = Field(
        ...,
        description="Nova senha administrativa a ser aplicada diretamente na conta do usuário, sujeita à validação da política de senhas.",
        examples=["Redefinida@2026"],
    )
    trocar_senha: bool = Field(
        default=False,
        description="Quando True, marca o atributo pwdLastSet como 0 para exigir nova troca pelo próprio usuário no próximo acesso.",
    )


class ModeloErro(BaseModel):
    codigo: str
    mensagem: str