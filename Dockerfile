FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copia os arquivos de dependência primeiro para aproveitar cache de camadas
COPY pyproject.toml uv.lock ./

# Instala apenas as dependências de produção sem instalar o projeto ainda
RUN uv sync --frozen --no-install-project --no-dev

# Copia o código-fonte
COPY README.md ./
COPY src/ ./src/

# Instala o próprio projeto no ambiente virtual
RUN uv sync --frozen --no-dev

# ==========================================
# Imagem final de execução
# ==========================================
FROM python:3.12-slim-bookworm

WORKDIR /app

# Usuário não-root por segurança
RUN useradd -m -u 1000 appuser

# Copia o ambiente virtual e a aplicação preparados na etapa builder
COPY --from=builder /app /app

# Ativa o PATH do ambiente virtual do uv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

CMD ["uvicorn", "ad_api.main:app", "--host", "0.0.0.0", "--port", "8000"]