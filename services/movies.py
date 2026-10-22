import sqlite3
import unicodedata

import pandas as pd
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


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
                            max_df=0.6)  # Ignora palabras que salen en más del 80% de las pelis
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
    sim_scores = sim_scores[1:limite + 1]

    # 5. Devolvemos los datos de las elegidas
    indices_pelis = [i[0] for i in sim_scores]
    return df.iloc[indices_pelis].to_dict('records')
