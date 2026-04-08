# syntax=docker/dockerfile:1
# Enable BuildKit for cache mounts (dramatically speeds up repeated builds)
FROM python:3.12-slim

# Install ONLY the system packages we actually need.
# build-essential / libgraphviz-dev / pkg-config removed — nothing in requirements.txt
# needs compilation (all packages ship pre-built wheels).
# apt cache is mounted so packages are not re-downloaded on every build.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    curl \
    graphviz \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (Hugging Face runs containers as user 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set working directory
WORKDIR $HOME/app

# Install Python dependencies with pip cache mounted.
# This layer is only rebuilt when requirements.txt changes.
COPY --chown=user requirements.txt .
RUN --mount=type=cache,target=/home/user/.cache/pip,uid=1000 \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy application source
COPY --chown=user . .

# Initialize Reflex (sets up .web directory structure).
# NOTE: `reflex export` (frontend build) is intentionally moved to prestart.sh
# so the heavy Next.js compilation step does NOT run on every Docker build.
RUN reflex init

# Ensure the database file is writable (HF Spaces requirement)
RUN touch reflex.db && chmod 666 reflex.db

# Make the startup script executable
RUN chmod +x prestart.sh

EXPOSE 7860

CMD ["bash", "prestart.sh"]
