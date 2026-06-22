#!/bin/bash

echo "=============================================="
echo "Iniciando SPECTRA - AutoML Distribuido"
echo "=============================================="

echo "[1/5] Comprobando dependencias (Docker, Python, Node)..."
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker no esta instalado o corriendo."
    exit 1
fi

if ! command -v python3.12 &> /dev/null; then
    echo "[ERROR] Python 3.12 no esta instalado."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js no esta instalado."
    exit 1
fi
echo "[OK] Dependencias comprobadas."

echo "[2/5] Descargando y ejecutando contenedor Sandbox (Training Service)..."
docker pull ghcr.io/jorgercid/spectra-training-service:latest
if ! docker image inspect ghcr.io/jorgercid/spectra-training-service:latest &> /dev/null; then
    echo "[ERROR] La imagen de Docker no existe localmente."
    exit 1
fi
# Corremos el contenedor en segundo plano (-d) para no bloquear la terminal
docker compose up -d

echo "[3/5] Configurando Entorno Virtual Python y Backend local..."
cd services/backend
if [ ! -d ".venv" ]; then
    echo "Creando entorno virtual..."
    python3.11 -m venv .venv
fi
if [ ! -d ".venv" ] || [ ! -f ".venv/bin/activate" ]; then
    echo "[ERROR] El entorno virtual no existe o no se creó correctamente."
    exit 1
fi
source .venv/bin/activate
echo "Instalando dependencias de Python..."
pip install -r requirements.txt
# Lanzamos FastAPI en segundo plano
uvicorn main:app --host 0.0.0.0 --port 8000 &
cd ../..

echo "[4/5] Configurando Frontend..."
cd services/frontend
echo "Instalando dependencias de Node..."
npm install
# Lanzamos Vite en segundo plano
npm run dev &
cd ../..

echo "=============================================="
echo "[5/5] ¡Todo levantado con éxito!"
echo "El frontend estará disponible en http://localhost:5173"
echo "=============================================="
