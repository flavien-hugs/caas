# ADR-0008 — Sécurité paiement : prix serveur, montants entiers, amount-check

- **Statut** : Accepté
- **Date** : 2026-06-17

## Contexte

Le paiement est la surface la plus sensible : un client malveillant ne doit pas
pouvoir payer moins que le prix, ni faire confirmer une transaction au mauvais
montant. Les montants en XOF n'ont pas de décimales, mais l'arithmétique
flottante reste une source de bugs.

## Décision

- **Prix serveur-autoritaire** : `POST /purchases` ignore tout montant fourni
  par le client (`client_amount` n'est jamais utilisé pour la persistance) ; le
  prix vient du catalogue côté serveur.
- **Amount-check obligatoire** : à la confirmation (callback **et** sync admin),
  le montant rapporté par le provider est comparé au prix attendu. En cas
  d'écart, la transaction passe en **`security_error`** et n'est **jamais
  ressuscitée** par les re-vérifications ultérieures.
- **Money en entiers** (`domain/money.py`, XOF : 1 = 1 FCFA) — aucune
  arithmétique flottante sur les montants.
- **Idempotence livraison** : l'envoi email est protégé par
  `payment_metadata.email_sent` (pas de double livraison).
- **Garde-fous transverses** : rate-limit `slowapi` sur `/purchases`
  (`PURCHASES_RATE_LIMIT`, défaut `3/minute`) ; sanitization des champs libres
  via validators Pydantic à la frontière HTTP ; `secrets.compare_digest` pour le
  Basic super-admin.

## Conséquences

**Positives**
- Impossible de payer moins que le prix ou de confirmer un mauvais montant.
- `security_error` est un signal d'anomalie exploitable (dashboard).

**Négatives / suivi**
- L'amount-check dépend de la fiabilité du champ `amount` renvoyé par le
  provider ; l'extraction est isolée (`extract_provider_amount`) pour s'adapter
  par provider.
- Une transaction légitime mal rapportée tombera en `security_error` et
  nécessitera une intervention manuelle (par construction, c'est le but).
