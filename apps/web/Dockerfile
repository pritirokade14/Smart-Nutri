# syntax=docker/dockerfile:1
# Build from the REPO ROOT: docker build -f apps/web/Dockerfile -t sn-web .
FROM node:24-slim AS base
ENV PNPM_HOME=/pnpm PATH=/pnpm:$PATH
RUN corepack enable
WORKDIR /repo

FROM base AS build
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json apps/web/
COPY packages/api-contract/ts/package.json packages/api-contract/ts/
COPY packages/i18n/package.json packages/i18n/
COPY packages/design-tokens/package.json packages/design-tokens/
COPY packages/test-fixtures/package.json packages/test-fixtures/
RUN pnpm install --frozen-lockfile --filter @smartnutri/web...
COPY apps/web apps/web
COPY packages packages
# NEXT_PUBLIC_* are public by definition and baked into the browser bundle at build time.
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_SITE_URL
ARG NEXT_PUBLIC_POSTHOG_KEY
ARG NEXT_PUBLIC_SENTRY_DSN
ARG NEXT_PUBLIC_FEATURE_PHONE_OTP=false
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL \
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=$NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY \
    NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL \
    NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL \
    NEXT_PUBLIC_POSTHOG_KEY=$NEXT_PUBLIC_POSTHOG_KEY \
    NEXT_PUBLIC_SENTRY_DSN=$NEXT_PUBLIC_SENTRY_DSN \
    NEXT_PUBLIC_FEATURE_PHONE_OTP=$NEXT_PUBLIC_FEATURE_PHONE_OTP \
    NEXT_TELEMETRY_DISABLED=1
RUN pnpm --filter @smartnutri/web build

FROM node:24-slim AS runner
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=8080 HOSTNAME=0.0.0.0
WORKDIR /app
RUN useradd --system --create-home --uid 10001 app
COPY --from=build --chown=app:app /repo/apps/web/.next/standalone ./
COPY --from=build --chown=app:app /repo/apps/web/.next/static ./apps/web/.next/static
COPY --from=build --chown=app:app /repo/apps/web/public ./apps/web/public
USER app
EXPOSE 8080
CMD ["node", "apps/web/server.js"]
