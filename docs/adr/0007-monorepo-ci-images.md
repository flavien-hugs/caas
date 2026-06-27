# ADR-0007 — Monorepo + images Docker séparées + CI

- **Statut** : Accepté
- **Date** : 2026-06-26

## Contexte

Backend (Python/FastAPI) et frontend (SvelteKit/Node) évoluent ensemble mais se
déploient séparément. Il faut un dépôt unique cohérent et une CI qui ne
reconstruit que ce qui change, avec des images indépendantes.

## Décision

- **Monorepo** : `backend/` et `frontend/` à la racine, plus `docs/` et
  `.github/`.
- **Deux images Docker** publiées sur **GHCR** :
  `ghcr.io/<owner>/<repo>-backend` et `-frontend` (nom dérivé du dépôt,
  minuscule ; auth via `GITHUB_TOKEN` + `packages: write`).
- **CI GitHub Actions** ([.github/workflows/docker-publish.yml](../../.github/workflows/docker-publish.yml)) :
  - Détection de changements (`dorny/paths-filter`) → ne teste/builde que la
    partie modifiée.
  - `test-backend` : Poetry (cache), **lint pre-commit** (black/isort/flake8,
    scopé aux fichiers backend), pytest + coverage.
  - `check-frontend` : pnpm (cache), `pnpm lint` (prettier + eslint), `pnpm check`.
  - `build-*` : buildx + cache GHA (scope par image), tag dérivé de la branche
    (`main→latest`, `develop→dev`, `preprod`, `rc/x→x_RC`).
  - `concurrency` : annule les runs PR obsolètes.

## Conséquences

**Positives**
- Une seule source de vérité ; PRs atomiques cross-stack.
- CI rapide (path filtering + caches) ; images indépendantes et déployables
  séparément.

**Négatives / suivi**
- Le lint a été ajouté **après coup** : un premier passage normalise du
  formatage pré-existant (backend black, frontend prettier).
- `seed-isort-config` (pre-commit) est ancien/déprécié — à remplacer ou retirer.
- L'image frontend lit `BACKEND_BASE` au runtime (cf. ADR-0006).
