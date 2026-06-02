import sqlite3
import unicodedata
import requests
from google import genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import DirectoryReadTool, FileReadTool, EXASearchTool
from crewai.tools import tool
from dotenv import load_dotenv


load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
os.environ["GEMINI_API_VERSION"] = "v1"



def conectar():
    return sqlite3.connect('cine.db')

def normalizar(texto):
    texto = texto.lower()
    return "".join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).strip()


def filtrar_por_genero(termino_buscado):
    conn = conectar()
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # Traemos todo
    cursor.execute("SELECT * FROM peliculas") 
    todas = cursor.fetchall()
    conn.close()

    if not termino_buscado:
        return []

    busqueda_limpia = normalizar(termino_buscado)
    lista_final = []

    for fila_sqlite in todas:
        # 1. Convertimos a diccionario real para evitar problemas con sqlite3.Row
        peli = dict(fila_sqlite)
        
        # Si la columna 'reparto' no existe, devolverá "" en lugar de petar
        genero = normalizar(str(peli.get('genero') or ""))
        titulo = normalizar(str(peli.get('titulo') or ""))
        sinopsis = normalizar(str(peli.get('sinopsis') or ""))
        reparto = normalizar(str(peli.get('reparto') or ""))
        director = normalizar(str(peli.get('director') or ""))

        # 3. Buscamos en todos los campos
        if (busqueda_limpia in genero or 
            busqueda_limpia in titulo or 
            busqueda_limpia in sinopsis or 
            busqueda_limpia in reparto or 
            busqueda_limpia in director):
            
            lista_final.append(peli)

    return sorted(lista_final, key=lambda x: x.get('puntuacion', 0), reverse=True)


@tool("consultar_cine_db")
def consultar_cine_db(termino: str):
    """
    Busca películas por género, título, actor, director o palabras clave.
    """
    import sqlite3
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


def obtener_info_extra_api(id_tmdb, token):
    headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
    
    # 1. Sacamos Créditos (Director y Reparto)
    url_credits = f"https://api.themoviedb.org/3/movie/{id_tmdb}/credits?language=es-ES"
    res_c = requests.get(url_credits, headers=headers).json()
    director = next((p['name'] for p in res_c.get('crew', []) if p['job'] == 'Director'), "Desconocido")
    actores = [p['name'] for p in res_c.get('cast', [])[:5]]

    # 2. Sacamos Plataformas
    url_prov = f"https://api.themoviedb.org/3/movie/{id_tmdb}/watch/providers"
    res_p = requests.get(url_prov, headers=headers).json()
    espana = res_p.get('results', {}).get('ES', {})
    plataformas = [p['provider_name'] for p in espana.get('flatrate', [])]

    return director, actores, plataformas

def obtener_recomendaciones_pro(lista_generos, titulos_favoritos, salto=0):
    conn = conectar()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    favoritos_limpios = [t.strip() for t in titulos_favoritos if t.strip()]
    
    placeholders_gen = ', '.join(['?'] * len(lista_generos))
    
    # Si no hay favoritos, evitamos que la query falle
    if favoritos_limpios:
        placeholders_fav = ', '.join(['?'] * len(favoritos_limpios))
        filtro_favoritos = f"AND titulo NOT IN ({placeholders_fav})"
    else:
        filtro_favoritos = ""
    
    query = f"""
        SELECT DISTINCT 
            id_tmdb, 
            titulo, 
            genero, 
            poster, 
            puntuacion, 
            sinopsis, 
            fecha,
            COALESCE(director, 'Desconocido') AS director,
            COALESCE(reparto, 'Desconocido') AS reparto
        FROM peliculas 
        WHERE genero IN ({placeholders_gen})
        {filtro_favoritos}
        ORDER BY RANDOM()
        LIMIT 12
    """
    
    params = lista_generos + favoritos_limpios
    cursor.execute(query, params)
    
    filas = cursor.fetchall()
    conn.close()
    
    return [dict(f) for f in filas]

def buscar_peli_por_nombre(nombre):
    conn = conectar()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Buscamos parecido (LIKE) por si no escribe el nombre exacto
    cursor.execute("SELECT genero FROM peliculas WHERE titulo LIKE ? LIMIT 1", (f"%{nombre}%",))
    res = cursor.fetchone()
    conn.close()
    return dict(res) if res else None

# 1. Configuración de la IA

def recomendacion_emocional_ia(frase_usuario):
    # Prompt evolucionado: le pedimos géneros específicos
    prompt = f"""
    Eres un experto en cine. El usuario dice: "{frase_usuario}"
    
    1. Genera un párrafo de máximo 20 palabras con términos que aparecerían en la SINOPSIS de una película ideal para él.
    2. Identifica los 2 géneros más probables de esta lista: 
       Acción, Drama, Animación, Ciencia Ficción, Terror, Romance, Thriller, Fantasía, Crimen, Comedia.

    Responde con este formato exacto:
    DESCRIPCION: [tu párrafo]
    GENEROS: [genero1, genero2]
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        texto_ia = response.text
        # Extraemos la descripción y los géneros usando partición de texto
        descripcion = texto_ia.split("DESCRIPCION:")[1].split("GENEROS:")[0].strip().lower()
        generos_raw = texto_ia.split("GENEROS:")[1].strip().replace("[", "").replace("]", "")
        lista_generos = [g.strip() for g in generos_raw.split(",")]

        print(f"DEBUG: Buscando por '{descripcion}' en géneros {lista_generos}")
        
        return buscar_en_bd(descripcion, lista_generos)

    except Exception as e:
        print(f"Error con la IA: {e}")
        return []

def buscar_en_bd(descripcion, generos_ia):
    conn = conectar()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Limpieza de palabras de relleno
    stopwords = {'una', 'trama', 'de', 'con', 'en', 'y', 'el', 'la', 'que', 'los', 'un', 'para', 'las', 'del', 'personajes', 'situaciones'}
    palabras = [p for p in descripcion.split() if len(p) > 3 and p not in stopwords]
    
    # Construcción de la relevancia por palabras clave
    condiciones_keywords = " + ".join([f"(case when sinopsis LIKE ? then 5 else 0 end)" for _ in palabras])
    
    # Construcción de la prioridad por géneros (dinámica)
    # Si la peli es de uno de los géneros que dijo la IA, le damos 100 puntos extra
    placeholders_gen = ", ".join(["?" for _ in generos_ia])
    
    query = f"""
        SELECT *, ({condiciones_keywords}) as relevancia
        FROM peliculas 
        WHERE relevancia > 0
        ORDER BY 
            (CASE WHEN genero IN ({placeholders_gen}) THEN 100 ELSE 0 END) DESC,
            relevancia DESC, 
            puntuacion DESC
        LIMIT 6
    """
    
    params = [f"%{p}%" for p in palabras] + generos_ia
    cursor.execute(query, params)
    filas = cursor.fetchall()
    conn.close()
    
    return [dict(f) for f in filas]

def obtener_recomendaciones_ml(id_peli_actual, limite=3):
    conn = sqlite3.connect('cine.db')
    # Traemos todas las pelis para comparar
    df = pd.read_sql_query("SELECT * FROM peliculas", conn)
    conn.close()

    if id_peli_actual not in df['id_tmdb'].values:
        return []

    # 1. Vectorización: Convertimos texto en una matriz de números
    # 'stop_words' ignora palabras vacías como "el", "la", "de"
    # Lista básica de palabras a ignorar en español
    palabras_irrelevantes = [
    'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'pero', 'si', 'no', 'con', 'por', 
    'para', 'en', 'de', 'del', 'al', 'que', 'es', 'son', 'fue', 'su', 'sus', 'este', 'esta', 'ese', 
    'aquél', 'todo', 'todos', 'sobre', 'tan', 'donde', 'cuando', 'quien', 'cada', 'bien', 'también', 
    'propios', 'le', 'había', 'era', 'muy', 'mismo', 'esta', 'se', 'ha', 'una', 'una', 'lo', 'como', 'más'
]
    df['metadata'] = df['sinopsis'].fillna('') + " " + df['genero'].fillna('')

    tfidf = TfidfVectorizer(stop_words=palabras_irrelevantes,
                            ngram_range=(1, 2), 
                            min_df=2,
                            max_df=0.6) # Ignora palabras que salen en más del 80% de las pelis
    tfidf_matrix = tfidf.fit_transform(df['metadata'])

    # 2. Cálculo de Similitud del Coseno (compara qué tan cerca está cada vector de otro)
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    # 3. Buscamos el índice de la peli que el usuario está viendo
    idx = df.index[df['id_tmdb'] == id_peli_actual][0]
    genero_actual = df.iloc[idx]['genero']

    # 4. Ordenamos las pelis por similitud y descartamos la primera (que es ella misma)
    sim_scores = list(enumerate(cosine_sim[idx]))
    scores_con_bonus = []
    for i, puntuacion in sim_scores:
        # Si el género es el mismo, le damos un empujón de 0.2 (20% de afinidad extra)
        if df.iloc[i]['genero'] == genero_actual:
            puntuacion += 0.4
        scores_con_bonus.append((i, puntuacion))
    # --------------------------------------------

    # 4. Ordenamos usando la nueva lista con bonus
    sim_scores = sorted(scores_con_bonus, key=lambda x: x[1], reverse=True)
    
    # Descartamos la primera (ella misma) y cogemos el límite
    sim_scores = sim_scores[1:limite+1] 
    
    # 5. Devolvemos los datos de las elegidas
    indices_pelis = [i[0] for i in sim_scores]
    return df.iloc[indices_pelis].to_dict('records')


## Agente para recomendación emocional


def obtener_recomendacion_agente(sentimiento_usuario):
    # 1. Definimos al Agente dentro de la función
    analista = Agent(
        role='Psicólogo Experto en Cine',
        goal='Analizar el sentimiento y recomendar 3 géneros y 3 películas específicas.',
        backstory="Eres un experto en psicología aplicada al cine. Analizas emociones y das soluciones cinematográficas.",
        llm="gemini/gemini-2.5-flash",
        verbose=False,
        tools=[consultar_cine_db]
    )

    # 2. Definimos la Tarea
    tarea = Task(
        description=f'El usuario dice: "{sentimiento_usuario}". Decide qué géneros necesita y menciona 3 películas famosas que encajen.',
        expected_output='Un texto breve con los géneros, las pelis y el porqué.',
        agent=analista
    )

    # 3. Ejecutamos la "Tripulación"
    crew = Crew(agents=[analista], tasks=[tarea])
    
    try:
        resultado = crew.kickoff()
        return str(resultado)
    except Exception as e:
        return f"La IA está descansando un momento... (Error: {e})"


# Configuramos la herramienta para que lea tu archivo local dentro de Docke

def ejecutar_negociacion(gusto_amigo_1, gusto_amigo_2):
    # AGENTE 1: El experto en el Amigo 1
    abogado_1 = Agent(
        role='Defensor del Amigo 1',
        goal=f'Extraer lo mejor de los gustos: {gusto_amigo_1}',
        backstory='Eres un experto en encontrar la esencia de lo que le gusta a la primera persona, en el contexto de la cinematografía.',
        llm="gemini/gemini-2.5-flash",
        allow_delegation=False
    )

    # AGENTE 2: El experto en el Amigo 2
    abogado_2 = Agent(
        role='Defensor del Amigo 2',
        goal=f'Extraer lo mejor de los gustos: {gusto_amigo_2}',
        backstory='Eres un experto en defender los intereses de la segunda persona, en el contexto de la cinematografía.',
        llm="gemini/gemini-2.5-flash",
        allow_delegation=False
    )

    # AGENTE 3: El Juez (El único que usa la herramienta SQL)
    juez = Agent(
        role='Juez de Paz Cinematográfico',
        goal='Buscar en la base de datos una película que sea el consenso perfecto.',
        backstory='Eres un mediador experto. Sabes encontrar películas que mezclan géneros opuestos.',
        tools=[consultar_cine_db],
        llm="gemini/gemini-2.5-flash",
        verbose=True
    )

    # DEFINICIÓN DE TAREAS
    t1 = Task(
        description=f'Analizad los gustos del Amigo 1: "{gusto_amigo_1}" y proponed 3 palabras clave que los unan.',
        expected_output='Una lista de 3 conceptos híbridos (ej: "Comedia Negra", "Thriller Psicológico").',
        agent=abogado_1 # El primer abogado inicia la propuesta
    )

    t2 = Task(
        description=f'Analiza en profundidad los gustos del Amigo 2: "{gusto_amigo_2}". Desglosa qué elementos narrativos, tonos y subgéneros busca implícitamente.',
        expected_output='Un informe técnico con los pilares cinematográficos esenciales para el Amigo 2.',
        agent=abogado_2
    )

    t3 = Task(
        description='Usa las palabras clave para buscar en la base de datos y elige LA MEJOR película de consenso.',
        expected_output='Título de la película, género y una breve explicación de por qué convence a ambos.',
        agent=juez
    )

    # LA TRIPULACIÓN
    negociacion_crew = Crew(
        agents=[abogado_1, abogado_2, juez],
        tasks=[t1, t2, t3],
        process=Process.sequential
    )

    return negociacion_crew.kickoff()