# Architecture Decision Records (ADR)

Décisions d'architecture du projet CaaS, au format léger MADR (Contexte →
Décision → Conséquences). Les ADR sont **immuables** : on ne réécrit pas une
décision passée, on en ajoute une nouvelle qui la **supersède**.

| #    | Décision | Statut |
|------|----------|--------|
| [0001](0001-architecture-hexagonale.md) | Architecture hexagonale (ports & adapters) | Accepté |
| [0002](0002-cohabitation-strangler-db-partagee.md) | Cohabitation strangler avec le legacy sur DB partagée | Accepté |
| [0003](0003-configuration-runtime-chiffree.md) | Configuration runtime en DB (fallback env) + secrets chiffrés | Accepté |
| [0004](0004-authentification-rbac.md) | Auth session + Basic super-admin, RBAC code-défini | Accepté |
| [0005](0005-page-builder-blocs-json.md) | Page builder : blocs JSON opaques, schéma piloté par le frontend | Accepté |
| [0006](0006-frontend-sveltekit-bff.md) | Frontend SvelteKit en BFF, env runtime | Accepté |
| [0007](0007-monorepo-ci-images.md) | Monorepo + images Docker séparées + CI | Accepté |
| [0008](0008-securite-paiement.md) | Sécurité paiement : prix serveur, montants entiers, amount-check | Accepté |
| [0009](0009-reconciliation-confirmpayment.md) | Réconciliation via un ConfirmPayment partagé (HTTP + CLI) | Accepté |
| [0010](0010-lint-backend-ruff.md) | Lint backend : migration vers Ruff (précise ADR-0007) | Accepté |

## Format

```
# ADR-NNNN — Titre
- Statut : Proposé | Accepté | Déprécié | Supersédé par ADR-XXXX
- Date : YYYY-MM-DD
## Contexte
## Décision
## Conséquences (positives / négatives / suivi)
```
