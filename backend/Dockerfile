# ==============================================================================
# GQT HRMS Backend — Production Dockerfile
# Base: Python 3.12 Slim (Debian Bookworm)
# Security: Non-root execution, minimal layers, pinned dependencies
# ==============================================================================

FROM python:3.12-slim-bookworm AS production

LABEL maintainer="GQT DevOps <devops@gqtech.in>"
LABEL org.opencontainers.image.title="GQT HRMS Backend API"
LABEL org.opencontainers.image.description="Enterprise HRMS & Recruitment CRM Django REST Backend"
LABEL org.opencontainers.image.version="1.0.0"

# Set secure, deterministic Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

# Create non-root dedicated application service user & group (UID 10001)
RUN groupadd --system --gid 10001 appgroup && \
    useradd --system --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin appuser

# Set predictable application working directory
WORKDIR /app

# Install dependencies in a separate layer for build cache efficiency
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application source code with non-root ownership
COPY --chown=appuser:appgroup manage.py ./
COPY --chown=appuser:appgroup config/ ./config/
COPY --chown=appuser:appgroup apps/ ./apps/

# Provision persistent directories for templates, static collection and media uploads
RUN mkdir -p /app/templates /app/staticfiles /app/media /app/media/private && \
    python manage.py collectstatic --noinput --settings=config.settings.test && \
    chown -R appuser:appgroup /app/templates /app/staticfiles /app/media && \
    chmod -R 750 /app/media

# Switch to unprivileged non-root user
USER appuser

# Document exposed HTTP port for internal container networking
EXPOSE 8000

# Health Check Strategy: Standard library urllib query to zero-secret health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/')" || exit 1

# Production WSGI Server: Gunicorn with multi-worker threads and stdout/stderr logging
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
