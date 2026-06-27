FROM ghcr.io/flavien-hugs/python-poetry-base:latest

WORKDIR /app

ENV POETRY_VIRTUALENVS_CREATE=false \
    APP_ENTRYPOINT=src.infrastructure.http.app:create_app

USER root

COPY pyproject.toml poetry.lock* ./

RUN poetry install --no-root --no-interaction

USER appuser

COPY --chown=appuser:appuser . .
