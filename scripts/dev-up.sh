#!/usr/bin/env bash
# Equivalente a dev-up.ps1 para Mac/Linux: arranca todo el proyecto con un
# solo comando. Docker Compose levanta el backend completo, incluido
# garita-controller (el orquestador de la garita fisica), que ahora corre
# como un microservicio mas del stack (usa una camara IP para la deteccion
# de placa, configurable en .env via PLATE_CAMERA_SOURCE).
#
# Uso: ./scripts/dev-up.sh

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Se creo .env desde .env.example (primera vez)."
else
    echo ".env ya existe, no se toca (para no perder ajustes ya hechos)."
fi

echo "Levantando Docker Compose (backend completo, incluye garita-controller)..."
docker compose up -d --build

echo "Esperando a que parking-service responda..."
deadline=$((SECONDS + 120))
ready=false
while [ $SECONDS -lt $deadline ]; do
    if curl -sf -o /dev/null "http://localhost:8004/health"; then
        ready=true
        break
    fi
    sleep 2
done
if [ "$ready" = true ]; then
    echo "Backend listo."
else
    echo "AVISO: parking-service no respondio en 120s (revisa 'docker compose logs')." >&2
fi

garita_port="$(grep -m1 '^GARITA_CONTROLLER_PORT=' .env | cut -d= -f2)"
garita_port="${garita_port:-8010}"
echo "Vista en vivo de la garita: http://localhost:${garita_port}/"
echo "Configura PLATE_CAMERA_SOURCE en .env con la URL de tu camara IP (rtsp://... o http://...) y 'docker compose up -d --build garita-controller' de nuevo si la cambias."
