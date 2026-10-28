$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot/../backend"
uv run fastapi dev customer_mock/main.py --port 8081
