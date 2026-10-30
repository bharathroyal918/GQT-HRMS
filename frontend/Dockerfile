# ==============================================================================
# GQT HRMS Frontend — Production Multi-Stage Dockerfile
# Stage 1: Node.js 22 LTS Builder
# Stage 2: Nginx 1.27 Alpine Slim Production Edge Server
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build React 19 + TypeScript + Vite Application
# ------------------------------------------------------------------------------
FROM node:22-alpine AS builder

WORKDIR /app

# Install dependencies using clean install with frozen lockfile
COPY package.json package-lock.json ./
RUN npm ci --no-audit --prefer-offline

# Copy frontend source files
COPY . .

# Build argument: Relative API base URL for single-origin reverse proxying
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build production assets (TypeScript validation + Vite bundle optimization)
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Serve Production Assets via Nginx
# ------------------------------------------------------------------------------
FROM nginx:1.27-alpine-slim AS production

LABEL maintainer="GQT DevOps <devops@gqtech.in>"
LABEL org.opencontainers.image.title="GQT HRMS Frontend SPA & Edge"
LABEL org.opencontainers.image.description="High performance Nginx server hosting GQT HRMS React SPA"
LABEL org.opencontainers.image.version="1.0.0"

# Copy compiled static distribution from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy production Nginx server configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port
EXPOSE 80

# Health check to ensure Nginx is responding on port 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1/ || exit 1

# Launch Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
