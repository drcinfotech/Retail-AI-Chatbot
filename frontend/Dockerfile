# ─── Retail AI Chatbot — Frontend Dockerfile ──────────────
# Two-stage build: compile the Vite bundle with Node, then serve the
# static dist/ with nginx (which also proxies /api → backend container).

# ─── Stage 1: Build ─────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Cache deps layer
COPY package*.json ./
RUN npm ci --silent

# Build the production bundle
COPY . .
RUN npm run build

# ─── Stage 2: Serve ─────────────────────────────────────
FROM nginx:1.27-alpine AS runner

# Custom nginx config: serves SPA + proxies /api/* to the backend service
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built static files from the build stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
