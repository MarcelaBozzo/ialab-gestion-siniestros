#!/usr/bin/env sh
set -e
cd "$(dirname "$0")/../backend"
uv run fastapi dev customer_mock/main.py --port 8081
