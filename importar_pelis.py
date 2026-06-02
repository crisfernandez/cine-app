import os
import sqlite3
import requests
import time
from dotenv import load_dotenv

load_dotenv()
TMDB_TOKEN = os.getenv("TMDB_TOKEN")

# Diccionario de géneros¡
GENEROS_CONFIG = {
    "Acción": 28,
    "Drama": 18,
    "Animación": 16,
    "Ciencia Ficción": 878,
    "Terror": 27,
    "Romance": 10749,
    "Thriller": 53,
    "Fantasía": 14,
    "Crimen": 80,
    "Comedia": 35
}

def importar_todo():
    conn = sqlite3.connect('cine.db')
    cursor = conn.cursor()

    # Cargamos lo que ya tenemos para no duplicar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS peliculas (
            id_tmdb INTEGER PRIMARY KEY,
            titulo TEXT NOT NULL UNIQUE,
            genero TEXT NOT NULL,
            poster TEXT,
            puntuacion REAL DEFAULT 7.0,
            sinopsis TEXT,
            fecha TEXT,
            reparto TEXT,
            director TEXT
        )
    """)
    existentes = {fila[0].lower().strip() for fila in cursor.fetchall()}

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_TOKEN}"
    }

    for nombre_gen, id_gen in GENEROS_CONFIG.items():
        print(f"\n--- 📂 Importando {nombre_gen} (ID: {id_gen}) ---")
        nuevas_en_este_genero = 0
        
        for pagina in range(1, 25): 
            url = (
                f"https://api.themoviedb.org/3/discover/movie?"
                f"with_genres={id_gen}&language=es-ES&page={pagina}&sort_by=popularity.desc"
            )
            
            try:
                res = requests.get(url, headers=headers)
                data = res.json()
                peliculas_api = data.get('results', [])

                for p in peliculas_api:
                    # Extraemos el ID de TMDB para futuras referencias
                    id_api = p.get('id')

                    # Extraemos el título
                    titulo = p['title']

                    ## Extraemos la puntuación
                    puntuacion = p.get('vote_average', 0.0)

                    # Extraemos su fecha de estreno
                    fecha_estreno = p.get('release_date', 'N/A')
                    # Solo nos interesa el año (los primeros 4 caracteres: 2024-05-10 -> 2024)
                    year = fecha_estreno.split("-")[0] if fecha_estreno != 'N/A' else "S/A"

                    # Extraemos el resumen
                    resumen = p.get('overview', 'Sin descripción disponible.')

                    # --- REPARTO Y DIRECTOR ---
                    print(f"Obteniendo créditos para: {titulo}...")
                    url_creditos = f"https://api.themoviedb.org/3/movie/{id_api}/credits?language=es-ES"
                    res_c = requests.get(url_creditos, headers=headers).json()
                    # Sacamos los 8 primeros actores
                    actores = [a['name'] for a in res_c.get('cast', [])[:8]]
                    reparto_txt = ", ".join(actores)
                    # Sacamos el director
                    director_txt = next((m['name'] for m in res_c.get('crew', []) if m['job'] == 'Director'), "Desconocido")
                    
                    # 1. Si la película YA EXISTE, actualizamos su nota
                    if titulo.lower().strip() in existentes:
                        cursor.execute(
                            """UPDATE peliculas 
                            SET puntuacion = ?, reparto = ?, director = ? 
                            WHERE id_tmdb = ?
                        """, (puntuacion, reparto_txt, director_txt, id_api))
                    
                    else:
                        poster_path = p.get('poster_path')
                        url_poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                        
                        cursor.execute("""
                                        INSERT OR IGNORE INTO peliculas (id_tmdb, titulo, genero, poster, puntuacion, sinopsis, fecha) 
                                        VALUES (?, ?, ?, ?, ?, ?, ?)
                                    """, (id_api, titulo, nombre_gen, url_poster, puntuacion, resumen, year))
                        existentes.add(titulo.lower().strip())
                        nuevas_en_este_genero += 1
                
                print(f"Página {pagina} procesada...")
                # Pequeña pausa para no saturar la API 
                time.sleep(0.2)

            except Exception as e:
                print(f"Error en página {pagina}: {e}")
        
        print(f"Total nuevas en {nombre_gen}: {nuevas_en_este_genero}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    importar_todo()