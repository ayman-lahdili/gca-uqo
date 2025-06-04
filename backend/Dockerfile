FROM python:3.13.1-bullseye

# Install bash and uv
RUN apt-get update && apt-get install -y bash && pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy pyproject.toml and install dependencies
COPY backend/pyproject.toml .
RUN uv pip compile pyproject.toml > requirements.txt \
 && uv pip install -r requirements.txt --system

# Copy backend source code
COPY backend/src ./src

# Copy .env from project root
COPY .env .

# Copy Alembic configuration and migrations
COPY backend/alembic.ini .
COPY backend/alembic ./alembic

# Copy the startup script
COPY backend/scripts ./scripts
RUN chmod +x ./scripts/*.sh

# Expose FastAPI port
EXPOSE 8000

# Run the startup script
CMD ["./scripts/start.sh"]