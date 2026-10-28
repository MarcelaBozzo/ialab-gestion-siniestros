#!/usr/bin/env sh
set -e
cd "$(dirname "$0")/../backend"
uv run fastapi dev app/main.py
