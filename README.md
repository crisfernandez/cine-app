## Estructura del Proyecto y Descripción de Archivos

El proyecto está dividido en módulos que separan la interfaz de usuario, la lógica de los agentes de IA y los scripts de mantenimiento de datos:

### Interfaz y Lógica Principal
* **`interface.py`:** El punto de entrada de la aplicación. Gestiona la interfaz gráfica interactiva con **Streamlit**, captura las entradas de texto con las preferencias de los usuarios y muestra el veredicto final de la mediación en tiempo real.
* **`database.py`:** Gestiona la base de datos, la IA y las recomendaciones mediante una serie de funciones.

### Gestión de Base de Datos (Módulo `database/`)
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
* **`Dockerfile`:** Define la receta de construcción del contenedor de Docker (imagen base de Python, instalación de dependencias y exposición de puertos).
* **`docker-compose.yml`:** Gestiona el arranque automatizado de los contenedores locales para aislar el entorno de desarrollo con un solo comando.
* **`.gitignore`:** El escudo de seguridad del repositorio. Evita que archivos privados como las variables de entorno (`.env`), la base de datos local (`cine.db`) o la caché de Python (`__pycache__`) se suban públicamente a GitHub.
