FROM node:20-alpine AS base
WORKDIR /app

# ── dev stage ──────────────────────────────────────────────────────────────
# node_modulesはdocker-composeの名前付きボリュームで管理する
FROM base AS dev
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
CMD ["npm", "run", "dev"]

# ── builder stage ──────────────────────────────────────────────────────────
FROM base AS builder
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ── prod stage ─────────────────────────────────────────────────────────────
# Next.js standaloneモードで最小イメージを構成（ECS Fargateへのデプロイ用）
FROM base AS prod
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
