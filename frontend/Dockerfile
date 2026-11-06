# CivicTrack Frontend - Multi-stage Production Dockerfile
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE_URL=/api/v1
ARG VITE_ENABLE_AI=false
ARG VITE_ENABLE_MAP=false
ARG VITE_ENABLE_FEEDBACK=false
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_ENABLE_AI=${VITE_ENABLE_AI} \
    VITE_ENABLE_MAP=${VITE_ENABLE_MAP} \
    VITE_ENABLE_FEEDBACK=${VITE_ENABLE_FEEDBACK}

RUN npm run build

# ----------------- Runtime Stage -----------------
FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
