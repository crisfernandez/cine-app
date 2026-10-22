## Estructura del Proyecto y Descripción de Archivos

El proyecto está dividido en capas: la interfaz (Streamlit) habla con una API interna (Flask), que a su vez consume la lógica de negocio (`services/`) y los agentes de IA (`agents/`):

### Interfaz y Lógica Principal
* **`interface.py`:** El punto de entrada de la aplicación. Gestiona la interfaz gráfica interactiva con **Streamlit** y consume la API Flask interna vía HTTP (`API_BASE_URL`, por defecto `http://localhost:5000`).
* **`app.py`:** API interna con **Flask** (puerto 5000). Expone los endpoints de películas, recomendaciones y agentes que la interfaz utiliza.
* **`run.py`:** Lanzador único que arranca la API Flask y la interfaz Streamlit a la vez (`python run.py`).

### Lógica de Negocio y Agentes
* **`services/movies.py`:** Toda la lógica de películas: búsqueda en SQLite, datos de TMDB y recomendaciones con scikit-learn (ML).
* **`agents/`:** Agentes de IA con **CrewAI**:
  * `mood.py`: agente de recomendación emocional (pestaña Mood AI).
  * `negotiator.py`: agentes de la negociación entre dos personas (pestaña Negociador).
  * `tools.py`: herramienta SQL que usan los agentes para consultar la base de datos.

### Gestión de Base de Datos 
* **`setup.py`:** Script de inicialización. Se encarga de borrar versiones corruptas previas y crear la estructura limpia de la tabla `peliculas` en SQLite (`cine.db`), definiendo las columnas necesarias (título, género, sinopsis, póster, puntuación, año).
* **`importar_pelis.py`:** Conecta de forma masiva con la API de **TMDB**, recorre múltiples páginas por género, extrae los datos principales de las películas y se conecta a la sección de créditos para obtener el director y el reparto principal. Cuenta con lógica de actualización para evitar duplicados.

### Historial de Desarrollo (Módulo `Legacy/`)
*Esta carpeta almacena los scripts independientes utilizados durante la fase de investigación y pruebas antes de la unificación del sistema:*
* **`Legacy/setup.py`:** Primera versión de la estructura de la base de datos.
* **`Legacy/notas.py`:** Script de mantenimiento utilizado para sincronizar, normalizar y redondear a un decimal las calificaciones de las películas consumiendo la API de TMDB.
* **`Legacy/posters.py`:** Script auxiliar que añade de forma masiva los enlaces URL de los pósters oficiales de las imágenes de TMDB a los registros existentes.
* **`Legacy/reparto.py`:** Script de migración estructural que altera la base de datos para inyectar de forma segura las columnas de `reparto` y `director`.
* **`Legacy/app.py`:** Una API intermedia desarrollada con **Flask** para servir los datos en formato JSON. Quedó obsoleta al conectar Streamlit de forma directa y nativa a la lógica de `database.py`.

### Infraestructura y Despliegue
* **`Dockerfile`:** Define la receta de construcción del contenedor de Docker (imagen base de Python, instalación de dependencias y exposición de puertos). El `CMD` ejecuta `run.py`.
* **`docker-compose.yml`:** Gestiona el arranque automatizado de los contenedores locales para aislar el entorno de desarrollo con un solo comando.

