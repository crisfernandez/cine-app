import sqlite3

from crewai.tools import tool


@tool("consultar_cine_db")
def consultar_cine_db(termino: str):
    """
    Busca películas por género, título, actor, director o palabras clave.
    """
    conn = sqlite3.connect('cine.db')
    cursor = conn.cursor()

    # Limpiamos el término
    busqueda = f"%{termino.strip()}%"

    # Query que busca en múltiples columnas a la vez
    query = """
        SELECT titulo, genero, sinopsis
        FROM peliculas
        WHERE genero LIKE ?
           OR titulo LIKE ?
           OR sinopsis LIKE ?
        LIMIT 6
    """

    cursor.execute(query, (busqueda, busqueda, busqueda))
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        return f"No encontré nada relacionado con '{termino}'. Prueba con otro nombre o género."

    respuesta = f"Resultados para '{termino}':\n"
    for r in resultados:
        respuesta += f"- **{r[0]}** ({r[1]}): {r[2][:120]}...\n"

    return respuesta
