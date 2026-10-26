# MovieAI Pro — Arquitectura y Descripción

Aplicación de recomendación de películas con interfaz web (Streamlit), API interna (Flask) y agentes de IA (CrewAI + Gemini).

---

## Cómo ejecutarla

```bash
pip install -r requirements.txt
python run.py
```

Esto arranca dos procesos:
- **API Flask** en `http://localhost:5000`
- **Interfaz Streamlit** en `http://localhost:8501` (se abre en el navegador)

Variables necesarias en `.env`:
```
TMDB_TOKEN=...          # API de The Movie Database (poblar BD + detalles en vivo)
GEMINI_API_KEY=...      # API de Google Gemini (cerebro de los agentes)
```

---

## Esquema de comunicación

```
Chrome (usuario)
   │
   ▼
interface.py (Streamlit :8501)  — solo pinta la UI, no toca BD ni IA
   │  HTTP (requests)
   ▼
app.py (Flask API :5000)        — router: recibe, valida, delega
   │                    │
   ▼                    ▼
services/movies.py     agents/ (CrewAI)
(datos, ML, TMDB)      (Gemini + tool SQL)
   │                    │
   ▼                    ▼
cine.db (SQLite)  ◄── agents/tools.py (SELECT para los agentes)
```

---

## Estructura del proyecto

### Interfaz y Lógica Principal
* **`interface.py`:** Punto de entrada. Interfaz con **Streamlit**; consume la API Flask vía HTTP (`API_BASE_URL`).
* **`app.py`:** API interna con **Flask** (puerto 5000). Expone los endpoints de películas, recomendaciones y agentes.
* **`run.py`:** Lanzador único que arranca Flask y Streamlit a la vez.

### Lógica de Negocio y Agentes
* **`services/movies.py`:** Búsqueda en SQLite, datos en vivo de TMDB y recomendaciones con scikit-learn (TF-IDF + similitud del coseno).
* **`agents/`:** Agentes de IA con **CrewAI**:
  * `mood.py`: agente de recomendación emocional (pestaña Mood AI). Un agente "Psicólogo Experto en Cine" con tool SQL.
  * `negotiator.py`: 3 agentes (2 abogados + juez) en proceso secuencial (pestaña Negociador). Solo el juez usa la tool SQL.
  * `tools.py`: herramienta `consultar_cine_db` (SELECT LIKE) que usan los agentes para consultar `cine.db`.

### Gestión de Base de Datos
* **`setup.py`:** Inicialización. Borra la tabla `peliculas` si existe y la crea limpia en `cine.db`.
* **`importar_pelis.py`:** Importación masiva desde la API de **TMDB**: recorre páginas por género, extrae datos, créditos (director y reparto) y evita duplicados.

### Historial de Desarrollo (`legacy/`)
Scripts independientes de la fase de investigación, no se usan en la versión actual:
* **`legacy/notas.py`:** Sincroniza y normaliza puntuaciones consumiendo TMDB.
* **`legacy/posters.py`:** Añade masivamente URLs de pósters de TMDB a registros existentes.
* **`legacy/reparto.py`:** Migra las columnas `reparto` y `director` a la tabla.

### Infraestructura y Despliegue
* **`Dockerfile`:** Imagen Python 3.11-slim; el `CMD` ejecuta `run.py`.
* **`docker-compose.yml`:** Arranque automatizado del contenedor con un solo comando.

---

## Endpoints de la API (`app.py`)

| Endpoint | Método | Descripción | Consumidor |
|---|---|---|---|
| `/api/salud` | GET | Heartbeat para `run.py` | Lanzador |
| `/api/peliculas?termino=X` | GET | Busca por género, título, sinopsis, reparto o director | Búsqueda lateral |
| `/api/peliculas/<id>/detalles` | GET | Director, actores y plataformas en España (TMDB en vivo) | Diálogo "Ficha Técnica" |
| `/api/peliculas/<id>/similares` | GET | 3 películas similares (TF-IDF + coseno) | Recomendaciones ML del diálogo |
| `/api/recomendaciones` | POST | Cartelera personalizada: `generos` + `favoritos`, SQL `RANDOM()` | Pestaña Recomendador |
| `/api/agentes/mood` | POST | Texto → agente CrewAI → recomendación | Pestaña Mood AI |
| `/api/agentes/negociacion` | POST | 2 gustos → 3 agentes → veredicto | Pestaña Negociador |

---

## APIs externas utilizadas

### TMDB (The Movie Database)
* **Poblado de la BD** (`importar_pelis.py`, script manual): trae título, género, sinopsis, puntuación, año, póster, director y reparto.
* **En vivo** (`services/movies.py → obtener_info_extra_api`): al abrir la ficha técnica, consulta director, actores y plataformas de suscripción en España. Son 2 llamadas por apertura (créditos + watch providers).

### Gemini (Google)
* Usado por **CrewAI** como LLM (`gemini/gemini-2.5-flash`): analiza sentimientos o gustos, razona y decide cuándo usar la tool SQL. Sin esta API, Mood AI y Negociador no funcionan.
* La clave se carga en `agents/__init__.py` (`GOOGLE_API_KEY` + `GEMINI_API_VERSION`).

---
