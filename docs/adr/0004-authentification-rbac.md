# ADR-0004 — Auth session + Basic super-admin, RBAC code-défini

- **Statut** : Accepté
- **Date** : 2026-06-20

## Contexte

L'admin doit être protégé pour plusieurs profils (admin, opérateur, lecteur) et
rester scriptable (curl/CI). En Phase 1, il n'y a pas encore de multi-tenancy ni
de fournisseur d'identité externe.

## Décision

Deux mécanismes d'authentification (`infrastructure/http/auth.py`) :

1. **Cookie de session signé** (`SessionMiddleware`, `SESSION_SECRET`) — posé au
   login, transporte `username` + `role`. Chemin nominal du frontend.
2. **HTTP Basic** — fallback curl/scripts/CI, **super-admin uniquement**
   (env-keyed `ADMIN_USERNAME`/`ADMIN_PASSWORD`, comparaison
   `secrets.compare_digest`).

Le super-admin est **env-keyed et non stocké en DB** : la table `users` reste
purement « opérateurs », donc toute réponse CRUD est correcte par construction.

**RBAC code-défini** (`domain/role.py`) : matrice `Role → frozenset[Permission]`.
Les routes ne listent jamais les permissions : elles déclarent
`require_permission(Permission.X)` et le rôle du principal décide. Rôles :
`super_admin` (tout), `admin` (tout sauf `delete:user`), `operator`
(lecture + resend + export), `reader` (lecture).

## Conséquences

**Positives**
- Login sans énumération de comptes (même 401 user inconnu / mauvais mot de
  passe). `delete:user` réservé au super-admin.
- Matrice centralisée, testée de bout en bout (`test_rbac.py`).

**Négatives / suivi**
- La matrice est code-définie : en Phase 2, elle passera en DB (RBAC par tenant)
  ; les sites d'appel `require_permission` restent identiques.
- Pas d'OAuth/SSO en Phase 1 (prévu Phase 2).
