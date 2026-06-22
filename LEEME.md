# Proyecto TFG: SPECTRA - AutoML Distribuido (Local Training / Remote LLM)

**Autor/a**: Carlota Santiago
**Titulación**: Ingeniería Informática
**Institución**: Universidad de Vigo
**Fecha**: Junio 2026

## 1. Descripción del Proyecto

SPECTRA es una plataforma de **AutoML Distribuido** que divide la carga de trabajo entre una evaluación estadística local (Local Training) y la orquestación semántica mediante un Modelo de Lenguaje Grande (Remote LLM). 

El sistema está diseñado para:
1. Analizar datasets y extraer un perfil estadístico y semántico (TOON Dossier).
2. Determinar la dependencia entre múltiples objetivos (Targets) detectando ausencias estructurales (MNAR) y definiendo estrategias complejas como `GatedChain`, `ClassifierChain`, `RegressorChain`, `HybridChain` o `MultiOutput`.
3. Utilizar el contexto semántico con un orquestador LLM para generar scripts de entrenamiento óptimos.
4. Ejecutar de forma segura el entrenamiento en un entorno aislado (Sandbox/Docker).
5. Aplicar un bucle cerrado de autorreparación (Self-Healing) guiado por LLM ante errores de compilación o ejecución.

## 2. Contenido del Pendrive / Directorio de Entrega

La entrega digital de este proyecto se estructura de la siguiente manera:

* **`/doc`**:
  * `Documentación.pdf`: Memoria principal del TFG con la fundamentación teórica, análisis de requisitos, diseño del sistema, manual de usuario y conclusiones.

* **`Código fuente`**:
  * `/services/backend`: Contiene la lógica principal de Python, el generador de perfiles estadísticos (TOON), el gestor de orquestación, el entorno Sandbox y el bucle de Auto-Healing.
  * `/services/frontend`: Contiene la interfaz gráfica web de usuario mediante la cual se carga el dataset y se visualizan los scripts de entrenamiento y logs.
  * `docker-compose.yml`: Fichero de orquestación local para levantar los servicios del ecosistema.
  * `env`: Fichero con las variables de entorno de base.

* **`/dist`**:
  * Carpeta que contiene los archivos instalables y scripts de despliegue directo para montar SPECTRA en otra máquina, así como las dependencias paquetizadas (Ver la sección "Sobre los Distribuibles" más abajo).

## 3. Requisitos Previos e Instalación

Para ejecutar SPECTRA desde el código fuente es necesario disponer de:
- **Docker y Docker Compose**: Para levantar los entornos Sandbox y aislar el backend/frontend.
- **Python 3.12**: Si se desea ejecutar el backend en modo local o de desarrollo.
- **Node.js & NPM**: Para compilar e iniciar el servidor de desarrollo del Frontend.
- **Ollama**: (O acceso a una API de LLM equivalente) Para proveer la inteligencia al modelo orquestador.

### Despliegue Rápido:
El proyecto incluye scripts interactivos que comprueban las dependencias, descargan la última imagen del Sandbox, configuran los entornos virtuales e inician todos los servicios en segundo plano automáticamente.

### Opción A: Sistemas Linux / macOS (`scriptLinux.sh`)
1. Abre una terminal en la raíz de `Código fuente`.
2. Otorga permisos de ejecución al script si es necesario:
   ```bash
   chmod +x scriptLinux.sh 
   ```bash
3. Ejecuta el script:
  ```bash
  ./scriptLinux.sh
  ```bash

### Opción B: Sistemas Windows (`scriptWindows.bat`)
1. Asegúrate de tener **Docker Desktop** abierto y activo.
2. Haz doble clic sobre el archivo `scriptWindows.bat` o ejecútalo desde la consola de comandos (`cmd`) en la raíz del proyecto.


## 5. Acceso al Sistema

Una vez finalizada la ejecución de cualquiera de los dos scripts, los servicios de SPECTRA quedarán distribuidos y disponibles en los siguientes endpoints locales:

* **Interfaz de Usuario (Frontend)**: [http://localhost:5173](http://localhost:5173)
* **API REST del Sistema (Backend)**: [http://localhost:8001](http://localhost:8001)
* **Documentación Interactiva de la API (Swagger)**: [http://localhost:8001/docs](http://localhost:8001/docs)


## 6. Notas Adicionales

* **Aislamiento de Procesos (Sandbox)**: El entrenamiento real de los modelos de Machine Learning generados por el LLM no ocurre en la máquina nativa; se despacha de forma aislada dentro del contenedor `spectra-training-service` descargado durante el inicio mediante Docker.
* **Manual de Operación**: Cualquier duda sobre los flujos visuales de carga de datos (*Data Discovery*, selección de targets protegidos, etc.) está detallada rigurosamente en el capítulo **"Manual de Usuario"** de la memoria del TFG (`Documentación.pdf`).
