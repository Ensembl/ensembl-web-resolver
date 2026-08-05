# syntax=docker/dockerfile:1.7
# Base image
FROM python:3.11-slim

# Maintainer
LABEL org.opencontainers.image.authors="ensembl-webteam@ebi.ac.uk"

# Set Work Directory
WORKDIR /

# Copy source code
COPY ./app /app/
COPY requirements.txt /requirements.txt
COPY resolver_mappings.db /app/resolver_mappings.db

# Install dependencies. The job token is mounted only for this command and is
# not retained in the resulting layer or image history.
ARG GITLAB_USER=gitlab-ci-token
RUN --mount=type=secret,id=gitlab_token \
    gitlab_token="$(cat /run/secrets/gitlab_token)" && \
    pip install --no-cache-dir \
      --extra-index-url "https://${GITLAB_USER}:${gitlab_token}@gitlab.ebi.ac.uk/api/v4/projects/6228/packages/pypi/simple" \
      -r /requirements.txt

# Store metrics from all Uvicorn workers.
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus-multiproc
RUN mkdir -p /tmp/prometheus-multiproc

# Expose Ports
ENV PORT 8001
EXPOSE 8001

# Run uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "5"]
