FROM node:22-alpine
WORKDIR /app
RUN corepack enable
# pnpm-workspace.yaml contient l'autorisation de build d'esbuild (pnpm approve-builds)
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml* ./
RUN corepack install
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build
EXPOSE 3010
ENV HOST=0.0.0.0
ENV PORT=3010
CMD ["node", ".output/server/index.mjs"]