# ADR-0010 — Lint backend : migration vers Ruff

- **Statut** : Accepté
- **Date** : 2026-06-27
- **Précise** : le volet outillage de lint de [ADR-0007](0007-monorepo-ci-images.md)

## Contexte

Le lint backend reposait sur **black 24.3.0 + isort (`seed-isort-config`) +
flake8 (+bugbear)**, exécutés via pre-commit. Problèmes :

- **Pin black fragile** : la version locale (26.x) divergeait de celle de la CI
  (24.3.0), provoquant des allers-retours de formatage.
- **`seed-isort-config`** est **déprécié** et ne triait pas réellement les
  imports (aucun hook isort actif → ordre d'import non appliqué en CI).
- Trois outils + leurs configs à maintenir, plus lents qu'une solution unique.

## Décision

Remplacer black + isort + flake8 par **Ruff** (linter + formateur) :

- Config unique dans `pyproject.toml` `[tool.ruff]` : `line-length = 128`,
  `target-version = "py312"`, `extend-exclude = ["alembic/versions"]`.
- `[tool.ruff.lint]` : `select = ["E", "F", "W", "I", "B"]` (le **I** active
  enfin le tri d'imports) ; `ignore = ["E402", "B006", "B008", "B010"]`
  (notamment **B008** = `Depends()` FastAPI en valeur par défaut).
- pre-commit via `astral-sh/ruff-pre-commit` **v0.15.20** : hooks `ruff`
  (`--fix`) + `ruff-format`. Les hooks d'hygiène (`pre-commit-hooks`) restent.
- `Makefile` : `make lint` → `ruff check` + `ruff format --check` ;
  `make format` → `ruff check --fix` + `ruff format`.
- Suppression de `.isort.cfg`, `[tool.black]`, `[tool.flake8]`, et des hooks
  black/isort/flake8.

La CI (job `test-backend`) exécute toujours **pre-commit** scopé aux fichiers
backend : aucune modification du workflow, l'outillage sous-jacent change seul.

## Conséquences

**Positives**
- Un seul outil (Rust, rapide), une seule config ; fin du pin black douloureux.
- Tri d'imports réellement appliqué (`I`), auto-corrigé.
- Reformatage minimal à la bascule (ruff-format ≈ black ; 1 fichier reformaté).

**Négatives / suivi**
- Codes non implémentés par Ruff retirés des ignores (`E704`, `B903`, `B907`,
  `W503`) — sans impact (le formateur gère, les stubs `...` ne sont pas flaggés).
- **B904** (`raise ... from`) n'était pas réellement appliqué avant. Les 27
  sites de mapping d'erreurs HTTP ont été corrigés (`raise ... from None`, ou
  `from e`/`from exc` quand l'exception est référencée) et la règle est
  **désormais active** (B904 hors de l'ignore).
