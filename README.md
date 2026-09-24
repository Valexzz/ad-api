

# ad-api `v0.1.0`

API desenvolvida em FastAPI para interagir com múltiplos ambientes Active Directory (AD) via LDAPS (porta 636). O objetivo da aplicação é prover endpoints REST para automação de tarefas de infraestrutura, como cadastro de usuários, reativação de contas e redefinição de senhas, permitindo a integração com portais internos ou sistemas externos (como portais de chamados).

## Tecnologias

* Python 3.12+
* FastAPI
* ldap3
* uv
* Pytest e Testcontainers
* Docker

## Arquitetura

O projeto utiliza uma estrutura baseada em Clean Architecture, separando as regras de negócio dos detalhes de infraestrutura, inspirada nos conceitos do livro *Cosmic Python*:

```text
src/ad_api/
├── adapters/      # Conexão LDAPS e repositório LDAP
├── api/           # Endpoints, schemas e dependências FastAPI
├── domain/        # Modelos, portas (interfaces) e regras de domínio
├── services/      # Orquestração das regras de negócio
└── main.py        # Inicialização da aplicação FastAPI

```

## Pré-requisitos

* Docker e Docker Compose
* Python 3.12+
* Gerenciador de pacotes `uv`
* ADs de destino com porta 636 aberta e conexão LDAPS (emitir certificado auto-assinado ou por uma CA)

---

## Configuração

A configuração da API é dividida em duas partes:

1. **`.env`**: Define parâmetros globais da aplicação e armazena os segredos (senhas e chaves de API) de cada AD.
2. **`config.yml`**: Centraliza os parâmetros estruturais de conexão e mapeia dinamicamente os nomes das variáveis de ambiente para cada Active Directory.

### 1. Arquivo `.env`

Crie um arquivo `.env` na raiz do projeto com as configurações globais e os segredos correspondentes aos perfis declarados no YAML:

```env
# Configurações Globais da API
DEBUG=false
LOG_LEVEL=INFO
AD_PADRAO=ad1
CAMINHO_ARQUIVO_YML=config.yml

# Segredos do Perfil ad1
AD_1_SENHA=SENHA_MUITO_SEGURA@123
AD_1_CHAVE_API=HASH_CHAVE_MUITO_SEGURA@123

# Segredos do Perfil ad2
AD_2_SENHA=OUTRA_SENHA_SEGURA@456
AD_2_CHAVE_API=OUTRO_HASH_SEGURO@456

```

#### Variáveis de Ambiente

| Variável | Descrição |
| --- | --- |
| `DEBUG` | Habilita o modo de depuração na aplicação (`true`/`false`). |
| `LOG_LEVEL` | Nível de detalhamento dos logs (`INFO`, `DEBUG`, `ERROR`). |
| `AD_PADRAO` | Nome do identificador do AD padrão a ser utilizado quando o parâmetro `?ad=` for omitido na requisição. |
| `CAMINHO_ARQUIVO_YML` | Caminho do arquivo YAML com a topologia dos Active Directories (padrão: `config.yml`). |
| `AD_*_SENHA` | Senha da conta de serviço apontada no `env_senha_service_account` do perfil correspondente. |
| `AD_*_CHAVE_API` | Hash da chave de API apontada no `env_chave_api_hash`, exigida no cabeçalho `x-api-key` para autorizar operações naquele perfil. |

---

### 2. Arquivo `config.yml`

Crie o arquivo `config.yml` na raiz do projeto listando os servidores e apontando para os nomes das variáveis de segredo definidas no `.env`:

```yaml
ads:
  ad1:
    servidor: "ldap.ad1.local"
    dominio: "ad1.local"
    dominio_netbios: "AD1"
    usuario_service_account: "svc_prefeitura@ad1.local"
    env_senha_service_account: "AD_1_SENHA"
    env_chave_api_hash: "AD_1_CHAVE_API"
    dn_base: "DC=ad1,DC=local"
    dn_padrao: "OU=Usuarios,DC=ad1,DC=local"
    timeout_ldap: 5
    politica_senha:
      tamanho_minimo: 8
      exigir_minuscula: true
      exigir_maiuscula: true
      exigir_numero: true
      exigir_caractere_especial: true
      chars_especiais: "!@#$%&*"
      dias_expiracao: 90

  ad2:
    servidor: "ldap.ad2.local"
    dominio: "ad2.local"
    dominio_netbios: "AD2"
    usuario_service_account: "svc_prefeitura@ad2.local"
    env_senha_service_account: "AD_2_SENHA"
    env_chave_api_hash: "AD_2_CHAVE_API"
    dn_base: "DC=ad2,DC=local"
    dn_padrao: "OU=Usuarios,DC=ad2,DC=local"
    politica_senha:
      tamanho_minimo: 10
      exigir_minuscula: false
      exigir_maiuscula: false
      exigir_numero: false
      exigir_caractere_especial: false
      chars_especiais: ""
      dias_expiracao: 60


```

#### Atributos de Cada Perfil de AD

| Atributo | Descrição |
| --- | --- |
| `servidor` | Hostname ou endereço IP do servidor Active Directory. |
| `dominio` | Nome FQDN do domínio DNS (ex: `ad1.local`). |
| `dominio_netbios` | Nome NetBIOS do domínio (ex: `AD1`). |
| `usuario_service_account` | Login/UPN da conta de serviço usada pela API para autenticar no AD. |
| `env_senha_service_account` | Nome da variável no `.env` que armazena a senha dessa conta de serviço. |
| `env_chave_api_hash` | Nome da variável no `.env` com a `x-api-key` autorizada a interagir com este AD. |
| `dn_base` | DN raiz para buscas e escopo de usuários (ex: `DC=ad1,DC=local`). |
| `dn_padrao` | Unidade Organizacional (OU) padrão onde os novos usuários serão criados. |
| `timeout_ldap` | *(Opcional)* Tempo limite de resposta da conexão em segundos (padrão: `5`). |
| `politica_senha` | *(Opcional)* Regras de validação de senha específicas aplicadas a este AD. |

---

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

---

## Endpoints e Roteamento

Todas as requisições exigem o envio do cabeçalho de autenticação `x-api-key`.

Para direcionar a operação a um Active Directory específico, utilize o query parameter opcional `?ad={identificador}` (ex: `?ad=ad1`, `?ad=ad2`). Caso o parâmetro seja omitido, a requisição é automaticamente roteada para o perfil configurado em `AD_PADRAO`.

* `GET /usuarios/{login}`: Consulta dados e status de um usuário.
* `POST /usuarios`: Cadastra um novo usuário no AD.
* `PATCH /usuarios/{login}/reativar`: Reativa uma conta inativa e permite movê-la de OU.
* `PATCH /usuarios/{login}/redefinir-senha`: Redefine a senha de um usuário existente.

---

## Licença

Distribuído sob a Licença MIT.

Feito por Victor Alexandre Borges Milhomem
