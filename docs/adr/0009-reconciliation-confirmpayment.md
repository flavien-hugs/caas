# ADR-0009 — Réconciliation via un ConfirmPayment partagé (HTTP + CLI)

- **Statut** : Accepté
- **Date** : 2026-06-17

## Contexte

Une transaction peut rester `PENDING` (widget abandonné, callback perdu, réseau
mobile instable). Il faut un mécanisme qui revérifie périodiquement les
paiements en attente auprès du provider — sans dupliquer la logique de
confirmation (vérification + amount-check + livraison) déjà utilisée par le
callback HTTP.

## Décision

- La confirmation est un **seul use case** : `ConfirmPayment` (vérification
  provider + amount-check + livraison + idempotence).
- La **réconciliation** (`ReconcilePending`) **délègue** à `ConfirmPayment` ligne
  par ligne : une seule source de vérité pour la logique de confirmation,
  partagée entre :
  - le **callback HTTP** (`GET /payment/callback`),
  - le **worker / CLI** (`caas sync-pending`, `caas sync-pending-loop`),
  - l'**action admin** (sync manuel d'une transaction).
- Le CLI/worker construit ses use cases via la composition root
  (`build_resolved_config()` + `build_reconcile_pending(cfg)`), donc il lit la
  **config runtime** (provider actif, credentials) comme le HTTP.
- Le worker tourne en service compose dédié ; l'intervalle est réglable
  (`SYNC_INTERVAL_SECONDS`). Une itération en erreur ne tue pas la boucle.

## Conséquences

**Positives**
- Pas de divergence possible entre confirmation « live » et réconciliation.
- Les paiements abandonnés/perdus finissent confirmés (ou marqués) sans
  intervention.

**Négatives / suivi**
- La réconciliation interroge le provider pour chaque ligne éligible :
  fréquence et volumétrie à surveiller (filtrage par `book_id`, statut).
- Dépend de l'idempotence de la livraison (cf. ADR-0008) pour éviter les doubles
  envois entre callback et sync.
