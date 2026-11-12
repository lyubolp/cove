FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

RUN mkdir /app
WORKDIR /app

COPY . .

RUN uv lock

ENV UV_LOCKED=true
ENV UV_NO_DEV=true

RUN uv sync

RUN echo "SECRET_KEY=$(openssl rand -hex 32)" > .env

ENV COVE_DB_PATH=/data/database.db
VOLUME /data

EXPOSE 8000

ENTRYPOINT ["sh", "-c", "uv run alembic upgrade head && uv run fastapi run main.py"]
