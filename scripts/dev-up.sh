#!/usr/bin/env bash
# Equivalente a dev-up.ps1 para Mac/Linux: arranca todo el proyecto con un
# solo comando, el backend (Docker Compose) y garita_controller.py (el
# orquestador de la garita fisica).
#
# garita_controller.py NO corre dentro de Docker a proposito: Docker Desktop
# (Mac y Windows por igual) corre en una VM y no tiene acceso directo a la
# webcam del host sin pasos extra fragiles. Este script simplemente
# automatiza lanzar ambas partes en orden.
#
# Uso: ./scripts/dev-up.sh
# Cierra la ventana de vista previa con ESC para terminar garita_controller.py
# (el stack de Docker se queda corriendo; usa "docker compose down" aparte).
#
# Nota macOS: la primera vez que corra, macOS va a pedir permiso de camara
# para Terminal/Python (Configuracion del Sistema > Privacidad y seguridad >
# Camara) - si no aparece el prompt, actívalo ahi a mano y vuelve a correr.

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Se creo .env desde .env.example (primera vez)."
else
    echo ".env ya existe, no se toca (para no perder ajustes ya hechos)."
fi

echo "Levantando Docker Compose (backend completo)..."
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
    echo "AVISO: parking-service no respondio en 120s; se intenta lanzar garita_controller.py de todas formas (revisa 'docker compose logs' si falla)." >&2
fi

cd "$root/iot/esp32"
echo "Instalando dependencias de Python (si faltan)..."
python3 -m pip install -r requirements.txt --quiet
# opencv-python se instala aparte: si se instala junto con ultralytics, pip a
# veces deja opencv-python-headless (sin ventanas) y rompe la vista previa
# en vivo (cv2.imshow).
python3 -m pip install opencv-python --quiet

echo "Lanzando garita_controller.py (ventana de vista previa; ESC para cerrarla)..."
python3 garita_controller.py
