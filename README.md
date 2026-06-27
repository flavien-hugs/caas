# CaaS — Checkout-as-a-Service

[![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-009688)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-async-336791)](https://www.postgresql.org/)
[![SvelteKit](https://img.shields.io/badge/Frontend-SvelteKit%202%20%2F%20Svelte%205-FF3E00)](https://kit.svelte.dev/)
[![Tests](https://img.shields.io/badge/backend%20tests-84%20passing-success)]()

SaaS de checkout pour vendeurs digitaux d'Afrique francophone: plomberie
paiement mobile money (Kkiapay, CinetPay à venir), page builder pour les
landings, dashboard admin avec RBAC. Backend en architecture hexagonale
(ports & adapters), frontend SvelteKit. Prêt pour le multi-tenancy en phase 2.

Ce dépôt est un **monorepo** :

| Dossier | Rôle | Stack |
|---|---|---|
| [`backend/`](backend/) | API + use cases + adapters | FastAPI · SQLModel · Postgres · Redis · Celery · Typer |
| [`frontend/`](frontend/) | Landings publiques + page builder + dashboard admin | SvelteKit 2 · Svelte 5 · Tailwind 4 · Vite 6 |

## Sommaire

- [Démarrage rapide](#démarrage-rapide)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [API](#api)
- [Authentification & RBAC](#authentification--rbac)
- [CLI](#cli)
- [Migrations](#migrations)
- [Tests](#tests)
- [Sécurité](#sécurité)
- [Roadmap](#roadmap)

## Démarrage rapide

### Backend (Docker)

```bash
cd backend
cp .env.example .env
make run                                                    # api + db + redis + adminer
docker compose -f compose.override.yaml --profile migrate run --rm migrate
open http://localhost:8080/health
open http://localhost:8080/caas/docs                        # OpenAPI (si HIDE_DOCS=false)
```

> `make run` enveloppe `docker compose --env-file=.env -f compose.override.yaml up -d`.
> Le service `migrate` est sous le profil `migrate` (opt-in), il ne démarre pas tout seul.

### Frontend (Node)

```bash
cd frontend
cp .env.example .env                                        # pointe BACKEND_BASE vers l'API
pnpm install
pnpm gen:api                                                # génère le client typé depuis l'OpenAPI
pnpm dev                                                    # http://localhost:5173
```

## Architecture

### Stack

| Couche | Backend | Frontend |
|---|---|---|
| HTTP | FastAPI 0.128+ | SvelteKit 2 (adapter-node), SSR |
| Langage | Python 3.12+ | TypeScript 5 / Svelte 5 (runes) |
| Données | SQLModel (Postgres asyncpg / SQLite aiosqlite en test) | client `openapi-fetch` typé via `openapi-typescript` |
| Migrations | Alembic | — |
| UI | — | Tailwind 4, bits-ui, lucide-svelte, superforms + zod |
| Cache / broker | Redis 7 | — |
| Tâches | Celery (broker Redis) — facultatif | — |
| CLI | Typer | — |
| Build | Poetry + Docker multi-stage | Vite 6 + pnpm |

### Backend — découpage hexagonal

```
backend/src/
├── domain/                       # entités pures, zéro dep framework
│   ├── purchase.py               # aggregate root immutable
│   ├── money.py                  # value object (amount entier, currency)
│   ├── product.py                # Product + EmailConfig + DeliveryMethod
│   ├── page.py                   # Page builder (blocks, slug, statut publié)
│   ├── user.py / role.py / password.py  # comptes admin, RBAC, hash mot de passe
│   ├── feedback.py / payment_ref.py / provider_amount.py
│   └── formatting.py             # format_price + format_datetime (FR)
│
├── application/                  # use cases + ports (Protocols PEP 544)
│   ├── ports/                    # PaymentProviderPort, *RepositoryPort, NotificationPort, CachePort
│   ├── use_cases/
│   │   ├── initiate_purchase.py
│   │   ├── confirm_payment.py    # amount-check + security_error + delivery
│   │   ├── record_beacon.py / lookup_purchase.py
│   │   ├── reconcile_pending.py  # délègue à ConfirmPayment
│   │   ├── dashboard.py          # ListTransactions, Stats, Revenue
│   │   ├── admin_actions.py      # Resend, AdminConfirm, Export xlsx
│   │   ├── pages.py              # CRUD + publish/unpublish des pages
│   │   ├── user_management.py    # CRUD comptes admin
│   │   └── feedback.py
│   └── dashboard_filters.py
│
└── infrastructure/               # adapters concrets
    ├── http/
    │   ├── app.py                # FastAPI + SessionMiddleware + SlowAPI
    │   ├── deps.py               # composition root manuelle
    │   ├── auth.py / credentials.py  # session cookie + Basic (super-admin)
    │   ├── rbac.py               # require_permission(Permission)
    │   ├── limiter.py            # slowapi
    │   └── routes/               # health, purchase, callback, beacon, feedback,
    │                             # auth, public_pages, admin_dashboard,
    │                             # admin_actions, admin_pages, admin_users
    ├── persistence/              # SQLModel + repos
    ├── payment/                  # KkiapayProvider
    ├── notification/             # SmtpEmailNotification + NoOp + catalog templates
    ├── cache/                    # CachePort + impl Redis
    ├── tasks/                    # Celery
    └── config/settings.py        # Pydantic Settings env-keyed
```

**Principe** : le domain ne sait pas qu'il existe une DB, le HTTP ne sait pas
qu'il existe Kkiapay. La composition root manuelle est dans
[`backend/src/infrastructure/http/deps.py`](backend/src/infrastructure/http/deps.py)
— un seul endroit où le graphe de dépendances est visible.

### Frontend — SvelteKit

```
frontend/src/
├── routes/
│   ├── +page.server.ts           # accueil
│   ├── p/[slug]/                 # landing publique rendue depuis les blocks du builder
│   ├── login/ · logout/          # auth (session côté backend)
│   └── (admin)/admin/            # zone admin (guard via /auth/me)
│       ├── +page.svelte          # dashboard (stats, revenue)
│       ├── transactions/         # liste + filtres + export.xlsx
│       ├── pages/                # page builder (list, new, [id])
│       └── users/                # gestion des comptes (list, new, [id])
└── lib/
    ├── api/client.ts             # openapi-fetch typé (schema.gen.ts)
    ├── blocks/                   # Hero, FAQ, FeatureGrid, CTAButton, PaymentForm, RichText, …
    ├── builder/                  # Canvas, Inspector, BlockLibrary, store (drag & drop)
    ├── server/session.ts         # propagation du cookie de session aux fetchs SSR
    ├── components/ui/ · permissions.ts · utils.ts
```

Les fetchs vers le backend se font côté serveur (`BACKEND_BASE`) ; le
navigateur ne voit que le serveur Node de SvelteKit.

## Configuration

> **Configuration runtime.** SMTP, agrégateurs de paiement (Kkiapay, CinetPay) et
> SMS sont éditables **à chaud** depuis l'admin (`/admin/settings`, permission
> `manage:settings`). La valeur effective est résolue **DB > env > défaut**
> ([`resolver.py`](backend/src/application/config/resolver.py)) : les variables
> ci-dessous restent les valeurs par défaut/fallback. Les secrets saisis en admin
> sont **chiffrés au repos** (Fernet, `CONFIG_ENCRYPTION_KEY`) et jamais réaffichés.

### Backend — [`backend/.env.example`](backend/.env.example)

```env
APP_NAME=caas
ENVIRONMENT=dev                              # dev | staging | production
HIDE_DOCS=false                              # true masque /caas/docs en prod
LOG_LEVEL=INFO

# DB (Postgres en prod, SQLite en test via DATABASE_URL override)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=caas
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}

# Redis + Celery (broker/result sur DB Redis séparées)
REDIS_URL=redis://redis:6379/1
REDIS_NAMESPACE=v2
CELERY_BROKER_URL=redis://redis:6379/2
CELERY_RESULT_BACKEND=redis://redis:6379/3

# Paiement (overridable via /admin/settings → general/kkiapay/cinetpay)
PAYMENT_PROVIDER=kkiapay                     # kkiapay | cinetpay
KKIAPAY_PUBLIC_KEY=
KKIAPAY_PRIVATE_KEY=
KKIAPAY_SECRET_KEY=
KKIAPAY_SANDBOX=true
CINETPAY_SITE_ID=
CINETPAY_API_KEY=
CINETPAY_SANDBOX=true

# SMS (scaffold ; overridable via /admin/settings → sms)
SMS_PROVIDER_URL=
SMS_API_KEY=
SMS_SENDER=

# Chiffrement des secrets de config en DB (Fernet). REQUIS en production.
# Générer: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
CONFIG_ENCRYPTION_KEY=

# Catalogue produits (phase 1, in-memory, env-keyed)
FRAUDE_WEBINAIRE_PRICE=10000
FRAUDE_WHATSAPP_GROUP_LINK=

# Email (vide → NoOpNotification ; overridable via /admin/settings → smtp)
SMTP_HOST=
SMTP_PORT=587
SMTP_FROM=no-reply@caas.com

# Réconciliation (sync-pending-loop)
SYNC_INTERVAL_SECONDS=900

# Auth : super-admin env-keyed + cookie de session signé
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin
SESSION_SECRET=                              # obligatoire en prod (cookie signé)

# Rate limiting (/purchases)
PURCHASES_RATE_LIMIT=3/minute

SITE_URL=http://localhost:8080

# Ports exposés par compose.override.yaml
API_PORT=8080
POSTGRES_PORT=5432
REDIS_PORT=6379
ADMINER_PORT=8081
```

### Frontend — [`frontend/.env.example`](frontend/.env.example)

```env
BACKEND_BASE=http://localhost:8080           # fetchs SSR
PUBLIC_API_BASE=http://localhost:8080        # utilisé par `pnpm gen:api`
```

## API

OpenAPI live sur `http://localhost:8080/caas/docs` une fois l'API démarrée
(si `HIDE_DOCS=false`). Les routes sont montées à la racine (pas de préfixe global).

### Publiques

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/health` | Santé + version |
| POST | `/purchases` | Initier un achat (server-authoritative price, rate-limité) |
| GET | `/purchases/{id}` | Projection publique (pages success/error SSR) |
| POST | `/payment/beacon` | sendBeacon : enregistre le `transactionId` provider (204) |
| GET | `/payment/callback` | Confirme avec contrôle de montant + delivery |
| POST | `/feedbacks` | Avis client |
| GET | `/feedbacks/recent` | Avis 4★+ pour les landings |
| GET | `/pages/{slug}` | Page publiée (rendu de la landing par le frontend) |

### Authentification

| Méthode | Route | Rôle |
|---|---|---|
| POST | `/auth/login` | Valide les identifiants, pose le cookie de session |
| POST | `/auth/logout` | Détruit la session (204) |
| GET | `/auth/me` | `{username, role}` courant — guard SSR du frontend |

### Admin (session cookie **ou** Basic super-admin, permission RBAC requise)

| Méthode | Route | Permission |
|---|---|---|
| GET | `/admin/transactions` | `read:transactions` |
| GET | `/admin/dashboard/stats` | `read:stats` |
| GET | `/admin/dashboard/revenue?days=30` | `read:stats` |
| POST | `/admin/transactions/{id}/resend` | `resend:delivery` |
| POST | `/admin/transactions/{id}/sync` | `sync:payment` (avec amount-check) |
| GET | `/admin/transactions/export.xlsx` | `export:transactions` |
| GET / POST | `/admin/pages` | `manage:pages` |
| GET / PATCH / DELETE | `/admin/pages/{id}` | `manage:pages` |
| POST | `/admin/pages/{id}/publish` · `/unpublish` | `manage:pages` |
| GET | `/admin/users` | `list:users` |
| POST | `/admin/users` | `create:user` |
| GET | `/admin/users/{id}` | `read:user` |
| PATCH | `/admin/users/{id}` | `update:user` |
| DELETE | `/admin/users/{id}` | `delete:user` (**super-admin uniquement**) |
| GET | `/admin/settings` · `/admin/settings/{section}` | `manage:settings` |
| PUT | `/admin/settings/{section}` | `manage:settings` (secrets write-only) |
| POST | `/admin/settings/smtp/test` · `/admin/settings/sms/test` | `manage:settings` |

## Authentification & RBAC

Deux mécanismes d'auth, définis dans
[`backend/src/infrastructure/http/auth.py`](backend/src/infrastructure/http/auth.py) :

1. **Cookie de session signé** (`SessionMiddleware`, `SESSION_SECRET`) — posé au
   login, transporte `username` + `role`. C'est le chemin nominal pour le frontend.
2. **HTTP Basic** — fallback pour curl/scripts/CI, **super-admin uniquement**
   (env-keyed `ADMIN_USERNAME`/`ADMIN_PASSWORD`, `secrets.compare_digest`).

Les routes n'énumèrent jamais les permissions : elles déclarent
`require_permission(Permission.X)` et le rôle du principal décide. La matrice
rôle → permissions est code-définie dans
[`backend/src/domain/role.py`](backend/src/domain/role.py) (passera en DB en phase 2) :

| Rôle | Transactions | Stats | Export / Resend | Users | Pages | Config |
|---|---|---|---|---|---|---|
| `super_admin` | ✅ | ✅ | ✅ | ✅ (+ delete) | ✅ | ✅ |
| `admin` | ✅ | ✅ | ✅ | ✅ (sauf delete) | ✅ | ✅ |
| `operator` | lecture | ✅ | ✅ | — | — | — |
| `reader` | lecture | ✅ | — | — | — | — |

## CLI

Toutes les commandes via Typer (depuis `backend/`) :

```bash
poetry run caas runserver --host 0.0.0.0 --reload        # API dev (auto-reload)
poetry run caas sync-pending --book-id lutte-contre-fraude   # réconciliation one-shot (cron)
poetry run caas sync-pending-loop -i 900                  # boucle longue (service compose)
```

## Migrations

Le service `migrate` du compose est opt-in (profil `migrate`) :

```bash
cd backend

# Appliquer toutes les migrations
docker compose -f compose.override.yaml --profile migrate run --rm migrate

# Sur une DB partagée déjà à jour (cohabitation avec des tables externes)
docker compose -f compose.override.yaml --profile migrate run --rm migrate \
  poetry run alembic stamp head

# Créer une migration
poetry run alembic revision --autogenerate -m "describe change"
```

Raccourcis Makefile équivalents : `make db-migrate`, `make db-migration msg="…"`,
`make db-status`, `make db-history`, `make db-reset` (dev only).

La chaîne Alembic est verrouillée en CI par
[`backend/tests/integration/test_alembic_migrations.py`](backend/tests/integration/test_alembic_migrations.py)
(upgrade head + round-trip insert via SQLModel).

## Tests

### Backend — 84 tests (`pytest-asyncio` mode auto)

```bash
cd backend
make test                                                # pytest + coverage
PYTHONPATH=src python -m pytest tests/unit/ -q           # use cases + fakes (ni DB, ni HTTP)
PYTHONPATH=src python -m pytest tests/integration/ -q    # app réelle + SQLite + provider mocké
```

- **Unitaires** : invariants métier (amount-check, idempotency, security_error,
  delivery selon `DeliveryMethod`).
- **Intégration** : FastAPI réel + SQLite in-memory + `KkiapayProvider.verify_payment`
  monkeypatché. Couvre routes paiement, feedback, dashboard, **auth, RBAC, pages,
  users, rate-limit** et migrations Alembic.

### Frontend

```bash
cd frontend
pnpm check                                                # svelte-check (types)
pnpm test                                                 # vitest (unitaire)
pnpm test:e2e                                             # playwright (e2e)
pnpm lint                                                 # prettier + eslint
```

## Sécurité

### Garanties

- **Prix serveur autoritaire** sur `/purchases` — le `client_amount` n'est jamais utilisé pour la persistance.
- **Amount-check obligatoire** sur le callback et l'admin sync. Une transaction marquée `security_error` n'est jamais ressuscitée.
- **RBAC** code-défini, vérifié par `require_permission` à la frontière HTTP ; `delete:user` réservé au super-admin.
- **Session signée** (`SESSION_SECRET`) + **Basic super-admin** en `compare_digest` (timing-constant). Login sans énumération de comptes (même 401 user inconnu / mauvais mot de passe).
- **Rate limiting** slowapi sur `/purchases` (`PURCHASES_RATE_LIMIT`, défaut `3/minute`).
- **Sanitization** des champs free-form via Pydantic validators (strip caractères de contrôle, longueur bornée).
- **Money en entiers** (XOF, 1 = 1 FCFA) — pas d'arithmétique flottante.
- **Idempotency** : la delivery email est protégée par `payment_metadata.email_sent`.
- **Secrets de config chiffrés au repos** (Fernet) et write-only via l'API (jamais réaffichés).
- **Markdown sanitisé** (DOMPurify) avant rendu `{@html}` sur les pages publiques.

### À venir

- OAuth/SSO pour les admins multi-tenant (phase 2).
- Intégration gateway CinetPay complète (adapter scaffold en place).

## Roadmap

### Phase 1 (en cours)

- ✅ Backend hexagonal : domain + use cases + adapters Kkiapay/SMTP/Redis.
- ✅ Flow paiement bout-en-bout (purchase → callback → beacon → success/error).
- ✅ Réconciliation périodique (sync-worker).
- ✅ Dashboard admin (stats, filtres, liste, resend, sync, export xlsx).
- ✅ Auth session + RBAC (rôles, permissions, gestion des comptes admin).
- ✅ Page builder (blocks + canvas drag-and-drop, pages publiques par slug).
- ✅ Champs multi-textes en **Markdown** (marked + DOMPurify).
- ✅ **Configuration runtime** (SMTP, agrégateurs, SMS) éditable en admin, secrets chiffrés.
- ✅ Rate-limiter `/purchases`.
- ✅ Feedback (soumission + listing 4★+).
- ✅ Frontend SvelteKit (landings + checkout + dashboard + builder) — palette ambre.
- ⏳ CinetPay & SMS : config + scaffold en place, intégration gateway à finaliser.

### Phase 2

- Multi-tenancy (table `tenants`, scoping des queries, matrice RBAC en DB).
- Onboarding self-serve (signup, configuration Kkiapay par tenant).
- Facturation du SaaS lui-même.
- Webhooks sortants pour les tenants.

## Auteur

- **Flavien HUGS** — `flavienhugs@pm.me`
- Version `0.1.0`
