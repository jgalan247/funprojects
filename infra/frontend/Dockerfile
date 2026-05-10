# Vue 3 + Vite + Tailwind frontend, built into static files and served by
# nginx. Build context is the repo root.

# ---------- build stage ------------------------------------------------------
FROM node:20-alpine AS build

WORKDIR /app

# Install deps separately so they cache.
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# Copy source and build.
COPY frontend/ ./
RUN npm run build

# ---------- serve stage ------------------------------------------------------
FROM nginx:1.27-alpine AS serve

COPY infra/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --quiet --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
