FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

RUN mkdir /app
WORKDIR /app

COPY . .

ENV UV_LOCKED=true
ENV UV_NO_DEV=true

RUN uv sync

RUN uv run alembic upgrade ff71e85db90d

RUN echo "SECRET_KEY=$(openssl rand -hex 32)" > .env

EXPOSE 8000

ENTRYPOINT ["uv", "run",  "fastapi", "run", "main.py"]