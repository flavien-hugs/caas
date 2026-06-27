# ADR-0005 — Page builder : blocs JSON opaques, schéma piloté par le frontend

- **Statut** : Accepté
- **Date** : 2026-06-18

## Contexte

Les vendeurs composent leurs landings via un page builder. On veut pouvoir
ajouter/faire évoluer des **types de blocs** rapidement, idéalement **sans
déploiement backend**, tout en gardant des données structurées.

## Décision

- Une page = `{ slug, title, blocks[], status }`. Chaque bloc =
  `{ id, type, props }`.
- Le backend stocke `blocks` comme **JSON opaque** (`PageRow.blocks`) et ne fait
  **aucune validation par type** : il persiste verbatim.
- Le **contrat par type vit dans le frontend** (Zod, `lib/blocks/types.ts`) :
  un schéma par bloc, une entrée dans le registre (`registry.ts`), un composant
  Svelte `{ props, mode }`. Ajouter un bloc = 3 fichiers front, 0 backend.
- Les champs **multi-textes** sont en **Markdown**, rendu **sanitisé** (marked +
  DOMPurify) avant `{@html}` (voir aussi DESIGN.md).
- Chaque bloc peut porter un blob `_style` partagé (fond/padding de section,
  alignement **des titres**, largeur), mappé en classes Tailwind déterministes.

## Conséquences

**Positives**
- Itération produit très rapide sur les blocs sans release backend.
- Découplage clair : structure (backend) vs présentation/validation (frontend).

**Négatives / suivi**
- La **validation** des props n'est pas garantie côté serveur ; un client
  malveillant pourrait stocker des props arbitraires. Mitigation : accès
  `manage:pages` requis ; le rendu sanitise le HTML. Une validation serveur
  optionnelle (JSON Schema) pourra être ajoutée si besoin.
- Pas de migration de blocs côté backend : les évolutions de schéma de bloc se
  gèrent par tolérance/fallback dans les composants (defaults Zod).
