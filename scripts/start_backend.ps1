$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot/../backend"
uv run fastapi dev app/main.py
