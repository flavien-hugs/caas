# PRD — CaaS (Checkout-as-a-Service)

- **Statut**: vivant (Phase 1 en cours)
- **Dernière révision** : 2026-06-27
- **Documents liés** : [PRODUCT.md](PRODUCT.md) (stratégie/design), [DESIGN.md](DESIGN.md) (système visuel), [adr/](adr/) (décisions d'architecture)

---

## 1. Contexte & problème

Les vendeurs digitaux d'Afrique francophone encaissent majoritairement par
**mobile money** (Kkiapay, CinetPay…) mais manquent d'un outil simple pour:
créer une page de vente, encaisser, suivre l'état des paiements et livrer le
produit. Les solutions existantes sont soit trop génériques (SaaS occidentaux
sans mobile money), soit du bricolage (liens de paiement + tableur).

**CaaS** fournit la plomberie de checkout: une page builder pour les landings de
vente, un dashboard d'exploitation des transactions, et une configuration des
intégrations (paiement, email, SMS) éditable sans redéploiement.

## 2. Objectifs & non-objectifs

### Objectifs (Phase 1)
- O1. Encaisser un paiement mobile money de bout en bout (initiation → widget →
  callback → confirmation → livraison), avec **prix autoritaire serveur**.
- O2. Construire et publier des **landing pages de vente** sans développeur.
- O3. **Exploiter** les transactions : recherche/filtre, réconciliation,
  relance de livraison, export.
- O4. **Configurer à chaud** SMTP / agrégateurs / SMS depuis l'admin, secrets
  chiffrés, sans redéploiement.
- O5. **RBAC** : plusieurs rôles d'exploitation (admin, opérateur, lecteur).

### Non-objectifs (Phase 1)
- Multi-tenancy / self-serve onboarding (Phase 2).
- Facturation du SaaS lui-même (Phase 2).
- Intégration gateway **CinetPay complète** (scaffold seulement).
- Canal **SMS branché** sur un flux métier (scaffold + test seulement).
- Application mobile native.

## 3. Utilisateurs

| Persona | Contexte | Besoin principal |
|---|---|---|
| **Vendeur digital** (propriétaire) | Mobile, pressé, peu technique | Encaisser, suivre ses ventes, publier une page |
| **Opérateur / support** | Desktop, back-office | Réconcilier, relancer une livraison, lire |
| **Admin technique** | Desktop | Configurer agrégateurs/SMTP/SMS, gérer les comptes |
| **Client final (acheteur)** | Mobile, paiement ponctuel | Payer vite et en confiance |

## 4. Parcours clés

1. **Achat** : l'acheteur ouvre `/p/{slug}`, remplit le formulaire de paiement,
   est redirigé vers le widget du provider, revient via callback → confirmation
   avec **contrôle de montant** → livraison (email/lien).
2. **Création de page** : l'admin ouvre le builder (modale), compose des blocs
   (Hero, FAQ, formulaire de paiement…), publie sur `/p/{slug}`.
3. **Exploitation** : l'opérateur filtre les transactions, relance une
   livraison, ou force une vérification (sync) avec contrôle de montant.
4. **Configuration** : l'admin renseigne SMTP/Kkiapay/CinetPay/SMS, teste
   l'envoi, change l'agrégateur actif — à chaud.

## 5. Périmètre fonctionnel

Priorités : **P0** = indispensable Phase 1, **P1** = important, **P2** = nice-to-have.

### Paiement & livraison
- P0 — Initier un achat (`POST /purchases`), prix calculé **serveur**.
- P0 — Callback de confirmation avec **amount-check** + idempotence livraison.
- P0 — Beacon (`transactionId` provider) ; lookup public (pages succès/erreur).
- P0 — Réconciliation périodique (worker) + manuelle (admin), même logique.
- P1 — Relance de livraison (email) depuis l'admin.

### Page builder & landings
- P0 — CRUD pages + publication ; rendu public `/p/{slug}`.
- P0 — Blocs : Hero, FeatureGrid, FAQ, RichText, CTA, Image, Section, Spacer,
  Divider, **Formulaire de paiement** (apparence configurable).
- P0 — Champs multi-textes en **Markdown** (sanitisé).
- P1 — Inspecteur de style par bloc (fond/padding de section, alignement titre).

### Dashboard & exploitation
- P0 — Liste transactions paginée + filtres (recherche/statut/produit/date).
- P0 — Statuts lisibles (payée/en attente/échouée/anomalie) libellé + icône.
- P1 — Stats (revenus, compteurs) + export XLSX.

### Configuration & comptes
- P0 — Config runtime DB > env (SMTP, Kkiapay, CinetPay, SMS, général),
  secrets **chiffrés**, write-only via l'API.
- P0 — Tests d'envoi SMTP / SMS depuis l'admin.
- P0 — RBAC (super_admin / admin / operator / reader) + gestion des comptes.
- P0 — Auth : session cookie signée + Basic super-admin (fallback CLI/CI).

## 6. Exigences non-fonctionnelles

- **Sécurité** : prix serveur-autoritaire ; amount-check sur callback & sync ;
  secrets de config chiffrés au repos (Fernet) et jamais réaffichés ; RBAC
  appliqué à la frontière HTTP ; rate-limit `/purchases` ; sanitization des
  champs libres ; `secrets.compare_digest` pour le Basic. Voir [ADR-0008](adr/0008-securite-paiement.md).
- **Accessibilité** : cible WCAG 2.1 AA (contraste ≥ 4.5:1, clavier, focus
  visibles, `prefers-reduced-motion`, statut jamais porté par la couleur seule).
- **Performance** : SSR ; lecture config par requête (1 requête, cache Redis en
  option) ; pas de layout shift ; images distantes.
- **Internationalisation** : FR par défaut ; montants `XOF` en **entiers**.
- **Disponibilité / exploitation** : Docker, healthcheck `/health`, logs JSON,
  migrations Alembic verrouillées en CI.
- **Compatibilité** : Python 3.12+ (CI 3.14) ; Node 22 ; Postgres ; Redis.

## 7. Architecture (résumé)

- **Backend** hexagonal (ports & adapters) : `domain` pur → `application`
  (use cases + ports) → `infrastructure` (FastAPI, persistence SQLModel,
  adapters paiement/notif/SMS, config). Voir [ADR-0001](adr/0001-architecture-hexagonale.md).
- **Cohabitation strangler** avec le legacy `app/` sur la même DB Postgres.
  Voir [ADR-0002](adr/0002-cohabitation-strangler-db-partagee.md).
- **Frontend** SvelteKit (adapter-node) en BFF : les fetchs backend se font
  côté serveur via `BACKEND_BASE`. Voir [ADR-0006](adr/0006-frontend-sveltekit-bff.md).
- **Monorepo** `backend/` + `frontend/`, deux images Docker, CI GitHub Actions.
  Voir [ADR-0007](adr/0007-monorepo-ci-images.md).

## 8. Modèle de données (tables CaaS)

`transactions` (achats), `users` (comptes opérateurs ; super-admin env-keyed,
non stocké), `pages` (blocs JSON opaques), `feedbacks`, `app_settings`
(config runtime, secrets chiffrés dans le blob JSON). Évolution **additive**
uniquement (colonnes nullables) tant que la cohabitation legacy dure.

## 9. Métriques de succès

- Taux de confirmation paiement (callback SUCCESS / initiations).
- Délai initiation → confirmation.
- Nombre de transactions `security_error` (doit rester proche de 0).
- Pages publiées / vendeur actif.
- Temps de configuration d'un nouvel agrégateur (objectif : sans redéploiement).

## 10. Hors périmètre & roadmap (Phase 2)

- Multi-tenancy (table `tenants`, scoping des requêtes, RBAC en DB).
- Onboarding self-serve (signup, config Kkiapay par tenant).
- Facturation du SaaS, webhooks sortants par tenant.
- Intégration gateway **CinetPay** complète ; **SMS** branché (delivery/alertes).
- OAuth/SSO admin.

## 11. Risques & dépendances

- **Dépendance providers** (Kkiapay/CinetPay) : disponibilité, format de
  réponse. Mitigation : adapter isolé derrière `PaymentProviderPort`.
- **CinetPay stub** : `verify_payment` renvoie `PENDING` — **ne pas activer en
  prod** avant l'intégration réelle (risque : aucune confirmation).
- **Cohabitation DB** : tout changement de schéma doit rester additif.
- **Clé de chiffrement** (`CONFIG_ENCRYPTION_KEY`) : sa perte rend les secrets
  config illisibles ; prévoir sauvegarde + rotation.

## 12. Glossaire

- **book_id** : identifiant produit dans le catalogue.
- **amount-check** : vérification que le montant payé = prix serveur.
- **security_error** : transaction dont le montant ne correspond pas ; jamais
  ressuscitée par les re-vérifications.
- **strangler** : migration progressive en cohabitation avec le legacy.
- **BFF** : Backend-for-Frontend (le serveur SvelteKit relaie vers l'API).
