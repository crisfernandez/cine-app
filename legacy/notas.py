import os
import sqlite3
import requests
import time
from dotenv import load_dotenv

load_dotenv()
TMDB_TOKEN = os.getenv("TMDB_TOKEN")

def sincronizar():
    conn = sqlite3.connect('cine.db')
    cursor = conn.cursor()

    # Seleccionamos todas las pelis para actualizar sus notas
    cursor.execute("SELECT id, titulo FROM peliculas")
    peliculas = cursor.fetchall()
    
    headers = {"Authorization": f"Bearer {TMDB_TOKEN}", "accept": "application/json"}
    
    print(f"🔄 Iniciando sincronización de {len(peliculas)} películas...")

    for id_peli, titulo in peliculas:
        # Buscamos la película exacta en TMDB
        url = f"https://api.themoviedb.org/3/search/movie?query={titulo}&language=es-ES"
        
        try:
            res = requests.get(url, headers=headers)
            data = res.json()
            results = data.get('results', [])

            if results:
                # Cogemos la nota y la REDONDEAMOS a 1 decimal aquí mismo
                nota_real = results[0].get('vote_average', 0.0)
                nota_formateada = round(nota_real, 1) # <--- Aquí ocurre la magia del decimal
                
                cursor.execute(
                    "UPDATE peliculas SET puntuacion = ? WHERE id = ?", 
                    (nota_formateada, id_peli)
                )
                conn.commit()
                print(f"⭐ {titulo}: {nota_formateada}")
            
            # Pausa para no saturar la API (importante)
            time.sleep(0.2) 
            
        except Exception as e:
            print(f"❌ Error con {titulo}: {e}")

    conn.close()
    print("\n🚀 ¡Todas las notas han sido actualizadas y redondeadas!")

if __name__ == "__main__":
    sincronizar()