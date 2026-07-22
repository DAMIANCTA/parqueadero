# Arranca todo el proyecto con un solo comando: Docker Compose levanta el
# backend completo, incluido garita-controller (el orquestador de la garita
# fisica), que ahora corre como un microservicio mas del stack.
#
# garita-controller usa una camara IP (PLATE_CAMERA_SOURCE en .env) para la
# deteccion de placa, no una webcam USB: Docker Desktop en Windows no tiene
# paso de dispositivos USB a contenedores de forma confiable, asi que se opto
# por camara de red para poder tenerlo dentro de Docker Compose junto a los
# demas servicios.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Set-Location $root
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Se creo .env desde .env.example (primera vez)."
} else {
    Write-Host ".env ya existe, no se toca (para no perder ajustes ya hechos)."
}
Write-Host "Levantando Docker Compose (backend completo, incluye garita-controller)..."
docker compose up -d --build

Write-Host "Esperando a que parking-service responda..."
$deadline = (Get-Date).AddSeconds(120)
$ready = $false
while ((Get-Date) -lt $deadline) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8004/health" -UseBasicParsing -TimeoutSec 3
        if ($resp.StatusCode -eq 200) { $ready = $true; break }
    } catch {
        Start-Sleep -Seconds 2
    }
}
if ($ready) {
    Write-Host "Backend listo."
} else {
    Write-Warning "parking-service no respondio en 120s (revisa 'docker compose logs')."
}

$garitaPort = (Get-Content .env | Where-Object { $_ -match '^GARITA_CONTROLLER_PORT=' }) -replace '^GARITA_CONTROLLER_PORT=', ''
if (-not $garitaPort) { $garitaPort = "8010" }
Write-Host "Vista en vivo de la garita: http://localhost:$garitaPort/"
Write-Host "Configura PLATE_CAMERA_SOURCE en .env con la URL de tu camara IP (rtsp://... o http://...) y 'docker compose up -d --build garita-controller' de nuevo si la cambias."
