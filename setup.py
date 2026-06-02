import sqlite3

def crear_estructura():
    conn = sqlite3.connect('cine.db')
    cursor = conn.cursor()

    print("🏗️ Configurando el almacén de datos...")
    
    # Eliminamos la tabla si existía una versión antigua mal hecha
    cursor.execute("DROP TABLE IF EXISTS peliculas")
    
    # Creamos la tabla con el UNIQUE en el título para evitar dobles nombres
    cursor.execute('''
        CREATE TABLE peliculas (
            id_tmdb INTEGER PRIMARY KEY, 
            titulo TEXT NOT NULL,
            genero TEXT NOT NULL,
            poster TEXT,
            puntuacion FLOAT,
            sinopsis TEXT,
            fecha TEXT  -- <--- AQUÍ GUARDAREMOS EL AÑO
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Base de datos 'cine.db' creada con éxito y protegida contra duplicados.")

if __name__ == "__main__":
    crear_estructura()