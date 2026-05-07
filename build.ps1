# Build the Docker image for the SeaClear replication.
# Run this from PowerShell after Docker Desktop is running.

$ErrorActionPreference = "Stop"

Write-Host "Checking Docker daemon..." -ForegroundColor Cyan
docker info --format '{{.ServerVersion}}' | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker daemon not reachable. Start Docker Desktop and retry." -ForegroundColor Red
    exit 1
}

Write-Host "Building seaclear-replication:melodic ..." -ForegroundColor Cyan
docker compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed." -ForegroundColor Red
    exit 1
}

Write-Host "Build complete. Run with: .\run-headless.ps1" -ForegroundColor Green
