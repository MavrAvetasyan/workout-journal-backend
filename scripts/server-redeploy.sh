#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f ".env.server" ]]; then
  echo ".env.server not found"
  exit 1
fi

docker compose -f docker-compose.server.yaml pull
docker compose -f docker-compose.server.yaml up -d
docker image prune -f
