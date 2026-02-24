# Stage 1: Python dependencies
FROM python:3.11-slim AS backend-deps
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir . && pip install --no-cache-dir asyncpg

# Stage 2: Frontend build
FROM node:20-slim AS frontend-build
WORKDIR /app/dashboard
COPY dashboard/package.json dashboard/package-lock.json* ./
RUN npm ci
COPY dashboard/ ./
RUN npm run build

# Stage 3: Runtime
FROM python:3.11-slim AS runtime
WORKDIR /app

# Copy Python deps from stage 1
COPY --from=backend-deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-deps /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini pyproject.toml ./

# Copy built frontend
COPY --from=frontend-build /app/dashboard/dist ./dashboard/dist

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
