import os
import sqlite3
import requests
from dotenv import load_dotenv

# 1. TU CONFIGURACIÓN
load_dotenv()
TMDB_TOKEN = os.getenv("TMDB_TOKEN")

def preparar_y_rellenar():
    conn = sqlite3.connect('cine.db')
    cursor = conn.cursor()

    # --- PASO 1: Asegurar que la columna existe ---
    try:
        cursor.execute("ALTER TABLE peliculas ADD COLUMN poster TEXT")
        print("✅ Columna 'poster' creada.")
    except sqlite3.OperationalError:
        print("ℹ️ La columna 'poster' ya existía, continuando...")

    # --- PASO 2: Obtener las películas ---
    cursor.execute("SELECT id, titulo FROM peliculas")
    peliculas = cursor.fetchall()

    # --- PASO 3: Buscar en la API y actualizar ---
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_TOKEN}"
    }

    for id_peli, titulo in peliculas:
        print(f"Buscando póster para: {titulo}...", end=" ")
        
        url_api = f"https://api.themoviedb.org/3/search/movie?query={titulo}&language=es-ES"
        
        try:
            res = requests.get(url_api, headers=headers)
            datos = res.json()
            
            if datos.get('results'):
                path = datos['results'][0]['poster_path']
                url_poster = f"https://image.tmdb.org/t/p/w500{path}"
                
                # Guardamos en la DB
                cursor.execute("UPDATE peliculas SET poster = ? WHERE id = ?", (url_poster, id_peli))
                print("✅")
            else:
                print("❌ (No encontrado)")
        except Exception as e:
            print(f"⚠️ Error: {e}")

    conn.commit()
    conn.close()
    print("\n✨ Proceso finalizado. ¡Base de datos lista!")

if __name__ == "__main__":
    preparar_y_rellenar()