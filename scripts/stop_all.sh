#!/usr/bin/env sh

echo "Deteniendo LAB IA..."

PIDS_8000="$(lsof -tiTCP:8000 -sTCP:LISTEN 2>/dev/null || true)"
if [ -n "$PIDS_8000" ]; then
  kill $PIDS_8000
fi

PIDS_8081="$(lsof -tiTCP:8081 -sTCP:LISTEN 2>/dev/null || true)"
if [ -n "$PIDS_8081" ]; then
  kill $PIDS_8081
fi

if docker ps --format '{{.Names}}' | grep -qx 'qdrant-lab'; then
  docker stop qdrant-lab >/dev/null
fi

echo "LAB IA detenido"
