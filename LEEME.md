# Proyecto TFG: SPECTRA - AutoML Distribuido (Local Training / Remote LLM)

**Autor/a**: Carlota Santiago
**Titulación**: Ingeniería Informática
**Institución**: Universidad de Vigo (Asumiendo por la plataforma Moovi)
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

* **`/Documentación`**:
  * `Documentación.pdf`: Memoria principal del TFG con la fundamentación teórica, análisis de requisitos, diseño del sistema, manual de usuario y conclusiones.
  * `AutoML_v3.pdf`: Documento técnico complementario sobre la arquitectura detallada.

* **`/Código fuente`**:
  * `/services/backend`: Contiene la lógica principal de Python, el generador de perfiles estadísticos (TOON), el gestor de orquestación, el entorno Sandbox y el bucle de Auto-Healing.
  * `/services/frontend`: Contiene la interfaz gráfica web de usuario mediante la cual se carga el dataset y se visualizan los scripts de entrenamiento y logs.
  * `docker-compose.yml`: Fichero de orquestación local para levantar los servicios del ecosistema.
  * `env`: Fichero con las variables de entorno de base.

* **`/Distribuibles`**:
  * Carpeta que contiene los archivos instalables y scripts de despliegue directo para montar SPECTRA en otra máquina, así como las dependencias paquetizadas (Ver la sección "Sobre los Distribuibles" más abajo).

## 3. Requisitos Previos e Instalación

Para ejecutar SPECTRA desde el código fuente es necesario disponer de:
- **Docker y Docker Compose**: Para levantar los entornos Sandbox y aislar el backend/frontend.
- **Python 3.11+**: Si se desea ejecutar el backend en modo local o de desarrollo.
- **Ollama**: (O acceso a una API de LLM equivalente) Para proveer la inteligencia al modelo orquestador.

### Despliegue Rápido:
1. Clonar o acceder a la carpeta de `/Código fuente`.
2. Renombrar el archivo `env` a `.env` (si procede) y ajustar las URLs de Ollama.
3. Ejecutar `docker-compose up --build` para levantar toda la infraestructura local.
4. Acceder a la interfaz web (puerto por defecto definido en el frontend).

## 4. Notas Adicionales

Cualquier duda sobre el uso de la interfaz gráfica y los flujos de carga de datos (Data Discovery, Selección de targets, etc.) está detallada en el apartado "Manual de Usuario" dentro del `Documentación.pdf`.
