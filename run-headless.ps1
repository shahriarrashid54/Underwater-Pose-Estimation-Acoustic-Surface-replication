# Run all 6 experiments headless inside the container.
# Results land in .\results on the host.

$ErrorActionPreference = "Stop"

if (-not (Test-Path .\results)) { New-Item -ItemType Directory -Path .\results | Out-Null }

Write-Host "Launching all experiments (headless). This takes ~25-30 min." -ForegroundColor Cyan
docker compose run --rm seaclear bash /root/run_all_experiments.sh
if ($LASTEXITCODE -ne 0) {
    Write-Host "Experiment run failed; see logs in .\results\*.log" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Tables:" -ForegroundColor Green
Get-ChildItem .\results\table_*.txt | ForEach-Object {
    Write-Host "==== $($_.Name) ===="
    Get-Content $_.FullName
    Write-Host ""
}

Write-Host "Figures saved in .\results\fig*.png" -ForegroundColor Green
