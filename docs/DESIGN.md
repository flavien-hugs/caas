---
name: CaaS Admin
description: Checkout-as-a-Service pour vendeurs digitaux d'Afrique francophone — système visuel ambre, net et fiable.
colors:
  orange-marche: "#e9590c"
  orange-marche-foreground: "#ffffff"
  ambre: "#f59f0a"
  ink: "#2b221d"
  surface: "#ffffff"
  secondary: "#faf5f0"
  secondary-ink: "#3c2b20"
  muted: "#f9f5f1"
  muted-ink: "#817065"
  accent: "#fff3e0"
  accent-ink: "#934510"
  destructive: "#ef4343"
  border: "#ede6de"
typography:
  display:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "clamp(1.875rem, 5vw, 3rem)"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 500
    lineHeight: 1.3
  body:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "0.02em"
rounded:
  sm: "6px"
  md: "8px"
  lg: "16px"
  full: "9999px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "24px"
components:
  button-primary:
    backgroundColor: "{colors.orange-marche}"
    textColor: "{colors.orange-marche-foreground}"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
    height: "36px"
  button-primary-hover:
    backgroundColor: "{colors.orange-marche}"
    textColor: "{colors.orange-marche-foreground}"
  button-outline:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
    height: "36px"
  button-secondary:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.secondary-ink}"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
    height: "36px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "24px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "4px 12px"
    height: "36px"
---

# Design System: CaaS Admin

## 1. Overview

**Creative North Star: "Le comptoir ambré"**

CaaS Admin est le comptoir d'un marchand : clair, ordonné, baigné d'une lumière
ambrée ouest-africaine. C'est un outil de travail où l'on traite des paiements
et publie des pages de vente, pas une vitrine. La densité est celle d'une
application : du texte courant à 14px qui fait le gros du travail, des surfaces
blanches sur un fond à peine réchauffé, et l'orange qui n'apparaît que là où il
guide une action ou signale un état. La chaleur vient de l'accent et de la
typographie, jamais d'un fond crème par défaut.

Le système rejette explicitement trois dérives : le **SaaS générique navy/violet**
(dashboards bleu-nuit, grilles de cartes identiques, dégradés décoratifs), le
**surchargé/"gamifié"** (animations criardes, badges, confettis dans un outil
sérieux), et l'**admin brut non stylé** (tables nues, zéro hiérarchie). Sérieux
quand il s'agit d'argent, chaleureux dans le ton.

**Key Characteristics:**
- Fond blanc / neutres chauds (jamais crème), l'ambre/orange comme seul accent.
- Densité applicative : `body` à 14px, hiérarchie par poids et taille.
- Plat par défaut ; l'ombre signale l'état, teintée orange sur les surfaces vedettes.
- Mobile réel : cibles tactiles confortables, contenu prioritaire d'abord.
- Statut jamais porté par la couleur seule (libellé + icône).

## 2. Colors

Une base neutre chaude et blanche, ponctuée d'un unique accent ambre/orange qui
porte l'identité et l'action.

### Primary
- **Orange Marché** (#e9590c, `hsl(21 90% 48%)`): l'accent unique. CTA principaux,
  élément de navigation actif, anneau de focus, indicateurs positifs. Choisi pour
  son contraste suffisant avec le blanc (texte blanc sur orange ≥ 3:1) tout en
  évoquant le commerce ouest-africain.
- **Ambre** (#f59f0a, `hsl(38 92% 50%)`): l'extrémité claire de l'identité.
  Dégradés de marque (badge, hero), surbrillances. À utiliser avec Orange Marché,
  pas seul comme texte sur blanc (contraste insuffisant).

### Neutral
- **Ink** (#2b221d, `hsl(24 20% 14%)`): texte courant et titres. Un quasi-noir
  légèrement chaud, pas un gris — c'est ce qui garde la lecture nette.
- **Surface** (#ffffff): fond des pages et des cartes.
- **Secondary** (#faf5f0) / **Muted** (#f9f5f1): fonds toniques chauds pour
  zones secondaires, survol de navigation, lignes alternées.
- **Muted Ink** (#817065): texte secondaire/légendes. Plancher de contraste à
  surveiller : à réserver au texte ≥ body, jamais sous 4.5:1 pour du corps dense.
- **Accent** (#fff3e0) / **Accent Ink** (#934510): paire chaude pour survols de
  boutons fantômes et bannières d'information douces.
- **Border** (#ede6de): bordures et séparateurs (sert aussi de couleur d'`input`).

### Tertiary
- **Destructive** (#ef4343, `hsl(0 84% 60%)`): suppressions, erreurs. Seule
  entorse au monochrome ambre, réservée au danger réel.

### Named Rules
**La règle de l'accent unique.** Orange Marché occupe ≤ 10 % d'un écran donné.
Sa rareté est ce qui le rend lisible comme signal d'action. Si deux choses se
disputent l'orange à l'écran, l'une n'est pas une action principale.

**La règle anti-crème.** Le fond est blanc ou un neutre chaud très désaturé
(chroma quasi nul vers la teinte de la marque). Jamais de fond crème/sable/beige
"pour la chaleur" : la chaleur passe par l'accent et la typo.

## 3. Typography

**Display Font:** stack sans système (`ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, …`)
**Body Font:** identique (une seule famille, contraste par le poids)
**Label/Mono Font:** aucune (pas de mono dans le produit)

**Character:** une grotesque système neutre et rapide à charger, qui s'efface
devant les données. La personnalité vient du contraste de poids (400 → 700) et de
l'échelle, pas d'un caractère décoratif. Une seule famille : la cohérence prime.

### Hierarchy
- **Display** (700, clamp(1.875rem, 5vw, 3rem), 1.1, -0.02em): titres de blocs
  hero des landings publiques uniquement. Plafond volontairement bas (≤ 3rem) —
  un admin ne crie pas.
- **Headline** (600, 1.5rem, 1.2, -0.01em): titre de page admin (Dashboard,
  Transactions, Configuration).
- **Title** (500, 1.125rem, 1.3): titres de carte et de section.
- **Body** (400, 0.875rem, 1.5): le cheval de trait. Texte d'interface, libellés
  de formulaire, cellules de table. Prose courante plafonnée à 65–75ch.
- **Label** (500, 0.75rem, 0.02em): libellés de champ et badges. En-têtes de
  groupe de navigation en 10px majuscules tracées — usage rare, réservé à la nav.

### Named Rules
**La règle d'une seule famille.** Pas d'appariement de polices. Toute la
hiérarchie tient par poids + taille. Ajouter une seconde famille serait de
l'indécision, pas de la richesse.

**La règle anti-capitales.** Les majuscules sont réservées aux libellés courts
(≤ 4 mots) et aux en-têtes de groupe de nav. Jamais de phrase en capitales.

## 4. Elevation

Plat par défaut. Les surfaces (cartes, champs, boutons) reposent à plat avec une
bordure 1px et, au plus, une `shadow-sm` discrète. La profondeur naît surtout des
bordures et des fonds toniques chauds, pas des ombres. Les ombres marquées sont un
**signal d'état** (survol, focus) ou réservées aux **surfaces vedettes** (carte de
connexion, badge de marque) où elles sont teintées orange pour renforcer l'identité.

### Shadow Vocabulary
- **Repos** (`box-shadow: 0 1px 2px rgba(0,0,0,0.05)`): cartes, champs, boutons.
  Quasi imperceptible, juste de quoi décoller du fond.
- **Vedette** (`box-shadow: 0 20px 25px -5px rgba(124,45,18,0.05)`): carte de
  connexion. Ombre large et tiède, jamais dure.
- **Lueur de marque** (`box-shadow: 0 10px 15px -3px rgba(234,88,12,0.30)`):
  badge dégradé ambre→orange, halos de la page de connexion.

### Named Rules
**La règle plat-par-défaut.** Une surface est plate au repos. Une ombre apparaît
en réponse à un état (hover, focus, élévation), pas comme décor permanent.

**La règle anti-fantôme.** Jamais bordure 1px **et** ombre large floue (≥16px) de
décor sur le même élément. On choisit l'un : une bordure pleine, ou une ombre
définie ≤ 8px. (Le pairing des deux est le tell le plus fréquent à proscrire.)

## 5. Components

Net & efficace : précis, rayons modérés, transitions brèves (`transition-colors`).
L'outil s'efface devant la tâche.

### Buttons
- **Shape:** coins légèrement arrondis (6px, `rounded-md`). Les boutons-icône et
  pastilles peuvent aller jusqu'au plein arrondi.
- **Primary:** fond Orange Marché, texte blanc, padding 8px 16px, hauteur 36px.
  Survol : `opacity: 0.9` (pas de changement de teinte).
- **Hover / Focus:** focus visible via anneau 2px Orange Marché (`ring-ring`).
  Transitions de couleur uniquement.
- **Secondary / Outline / Ghost:** Secondary = fond crème chaud (#faf5f0) ;
  Outline = bordure + fond blanc, survol fond Accent (#fff3e0) ; Ghost = survol
  Accent sans bordure. Tailles sm (h-32px) / default (36px) / lg (40px) / icon (36²).

### Cards / Containers
- **Corner Style:** 8px (`rounded-lg`).
- **Background:** Surface (#ffffff).
- **Shadow Strategy:** `shadow-sm` au repos (voir Elevation). Pas d'ombre large + bordure.
- **Border:** 1px Border (#ede6de).
- **Internal Padding:** 24px (lg).
- **Cartes imbriquées : interdites.** Une carte ne contient jamais une autre carte.

### Inputs / Fields
- **Style:** hauteur 36px, bordure 1px Border, fond blanc, rayon 6px, padding 4px 12px.
- **Focus:** anneau 2px Orange Marché ; l'icône d'aide passe en Orange au focus
  (`group-focus-within`).
- **Secrets:** champs `password` avec placeholder explicite (« •••• configuré —
  laisser vide pour conserver ») ; un secret n'est jamais réaffiché.
- **Error / Disabled:** message en Destructive ; disabled à 50% d'opacité.

### Navigation
- **Style:** sidebar admin repliable (persistée en localStorage), libellés Body,
  groupes coiffés d'un label 10px majuscules. Survol = fond Secondary.
- **Actif:** deux conventions selon la zone — nav principale : fond Secondary +
  texte Secondary Ink ; sous-nav Configuration : fond `orange/10` + texte Orange
  Marché + filet gauche 2px Orange (indicateur de nav, autorisé — ce n'est pas un
  bandeau de carte).
- **Mobile:** la sidebar repasse en barre horizontale scrollable.

### Combobox (select recherchable, composant signature)
Déclencheur type champ (bordure, rayon 6px) ouvrant un popover (`bg-popover`,
bordure, `shadow-lg`) avec champ de recherche, filtrage live, navigation clavier
(↑/↓/Entrée/Échap), coche sur l'option sélectionnée. À préférer au `<select>`
natif dès qu'il y a plus de quelques options ou un besoin de recherche.

## 6. Do's and Don'ts

### Do:
- **Do** garder Orange Marché (#e9590c) sur ≤ 10 % de l'écran : CTA, actif, focus, succès.
- **Do** écrire le texte courant en Ink (#2b221d) sur blanc ; viser ≥ 4.5:1, surtout pour Muted Ink (#817065) qu'on réserve aux légendes.
- **Do** rester plat au repos : bordure 1px Border (#ede6de) + `shadow-sm` ; l'ombre marque l'état.
- **Do** porter le statut d'un paiement par libellé **et** icône, jamais par la couleur seule.
- **Do** fournir une alternative `prefers-reduced-motion` à chaque animation (crossfade ou instantané).
- **Do** utiliser le Combobox recherchable plutôt qu'un `<select>` natif pour les choix non triviaux.
- **Do** des libellés de bouton verbe + objet en français (« Enregistrer », « Envoyer un test »).

### Don't:
- **Don't** virer au **SaaS générique navy/violet** : pas de dashboard bleu-nuit/indigo, pas de grilles de cartes identiques, pas de dégradés décoratifs partout.
- **Don't** **surcharger / "gamifier"** : pas de confettis, badges clinquants, couleurs criardes ou animations gratuites dans un outil de travail.
- **Don't** livrer un **admin brut non stylé** : pas de table nue ni de hiérarchie absente.
- **Don't** poser un fond crème/sable/beige « pour la chaleur ». Fond blanc ou neutre chaud désaturé ; la chaleur vient de l'accent.
- **Don't** appairer bordure 1px **et** ombre floue ≥ 16px sur le même élément (le « ghost-card »).
- **Don't** arrondir une carte au-delà de 16px. Cartes 8px, contrôles 6px, plein arrondi réservé aux pastilles/boutons-icône.
- **Don't** imbriquer des cartes, ni utiliser un filet latéral coloré (>1px) comme accent décoratif sur une carte/alerte (le filet de nav actif est la seule exception).
- **Don't** mettre une phrase en capitales ni du texte de marque type « X theater » / « not just X, it's Y ».
