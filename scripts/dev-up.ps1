# Arranca todo el proyecto con un solo comando: el backend (Docker Compose)
# y garita_controller.py (el orquestador de la garita fisica).
#
# garita_controller.py NO corre dentro de Docker a proposito: en Windows,
# Docker Desktop no tiene acceso directo a la webcam USB sin pasos extra
# fragiles (usbipd-win + WSL2, que se rompen cada vez que reconectas el USB).
#
# Cierra la ventana de vista previa con ESC para terminar garita_controller.py
# (el stack de Docker se queda corriendo; usa "docker compose down" aparte).

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Set-Location $root
Copy-Item .env.example .env -Force
Write-Host "Levantando Docker Compose (backend completo)..."
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
    Write-Warning "parking-service no respondio en 120s; se intenta lanzar garita_controller.py de todas formas (revisa 'docker compose logs' si falla)."
}

Set-Location (Join-Path $root "iot\esp32")
Write-Host "Instalando dependencias de Python (si faltan)..."
python -m pip install -r requirements.txt --quiet
# opencv-python se instala aparte: si se instala junto con ultralytics, pip a
# veces deja opencv-python-headless (sin ventanas) y rompe la vista previa
# en vivo (cv2.imshow).
python -m pip install opencv-python --quiet

Write-Host "Lanzando garita_controller.py (ventana de vista previa; ESC para cerrarla)..."
python garita_controller.py
