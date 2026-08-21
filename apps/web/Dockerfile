FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
ARG APP_ENVIRONMENT=development
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ARG NEXT_PUBLIC_SITE_URL=http://localhost:3000
ARG NEXT_PUBLIC_TURNSTILE_SITE_KEY
ARG NEXT_PUBLIC_GITHUB_USERNAME
ARG CONTENT_REVALIDATE_SECONDS=60

ENV APP_ENVIRONMENT=$APP_ENVIRONMENT \
    NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL \
    NEXT_PUBLIC_TURNSTILE_SITE_KEY=$NEXT_PUBLIC_TURNSTILE_SITE_KEY \
    NEXT_PUBLIC_GITHUB_USERNAME=$NEXT_PUBLIC_GITHUB_USERNAME \
    CONTENT_REVALIDATE_SECONDS=$CONTENT_REVALIDATE_SECONDS

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN node -e 'console.log("APP_ENVIRONMENT=" + JSON.stringify(process.env.APP_ENVIRONMENT)); console.log("NEXT_PUBLIC_API_URL=" + JSON.stringify(process.env.NEXT_PUBLIC_API_URL)); console.log("URL_LENGTH=" + (process.env.NEXT_PUBLIC_API_URL || "").length)'

RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
# Railway rebuild trigger
