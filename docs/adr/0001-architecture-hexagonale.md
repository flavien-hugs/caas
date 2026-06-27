# ADR-0001 — Architecture hexagonale (ports & adapters)

- **Statut** : Accepté
- **Date** : 2026-06-16

## Contexte

CaaS dépend de services externes volatils (agrégateurs de paiement, SMTP, SMS,
DB) et doit pouvoir en changer (Kkiapay → CinetPay), être testé sans réseau, et
évoluer vers le multi-tenancy. Un découpage en couches qui isole le métier des
détails techniques est nécessaire.

## Décision

Structurer le backend en trois couches :

- `domain/` — entités et value objects **purs** (zéro import framework) :
  `Purchase`, `Money`, `Product`, `Page`, `User`, `Role`, `ConfigSection`…
- `application/` — **use cases** + **ports** (Protocols PEP 544) :
  `PaymentProviderPort`, `*RepositoryPort`, `NotificationPort`,
  `SmsNotificationPort`, `SettingsRepositoryPort`. Les use cases ne dépendent
  que des ports.
- `infrastructure/` — **adapters** concrets : FastAPI (HTTP), SQLModel
  (persistence), Kkiapay/CinetPay (payment), SMTP/SMS (notification), config.

La **composition root** est manuelle et centralisée dans
`infrastructure/http/deps.py` (pas de conteneur DI) : un seul endroit où le
graphe de dépendances est lisible.

## Conséquences

**Positives**
- Le `domain` ne sait pas qu'il existe une DB ; le HTTP ne sait pas qu'il existe
  Kkiapay. Changer d'adaptateur n'impacte pas les use cases.
- Tests unitaires sans DB/HTTP (use cases + fakes) ; tests d'intégration avec
  SQLite in-memory + provider mocké.
- Prêt pour la Phase 2 (multi-tenancy) : les ports restent identiques.

**Négatives / suivi**
- Plus de boilerplate (ports + adapters) que pour un CRUD direct.
- La composition root manuelle grossit ; acceptable tant qu'elle reste lisible.
