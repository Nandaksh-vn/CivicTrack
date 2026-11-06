# CivicTrack Frontend — multi-stage production image (19.1, DEP-005)
#
# Builder (node): npm ci + Vite production build with all VITE_* values
# baked in at build time (Vite inlines env at build, not at runtime).
# Runtime (nginx): serves the SPA with /api + /health proxying and SPA
# fallback, runs as non-root `nginx` user.
# Build:   docker compose build web
# Demo:    VITE_ALLOW_DEMO_ESCALATION=true docker compose build web

FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE_URL=/api/v1
ARG VITE_ENABLE_AI=false
ARG VITE_ENABLE_MAP=false
ARG VITE_ENABLE_FEEDBACK=false
ARG VITE_ALLOW_DEMO_ESCALATION=false
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_ENABLE_AI=${VITE_ENABLE_AI} \
    VITE_ENABLE_MAP=${VITE_ENABLE_MAP} \
    VITE_ENABLE_FEEDBACK=${VITE_ENABLE_FEEDBACK} \
    VITE_ALLOW_DEMO_ESCALATION=${VITE_ALLOW_DEMO_ESCALATION}

# Typecheck is a separate CI gate (`npm run typecheck`); the image builds the
# Vite bundle only so in-progress type errors cannot block a demo deploy.
# The frontend `build` script still typechecks in local/CI flows.
RUN npx vite build

FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

# nginx:alpine ships `nginx` (uid 101). Hand it the content + writable dirs
# and drop privileges. Ports are published (8080->80) by Compose; the
# container hits nginx on 80 inside the bridge network.
RUN chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d \
    && chown nginx:nginx /run \
    && chmod 755 /run

USER nginx

EXPOSE 80
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD wget -qO- http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
