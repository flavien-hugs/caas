# Inclusion des fichiers d'environnement s'ils existent
ifneq (,$(wildcard .env))
    include .env
    export
endif

# Définition des fichiers Docker Compose
COMPOSE_FILES := -f compose.override.yaml

# Objectif par défaut
.DEFAULT_GOAL := help

# Couleurs pour l'affichage de l'aide
COLOR_TARGET := \033[36m
COLOR_DESC := \033[0m

# Cibles phony
.PHONY: help run restart stop logs down prune volume pre-commit

# Affiche l'aide avec les descriptions des cibles
help: ## Afficher cette aide
	@echo "Cibles disponibles :"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(COLOR_TARGET)%-30s$(COLOR_DESC)%s\n", $$1, $$2}'

# Installation
.PHONY: install
install: ## Installer les dépendances et configurer pre-commit
	poetry install
	poetry run pre-commit install

# Database Migrations (Alembic)
.PHONY: db-check
db-check: ## Vérifier la connexion à la base de données
	@poetry run python -c "from app.core.database import engine; import asyncio; asyncio.run(engine.connect()); print('✓ Database connection successful')"

.PHONY: db-status
db-status: ## Afficher l'état de la base et migrations en attente
	@echo "Current database version"
	@poetry run alembic current
	@echo "Migration history"
	@poetry run alembic history

.PHONY: db-init
db-init:  ## Init database
	poetry run alembic init

.PHONY: db-migration
db-migration: ## Créer une migration automatique (usage: make migration msg="description")
	@if [ -z "$(msg)" ]; then echo "Usage: make db-migration msg=\"description\""; exit 1; fi
	poetry run alembic revision --autogenerate -m "$(msg)"

.PHONY: db-migrate
db-migrate: ## Appliquer toutes les migrations en attente
	poetry run alembic upgrade head

.PHONY: db-downgrade
db-downgrade: ## Annuler la dernière migration
	poetry run alembic downgrade -1

.PHONY: db-history
db-history: ## Afficher l'historique complet des migrations
	poetry run alembic history

.PHONY: db-current
db-current: ## Afficher la version actuelle de la base
	poetry run alembic current

.PHONY: db-reset
db-reset: ## [DEV ONLY] Reset complet de la base de données
	@echo "WARNING: This will drop all tables and recreate them!"
	@read -p "Are you sure? [y/N] " -n 1 -r; echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		poetry run alembic downgrade base && poetry run alembic upgrade head && echo "Database reset complete"; \
	else \
		echo "Cancelled"; \
	fi

# Testing
.PHONY: test
test: ## Exécuter les tests avec coverage
	poetry run pytest --cov --cov-report term --cov-report xml:coverage.xml tests --durations=10

.PHONY: coverage
coverage: ## Afficher le rapport de coverage
	poetry run coverage report -m

# Code Quality
.PHONY: lint
lint: ## Lancer le linting (ruff)
	poetry run ruff check src tests
	poetry run ruff format --check src tests

.PHONY: format
format: ## Formater le code automatiquement (ruff)
	poetry run ruff check --fix src tests
	poetry run ruff format src tests

.PHONY: clean
clean: ## Nettoyer les fichiers générés
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache htmlcov coverage.xml

# Exécute les conteneurs
run: ## Démarrer les conteneurs
	COMPOSE_BAKE=true docker compose --env-file=.env $(COMPOSE_FILES) up -d

# Redémarre un ou plusieurs conteneurs
restart: ## Redémarrer un ou plusieurs conteneurs (utiliser SERVICE=<service>)
	docker compose $(COMPOSE_FILES) restart $(SERVICE)

# Arrête un ou tous les conteneurs
stop: ## Arrêter un ou tous les conteneurs (utiliser SERVICE=<service>)
	docker compose $(COMPOSE_FILES) stop $(SERVICE)

# Affiche les logs des conteneurs
logs: ## Voir les logs des conteneurs (utiliser SERVICE=<service>)
	docker compose $(COMPOSE_FILES) logs -f $(SERVICE)

# Supprime les conteneurs, réseaux, etc.
down: ## Arrêter les services et supprimer les conteneurs, réseaux, volumes
	docker compose $(COMPOSE_FILES) down

# Nettoie les ressources Docker non utilisées
prune: ## Nettoyer les images, conteneurs et réseaux non utilisés
	docker system prune

# Nettoie les volumes Docker non utilisés
volume: ## Nettoyer les volumes Docker non utilisés
	docker volume prune
