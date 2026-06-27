# ADR-0003 — Configuration runtime en DB (fallback env) + secrets chiffrés

- **Statut** : Accepté
- **Date** : 2026-06-26

## Contexte

SMTP, agrégateurs de paiement et SMS étaient **env-keyed** : changer un
paramètre imposait un redéploiement. Les vendeurs/admins doivent pouvoir
configurer ces intégrations **à chaud**. Mais ces réglages contiennent des
**secrets** (mot de passe SMTP, clés privées Kkiapay, clé API SMS) qui ne
doivent ni fuiter ni être réaffichés.

## Décision

- Une table `app_settings` stocke un blob JSON **par section**
  (`general`, `smtp`, `kkiapay`, `cinetpay`, `sms`).
- Un **résolveur** (`application/config/resolver.py`) calcule la config
  effective : **DB > env > défaut**, par champ. Un secret vide en DB retombe sur
  l'env (jamais d'écrasement involontaire).
- Chaque section a un schéma Pydantic déclarant ses **champs secrets**
  (`SECRET_FIELDS`). Cette déclaration unique pilote : le masquage en lecture,
  le chiffrement à l'écriture, et la sémantique « laisser vide = conserver ».
- Les secrets sont **chiffrés au repos** avec **Fernet**
  (`CONFIG_ENCRYPTION_KEY` ; en dev, dérivée de `SESSION_SECRET` avec warning ;
  **requise en production**). L'API ne renvoie jamais un secret, seulement un
  booléen « configuré ».
- La composition root expose une dépendance async `resolved_config()` ;
  paiement/notif/SMS lisent la config résolue (et plus `settings` directement).

## Conséquences

**Positives**
- Configuration sans redéploiement ; secrets protégés au repos et write-only.
- Fallback env → aucune régression pour les déploiements existants.
- Sélection d'agrégateur runtime (`general.payment_provider`).

**Négatives / suivi**
- Lecture config **par requête** (1 requête `all()`) ; cache Redis possible si
  besoin (via le `CachePort` existant), avec invalidation à l'update.
- **Gestion de la clé** : sauvegarde + stratégie de rotation à définir (perte de
  `CONFIG_ENCRYPTION_KEY` = secrets illisibles).
