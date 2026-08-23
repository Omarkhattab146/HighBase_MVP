FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.8 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uv","run","--no-sync","uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
