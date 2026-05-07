# Open an interactive container shell with X-server forwarding for Gazebo GUI.
# Requires VcXsrv or X410 running on the host with access control disabled.

$ErrorActionPreference = "Stop"

if (-not $env:DISPLAY) {
    $env:DISPLAY = "host.docker.internal:0.0"
    Write-Host "DISPLAY not set; using $env:DISPLAY" -ForegroundColor Yellow
}

Write-Host "Opening shell. From inside the container run:" -ForegroundColor Cyan
Write-Host "  roslaunch seaclear_pose experiment_imu_dvl_usbl.launch \\" -ForegroundColor Cyan
Write-Host "      duration:=150 out_path:=/root/results/imu_dvl_usbl.csv" -ForegroundColor Cyan

docker compose run --rm seaclear
