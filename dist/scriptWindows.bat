@echo off
echo ==============================================
echo Iniciando SPECTRA - AutoML Distribuido
echo ==============================================

echo [1/5] Comprobando dependencias (Docker, Python, Node)...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker no esta corriendo. Por favor, inicia Docker Desktop.
    pause
    exit /b
)

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    pause
    exit /b
)

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js no esta instalado.
    pause
    exit /b
)
echo [OK] Dependencias comprobadas.

echo [2/5] Descargando y ejecutando contenedor Sandbox (Training Service)...
docker pull ghcr.io/jorgercid/spectra-training-service:latest
docker image inspect ghcr.io/jorgercid/spectra-training-service:latest >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] La imagen de Docker no existe localmente.
    pause
    exit /b
)
:: Se abre una nueva terminal para que docker se quede ejecutando sin bloquear el script principal
start "SPECTRA - Training Service Docker" cmd /c "docker compose up"

echo [3/5] Configurando Entorno Virtual Python y Backend local...
cd services\backend
if not exist ".venv\" (
    echo Creando entorno virtual...
    python -m venv .venv
)
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] El entorno virtual no existe o no se creo correctamente.
    pause
    exit /b
)
call .venv\Scripts\activate.bat
echo Instalando dependencias de Python...
pip install -r requirements.txt
:: Asumiendo que es una app FastAPI (main:app), abrimos otra terminal para el backend
start "SPECTRA - Backend Server" cmd /c "call .venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000"
cd ..\..

echo [4/5] Configurando Frontend...
cd services\frontend
echo Instalando dependencias de Node...
call npm install
:: Abrimos otra terminal para el servidor de desarrollo de Vite
start "SPECTRA - Frontend Vite" cmd /c "npm run dev"
cd ..\..

echo ==============================================
echo [5/5] ¡Todo levantado con exito!
echo El frontend estara disponible en http://localhost:5173
echo ==============================================
pause
