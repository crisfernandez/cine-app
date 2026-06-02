import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()
TMDB_TOKEN = os.getenv("TMDB_TOKEN")

conn = sqlite3.connect('cine.db')
cursor = conn.cursor()


try:
    # Añadimos la columna para los actores
    cursor.execute("ALTER TABLE peliculas ADD COLUMN reparto TEXT")
    # Añadimos la columna para el director (ya que estamos, ¡es muy útil!)
    cursor.execute("ALTER TABLE peliculas ADD COLUMN director TEXT")
    conn.commit()
    print("✅ Columnas 'reparto' y 'director' añadidas con éxito.")
except sqlite3.OperationalError:
    # Esto evita que el código falle si vuelves a ejecutarlo y las columnas ya existen
    print("⚠️ Las columnas ya existían, saltando el paso.")
finally:
    conn.close()