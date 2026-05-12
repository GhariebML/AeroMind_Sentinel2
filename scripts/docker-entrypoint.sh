#!/bin/bash
set -e

# ═══════════════════════════════════════════════════════════════════════
#  AIC-4 DroneTracking — Professional Docker Entrypoint
# ═══════════════════════════════════════════════════════════════════════

# Fix permissions for mounted volumes
# We do this as root before dropping privileges
echo "[ENTRYPOINT] Adjusting permissions for volumes..."
mkdir -p /app/experiments /app/models /app/data /app/configs
chown -R aic4user:aic4group /app/experiments /app/models /app/data /app/configs

echo "[ENTRYPOINT] Initializing AIC-4 environment..."

# Drop privileges and execute the command
echo "[ENTRYPOINT] Executing as aic4user: $@"
exec gosu aic4user "$@"
