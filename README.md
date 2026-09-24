
# ad-api `v0.1.0`

API desenvolvida em FastAPI para interagir com o Active Directory (AD) via LDAPS (porta 636). O objetivo da aplicação é prover endpoints REST para automação de tarefas de infraestrutura, como cadastro de usuários, reativação de contas e redefinição de senhas, permitindo a integração com portais internos ou sistemas externos (como portais de chamados).

## Tecnologias

* Python 3.12+
* FastAPI
* ldap3
* uv
* Pytest e Testcontainers
* Docker

## Arquitetura

O projeto utiliza uma estrutura baseada em Clean Architecture, separando as regras de negócio dos detalhes de infraestrutura. Eu tentei me basear na arquitetura apresentada pelo livro Cosmic Python:

```text
src/ad_api/
├── adapters/      # Conexão e repositório LDAP
├── api/           # Endpoints, schemas e dependências da API
├── domain/        # Modelos, portas (interfaces) e regras de domínio
├── services/      # Orquestração das regras de negócio
└── main.py        # Inicialização da aplicação FastAPI
```

## Pré-requisitos

* Docker e Docker Compose
* Python 3.12+
* Gerenciador de pacotes `uv`

## Configuração

Crie um arquivo `.env` na raiz do projeto com base nas variáveis abaixo:

```env
SERVIDOR_AD=ldap.empresa.local
DOMINIO_AD=empresa.local
DOMAIN_AD=EMPRESA
USUARIO_SERVICE_ACCOUNT_AD=svc_api@empresa.local
SENHA_USUARIO_SERVICE_ACCOUNT_AD=sua_senha
DN_BASE_AD=DC=empresa,DC=local
DN_PADRAO_AD=OU=Users,DC=empresa,DC=local
TIMEOUT_LDAP=5

CHAVE_API=sua-chave-api

TAMANHO_MINIMO_SENHA_AD=8
EXIGIR_MINUSCULA_SENHA_AD=true
EXIGIR_MAIUSCULA_SENHA_AD=true
EXIGIR_NUMERO_SENHA_AD=true
EXIGIR_CARACTERE_ESPECIAL_SENHA_AD=true
CHARS_ESPECIAIS_SENHA_AD=!@#$%&*
DIAS_EXPIRACAO_SENHA_AD=90

DEBUG=false
LOG_LEVEL=INFO
```

Descrição das Variáveis de Ambiente

| Variável                             | Descrição                                                                                                                                                                       |
|:-------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `SERVIDOR_AD`                        | Endereço IP ou hostname do servidor Active Directory.                                                                                                                           |
| `DOMINIO_AD`                         | Nome do domínio DNS do AD (ex: `empresa.local`).                                                                                                                                |
| `DOMAIN_AD`                          | Nome NetBIOS do domínio (ex: `EMPRESA`).                                                                                                                                        |
| `USUARIO_SERVICE_ACCOUNT_AD`         | Conta de serviço utilizada pela API para autenticar e executar ações no AD. Garanta que ela possui permissões para recuperar, cadastrar, reativar e redefinir senha de usuários |
| `SENHA_USUARIO_SERVICE_ACCOUNT_AD`   | Senha da conta de serviço.                                                                                                                                                      |
| `DN_BASE_AD`                         | Distinguished Name raiz da árvore do diretório (ex: `DC=empresa,DC=local`).                                                                                                     |
| `DN_PADRAO_AD`                       | Unidade Organizacional (OU) padrão onde os novos usuários serão criados.                                                                                                        |
| `TIMEOUT_LDAP`                       | Tempo limite (em segundos) para interromper requisições travadas ao AD.                                                                                                         |
| `CHAVE_API_HASH`                     | Hash da Chave secreta exigida no cabeçalho (`x-api-key`) para consumir os endpoints.                                                                                            |
| `TAMANHO_MINIMO_SENHA_AD`            | Número mínimo de caracteres exigidos na criação/redefinição de senha.                                                                                                           |
| `EXIGIR_MINUSCULA_SENHA_AD`          | Define se a senha obrigatoriamente precisa conter letras minúsculas (`true`/`false`).                                                                                           |
| `EXIGIR_MAIUSCULA_SENHA_AD`          | Define se a senha obrigatoriamente precisa conter letras maiúsculas (`true`/`false`).                                                                                           |
| `EXIGIR_NUMERO_SENHA_AD`             | Define se a senha obrigatoriamente precisa conter números (`true`/`false`).                                                                                                     |
| `EXIGIR_CARACTERE_ESPECIAL_SENHA_AD` | Define se a senha obrigatoriamente precisa conter caracteres especiais (`true`/`false`).                                                                                        |
| `CHARS_ESPECIAIS_SENHA_AD`           | Conjunto de caracteres especiais aceitos pela política de validação.                                                                                                            |
| `DIAS_EXPIRACAO_SENHA_AD`            | Quantidade máxima de dias considerada antes de marcar a senha como expirada.                                                                                                    |
| `DEBUG`                              | Habilita o modo de depuração na aplicação (`true`/`false`).                                                                                                                     |
| `LOG_LEVEL`                          | Nível de detalhamento dos logs gerados (ex: `INFO`, `DEBUG`, `ERROR`).                                                                                                          |



## Como Executar

### 1. Executando a API via Docker

```bash
docker compose up --build
```
A API roda na porta `8000`. A documentação interativa fica disponível em `http://localhost:8000/docs`.

### 2. Ambiente de Testes (Samba AD)

Para subir o container local do Samba AD utilizado nos testes de integração:

```bash
docker compose -f docker-compose-test.yml up -d
```

## Executando os Testes

Para rodar a suíte de testes utilizando o `uv`:

```bash
uv sync
pytest
```

## Endpoints

Todas as requisições exigem o envio do cabeçalho `x-api-key`.

* `GET /usuarios/{login}`: Consulta dados e status de um usuário.
* `POST /usuarios`: Cadastra um novo usuário no AD.
* `PATCH /usuarios/{login}/reativar`: Reativa uma conta inativa e permite movê-la de OU.
* `PATCH /usuarios/{login}/redefinir-senha`: Redefine a senha de um usuário.

## Licença

Distribuído sob a Licença MIT.

Feito por Victor Alexandre Borges Milhomem