# Multi-stage build for React app
FROM node:18-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including devDependencies for build)
RUN npm install

# Copy source code
COPY . .

# Build the React app
RUN npm run build

# Production stage
FROM node:18-alpine

# Install dependencies for serving and health checks
RUN apk add --no-cache wget

# Install serve globally
RUN npm install -g serve

# Set working directory
WORKDIR /app

# Copy built app from build stage
COPY --from=build /app/build ./build

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S frontend -u 1001

# Change ownership of the app directory
RUN chown -R frontend:nodejs /app
USER frontend

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=3 \
    CMD wget --no-verbose --tries=1 --output-document=/dev/null http://localhost:3000/ || exit 1

# Start the application
CMD ["serve", "-s", "build", "-l", "3000"] 