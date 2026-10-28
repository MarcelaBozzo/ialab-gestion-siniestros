#!/usr/bin/env sh
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

echo "Iniciando LAB IA..."

# Qdrant
if ! docker info >/dev/null 2>&1; then
  echo "ERROR: abre Docker Desktop antes de iniciar el laboratorio."
  exit 1
fi

if ! docker ps --format '{{.Names}}' | grep -qx 'qdrant-lab'; then
  if docker ps -a --format '{{.Names}}' | grep -qx 'qdrant-lab'; then
    docker start qdrant-lab >/dev/null
  else
    docker run --name qdrant-lab -p 6333:6333 -p 6334:6334 -d qdrant/qdrant >/dev/null
  fi
fi

# Customer API
if ! lsof -tiTCP:8081 -sTCP:LISTEN >/dev/null 2>&1; then
  nohup uv run uvicorn customer_mock.main:app --host 127.0.0.1 --port 8081 \
    > /tmp/customer-mock.log 2>&1 &
fi

# Backend + frontend
if ! lsof -tiTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  nohup env CUSTOMER_INTEGRATION_PROVIDER=rest \
    uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 \
    > /tmp/claims-api.log 2>&1 &
fi

sleep 2

echo ""
echo "LAB IA iniciado"
echo "Plataforma:   http://127.0.0.1:8000"
echo "Customer API: http://127.0.0.1:8081"
echo "Qdrant:       http://127.0.0.1:6333"
