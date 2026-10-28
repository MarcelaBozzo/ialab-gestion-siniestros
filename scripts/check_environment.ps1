$ErrorActionPreference = "Continue"
Write-Host "=== LAB IA Insurance - chequeo de entorno ==="
$commands = @("python", "uv", "ollama")
foreach ($cmd in $commands) {
  if (Get-Command $cmd -ErrorAction SilentlyContinue) {
    Write-Host "[OK] $cmd"
    & $cmd --version
  } else {
    Write-Host "[FALTA] $cmd"
  }
}
Write-Host "Qdrant debe estar disponible en http://localhost:6333 para las capacidades RAG."
Write-Host "Lee 00_LEEME_PRIMERO.md antes de modificar el codigo."
