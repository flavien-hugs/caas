# Product

## Register

product

## Users

Vendeurs digitaux d'Afrique francophone (propriétaires de petites activités) qui
encaissent par mobile money et vendent des produits/services en ligne. Contexte
d'usage souvent mobile, en déplacement, pressé : ils veulent voir leurs ventes,
relancer une livraison et publier une page de vente sans friction.

Utilisateurs secondaires via RBAC : opérateurs/support (réconciliation des
transactions, relances, lecture), et admins/super-admins techniques
(configuration des agrégateurs/SMTP/SMS, gestion des comptes).

## Product Purpose

CaaS (Checkout-as-a-Service) est la plomberie de paiement mobile money
(Kkiapay, CinetPay) pour vendeurs digitaux francophones. L'application couvre :

- un **dashboard admin** : transactions (liste, filtres, export, réconciliation,
  relance de livraison), statistiques et revenus ;
- un **page builder** : landings de vente publiques composées de blocs, contenu
  multi-texte en Markdown ;
- la **gestion d'équipe** (RBAC : super_admin / admin / operator / reader) ;
- la **configuration runtime** (SMTP, agrégateurs de paiement, SMS) éditable à
  chaud, secrets chiffrés.

Le succès : le vendeur encaisse vite, comprend l'état de chaque paiement d'un
coup d'œil, et configure/publie sans toucher au code ni redéployer.

## Brand Personality

**Fiable · Direct · Chaleureux.** Sérieux quand il s'agit d'argent (statuts
clairs, jamais d'ambiguïté sur un montant), sans jargon ni anglicismes
marketing, avec la chaleur de l'identité ambre/orange ouest-africaine. Le ton
des libellés est factuel et en français : on dit ce que l'action fait.

## Anti-references

- **SaaS générique navy/violet** : dashboard bleu-nuit/indigo, grilles de cartes
  identiques, dégradés décoratifs partout. À proscrire.
- **Surchargé / "gamifié"** : trop d'animations, badges, confettis, couleurs
  criardes. C'est un outil de travail, pas un jeu.
- **Admin brut non stylé** : Bootstrap/Material par défaut, tables nues, zéro
  hiérarchie. L'opposé du soin attendu.

## Design Principles

1. **Le flux de travail d'abord.** Chaque écran sert une tâche précise ; la
   hiérarchie visuelle guide la décision (traiter une transaction, publier une
   page), elle ne décore pas.
2. **Confiance sur l'argent.** L'état d'un paiement (succès / en attente /
   échec / security_error) se lit instantanément ; un montant n'est jamais
   ambigu. La sécurité (secrets masqués, rôles) est visible sans être anxiogène.
3. **Chaleur mesurée.** L'ambre ponctue (CTA, élément actif, focus, statuts
   positifs) ; il ne sature pas la surface. La chaleur passe par l'accent et la
   typographie, jamais par un fond crème "par défaut".
4. **Mobile réel.** Pensé pour un vendeur sur téléphone : cibles tactiles
   confortables, contenu prioritaire visible sans scroll, formulaires courts.
5. **Sans dev.** Configurer un agrégateur, publier une landing, gérer une équipe
   se fait dans l'UI ; l'interface rend le configurable évident et réversible.

## Accessibility & Inclusion

Cible **WCAG 2.1 AA** : contraste ≥ 4.5:1 pour le texte courant (placeholders
inclus), ≥ 3:1 pour le grand texte ; navigation clavier complète et focus
visibles ; cibles tactiles confortables (usage mobile répandu, réseaux parfois
lents). Toute animation a une alternative `prefers-reduced-motion`. Les statuts
ne reposent jamais sur la couleur seule (libellé/icône en plus).
