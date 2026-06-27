FROM ghcr.io/flavien-hugs/python-poetry-base:latest

WORKDIR /app

ENV POETRY_VIRTUALENVS_CREATE=false \
    APP_ENTRYPOINT=src.infrastructure.http.app:create_app

USER root

COPY pyproject.toml poetry.lock ./

# Le projet utilise le layout PEP 621 ([project]) et un lock-version 2.1, qui
# exigent Poetry >= 2.1. L'image de base peut embarquer une version plus
# ancienne (qui rejetterait le lock / ne lirait pas [project]) : on épingle une
# version compatible, puis on installe via `python -m poetry` pour être sûr
# d'utiliser celle-ci.
RUN pip install --no-cache-dir --upgrade "poetry>=2.1,<3"

# Image runtime : seules les deps principales (pas dev/test = ruff, pytest…).
RUN python -m poetry install --no-root --only main --no-interaction

USER appuser

COPY --chown=appuser:appuser . .
