# ---------- Base ----------
FROM node:22-alpine AS base
WORKDIR /app
RUN npm install -g pnpm@11.20.0

# ---------- Build ----------
FROM base AS build
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

# ---------- Prod (étape par défaut) ----------
FROM node:22-alpine AS prod
WORKDIR /app
COPY --from=build /app/.output ./.output
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3010
EXPOSE 3010
CMD ["node", ".output/server/index.mjs"]