#!/usr/bin/env sh
set +e
echo "=== LAB IA Insurance - chequeo de entorno ==="
for cmd in python uv ollama; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "[OK] $cmd"
    "$cmd" --version
  else
    echo "[FALTA] $cmd"
  fi
done
echo "Qdrant debe estar disponible en http://localhost:6333 para las capacidades RAG."
