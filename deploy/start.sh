#!/bin/sh
set -eu
python -m scripts.validate_cloud_config
# One free instance. Do not run migrations concurrently from multiple replicas.
alembic -c backend/alembic.ini upgrade head
exec uvicorn backend.cloud_app:app --host 0.0.0.0 --port "${PORT:-10000}" --proxy-headers --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-*}"
