# Multi-stage build for AI Command Gateway
FROM python:3.13-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Runtime stage
FROM python:3.13-slim as runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies including Docker CLI
RUN apt-get update && apt-get install -y \
    docker.io \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user and add to docker group for Docker socket access
RUN groupadd -r appuser && \
    useradd -r -g appuser appuser && \
    usermod -aG docker appuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create application directory
WORKDIR /app

# Copy application source code
COPY src/ /app/src/

# Set ownership for security
RUN chown -R appuser:appuser /app

# Create directory for logs
RUN mkdir -p /app/logs && chown appuser:appuser /app/logs

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Expose port
EXPOSE 8003

# Set default command
CMD ["python", "-m", "uvicorn", "gateway.api.main:app", "--host", "0.0.0.0", "--port", "8003"] 