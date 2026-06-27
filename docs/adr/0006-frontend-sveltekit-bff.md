# ADR-0006 — Frontend SvelteKit en BFF, configuration au runtime

- **Statut** : Accepté
- **Date** : 2026-06-26

## Contexte

Le frontend (admin + landings publiques) doit appeler l'API backend en gardant
les secrets et l'URL backend hors du navigateur, et l'image Docker doit être
**agnostique de l'environnement** (une image, plusieurs déploiements).

## Décision

- **SvelteKit 2 / Svelte 5** avec **adapter-node** : un serveur Node sert le
  front et joue le rôle de **BFF**. Tous les fetchs vers le backend se font
  **côté serveur** via `BACKEND_BASE` ; le navigateur ne voit que le serveur
  SvelteKit. Le cookie de session est relayé (`hooks.server.ts`).
- `BACKEND_BASE` est lu via **`$env/dynamic/private`** (résolu au **runtime**),
  centralisé dans `$lib/server/env.ts`. L'image ne fige donc pas l'URL backend
  au build ; on passe `-e BACKEND_BASE=…` au conteneur.
- Stack : Tailwind 4 (tokens `@theme`), Vite 6, bits-ui, superforms + zod,
  lucide, marked + isomorphic-dompurify. Client API typé maison
  (`$lib/api/client.ts`).

## Conséquences

**Positives**
- Secrets/URL backend jamais exposés au client ; une seule image réutilisable
  sur dev/staging/prod.
- BFF = endroit naturel pour adapter les réponses et gérer les cookies.

**Négatives / suivi**
- Toute la navigation admin dépend du serveur Node (SSR) ; prévoir le
  dimensionnement.
- Deux lockfiles cohabitent (`pnpm-lock.yaml` et `package-lock.json`) :
  **pnpm** fait foi — supprimer `package-lock.json` pour éviter la dérive.
