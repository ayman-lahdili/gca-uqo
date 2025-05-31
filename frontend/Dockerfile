# ----------------------
# Build Stage
# ----------------------
FROM node:18-slim AS builder

# Set working directory
WORKDIR /app

# Copy only necessary files for installing dependencies
COPY frontend/package*.json ./

# Install ALL dependencies (required for build tools like Vite + Rollup)
RUN npm ci

# Copy application source
COPY frontend/ .

# Build the application for production
RUN npm run build
