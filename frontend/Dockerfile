# SvelteKit (adapter-node) — multi-stage build.
#
# BACKEND_BASE est lu via `$env/dynamic/private` (au runtime), pas au build :
# la même image marche partout, il suffit de passer `-e BACKEND_BASE=...` au
# `docker run` (ou via les variables du compose / de l'orchestrateur).

FROM node:22-alpine AS base
RUN corepack enable
WORKDIR /app

# --- Dépendances complètes + build ------------------------------------------
FROM base AS build
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

# --- Dépendances de production uniquement -----------------------------------
FROM base AS prod-deps
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --prod --frozen-lockfile

# --- Image finale -----------------------------------------------------------
FROM node:22-alpine AS runtime
WORKDIR /app
# BACKEND_BASE : à surcharger au runtime (-e BACKEND_BASE=http://backend:8080).
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000
ENV BACKEND_BASE=http://localhost:8080
COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=build /app/build ./build
COPY --from=build /app/package.json ./package.json
EXPOSE 3000
USER node
CMD ["node", "build"]
