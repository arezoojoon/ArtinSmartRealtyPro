# ArtinSmartRealty Frontend Dockerfile
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies with clean cache
RUN npm cache clean --force && \
    npm install --legacy-peer-deps

# Copy source code
COPY . .

# Build the application with verbose logging
RUN npm run build || (echo "Build failed, listing directory:" && ls -la && exit 1)

# Production stage
FROM nginx:alpine

# Install curl for healthcheck
RUN apk add --no-cache curl

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy smart-upload.html to nginx html directory
COPY smart-upload.html /usr/share/nginx/html/smart-upload.html

# Copy nginx configuration
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Copy environment injection script
COPY env-config.sh /docker-entrypoint.d/env-config.sh
RUN chmod +x /docker-entrypoint.d/env-config.sh

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
