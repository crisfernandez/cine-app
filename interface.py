import os
from dotenv import load_dotenv
import streamlit as st
import requests
import database

load_dotenv()

# 1. CONFIGURACIÓN Y DIÁLOGO

@st.dialog("🎬 Ficha Técnica", width="large")
def mostrar_detalle(peli):
    with st.spinner("Buscando disponibilidad en España..."):
        try:
            TOKEN_TMDB = os.getenv("TMDB_TOKEN")
            # Esta función de tu database.py debe devolver las plataformas
            director_api, reparto_api, plataformas = database.obtener_info_extra_api(peli['id_tmdb'], TOKEN_TMDB)
            _, _, plataformas = database.obtener_info_extra_api(peli['id_tmdb'], TOKEN_TMDB)
        except Exception:
            plataformas = []
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        # Usamos la imagen con seguridad por si falla el póster
        poster = peli['poster'] if peli['poster'] else "https://via.placeholder.com/500x750?text=Sin+Imagen"
        st.image(poster, width='stretch')
        st.metric("Puntuación", f"{peli['puntuacion']} / 10")
        
    with col2:
        st.title(peli['titulo'])
        st.caption(f"📅 Año: {peli.get('fecha', 'N/A')} | 🎭 Género: {peli['genero']}")
        
        # 2. Leemos 'director' y 'reparto' directamente de la DB
        director = peli.get('director', 'Desconocido')
        if director == 'Desconocido' and director_api:
            director = director_api
        else:
            director = director

        reparto_db = peli.get('reparto', 'No disponible')
        if (reparto_db == 'No disponible' or reparto_db == 'Desconocido') and reparto_api:
            reparto = reparto_api
        else:
            reparto = reparto_db

        if isinstance(reparto, list):
            # Si la API nos da una lista real de Python, la unimos limpiamente con comas
            reparto_limpio = ", ".join(reparto)
        else:
            reparto_limpio = (
                str(reparto)
                .replace("[", "")
                .replace("]", "")
                .replace("'", "")
                .replace('"', "")
                .strip()
            )
        
        st.write(f"**🎬 Director:** {director}")
        st.write(f"**👥 Reparto:** {reparto_limpio}")
        
        st.divider()
        st.subheader("Sinopsis")
        st.write(peli.get('sinopsis', "No hay descripción disponible."))
        
        st.divider()

        if plataformas:
            st.success("📺 **Disponible en:** " + " | ".join(plataformas))
        else:
            st.info("ℹ️ No se encontraron plataformas de suscripción en España para esta película.")

    # --- SECCIÓN DE MACHINE LEARNING ---
    st.divider()
    st.subheader("También podría interesarte:")
    
    # Llamamos a la función de ML
    with st.spinner("Buscando películas con tramas similares..."):
        similares = database.obtener_recomendaciones_ml(peli['id_tmdb'])
    
    if similares:
        # Creamos tantas columnas como pelis devuelva el modelo (máximo 3)
        cols_ml = st.columns(len(similares))
        for i, s in enumerate(similares):
            with cols_ml[i]:
                # Imagen con seguridad
                img_s = s['poster'] if s['poster'] else "https://via.placeholder.com/500x750?text=Sin+Imagen"
                st.image(img_s, width='stretch')
                st.caption(f"**{s['titulo']}**")
                
                # Botón para saltar a la peli recomendada
                if st.button("Ver", key=f"ml_det_{s['id_tmdb']}"):
                    mostrar_detalle(s)
    else:
        st.write("No se han encontrado películas con tramas parecidas en la base de datos.")


if "busqueda_activa" not in st.session_state:
    st.session_state.busqueda_activa = False

if "peliculas_tab1" not in st.session_state:
    st.session_state.peliculas_tab1 = []


# 2. CONFIGURACIÓN DE PÁGINA Y ESTILOS
GENEROS_CONFIG = {"Acción": 28, "Drama": 18, "Animación": 16, "Ciencia Ficción": 878, "Terror": 27, "Romance": 10749, "Thriller": 53, "Fantasía": 14, "Crimen": 80, "Comedia": 35}
st.set_page_config(page_title="MovieAI Pro", page_icon="🍿", layout="wide")

st.markdown("""
    <style>
    /* Estilo del botón */
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        background-color: #E50914; 
        color: white; 
    }
    
    [data-testid="stMain"] [data-testid="stImage"] img { 
        object-fit: cover; 
        border-radius: 10px; 
        max-height: 350px; /* Usamos max-height en lugar de height fijo */
    }

    /* Título: Ajuste de altura */
    .movie-title {
        min-height: 70px;
        max-height: 70px;
        overflow: hidden;
        margin-top: 10px;
    }
    /* CONTENEDOR PRINCIPAL DEL MARQUESINA */
    .marquee-container {
        background-color: #f0f0f0; /* Color crema/blanco envejecido */
        border: 15px solid #222; /* Marco grueso oscuro */
        border-radius: 10px;
        padding: 30px;
        text-align: center;
        box-shadow: 0 0 20px #e50914, inset 0 0 10px rgba(0,0,0,0.5);
        position: relative;
        /* Efecto de rejilla de fondo */
        background-image: 
            linear-gradient(to right, #ddd 1px, transparent 1px),
            linear-gradient(to bottom, #ddd 1px, transparent 1px);
        background-size: 40px 40px;
    }

    /* BOMBILLAS AZUL NEÓN */
    .marquee-container::before {
        content: '● ● ● ● ● ● ● ● ● ● ● ● ● ● ● ● ● ● ● ●';
        position: absolute;
        top: -22px; left: 0; right: 0;
        color: #00f2ff; /* Azul Neón */
        font-size: 18px;
        letter-spacing: 18px;
        text-shadow: 0 0 10px #00f2ff, 0 0 20px #00f2ff;
    }

    /* ESTILO DE LAS LETRAS EN NEGRO */
    .marquee-text {
        color: #000000 !important; /* Negro puro */
        font-family: 'Arial Black', Gadget, sans-serif;
        text-transform: uppercase;
        margin: 0;
    }

    .marquee-main-title {
        font-size: 4rem;
        font-weight: 900;
        letter-spacing: 8px;
    }

    .marquee-subtitle {
        font-size: 1.5rem;
        letter-spacing: 4px;
        border-top: 2px solid #333;
        display: inline-block;
        padding-top: 10px;
        margin-top: 10px;
    }
            
    /* Estilo para los contenedores de inputs en el recomendador */
    .stTextArea textarea {
        background-color: #1a1a1a !important;
        color: #00f2ff !important; /* Texto en azul neón */
        border: 1px solid #333 !important;
        font-family: 'Courier New', monospace !important;
    }

    .recommendation-box {
        background-color: #111;
        border-left: 5px solid #e50914; /* Franja roja lateral */
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    /* --- ESTILO PRO PARA LAS PESTAÑAS (TABS) --- */

    /* Estiliza el contenedor general de las pestañas */
    div[data-testid="stTabs"] button {
        font-family: 'Courier New', Courier, monospace !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        font-size: 0.9rem !important;
        color: #888 !important;
        padding: 10px 20px !important;
    }

    /* Color cuando una pestaña está activa (seleccionada) */
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #00f2ff !important; /* Azul neón */
        font-weight: bold !important;
    }

    /* Línea inferior roja clásica de cine */
    div[data-testid="stTabs"] [data-baseweb="tab-highlight-bar"] {
        background-color: #e50914 !important;
    }

    /* --- Añadir iconos minimalistas antes de cada pestaña --- */
    div[data-testid="stTabs"] button::before {
        font-family: monospace;
        margin-right: 8px;
        font-weight: normal;
    }

    /* Icono para Cartelera (Claqueta minimalista con caracteres o símbolo limpio) */
    div[data-testid="stTabs"] button[id*="tab-cartelera"]::before {
        content: "■";
        color: #e50914;
    }

    /* Icono para Recomendador (Líneas de datos / Filtro) */
    div[data-testid="stTabs"] button[id*="tab-recomendador"]::before {
        content: "⚙";
        color: #ffd700;
    }

    /* Icono para Mood AI (Cursor/Ánimo) */
    div[data-testid="stTabs"] button[id*="tab-mood"]::before {
        content: "›";
        color: #00f2ff;
    }

    /* Icono para Negociador (Mesa de diálogo) */
    div[data-testid="stTabs"] button[id*="tab-negociador"]::before {
        content: "«»";
        color: #ffffff;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #0b0c10 !important;
        border: 1px solid #1f2833 !important;
        border-radius: 0px !important; /* Bordes rectos, aspecto más industrial */
        color: #00f2ff !important; /* Texto azul neón al escribir */
        font-family: 'Courier New', Courier, monospace !important;
    }

    /* Efecto foco: cuando el usuario hace clic para escribir, brilla la caja */
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
        border-color: #00f2ff !important;
        box-shadow: 0 0 10px #00f2ff !important;
    }

    /* Estilo para los textos informativos secundarios */
    .stTextInput p, .stSelectbox p {
        color: #888 !important;
        font-family: 'Courier New', monospace !important;
        font-size: 0.85rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. SIDEBAR
with st.sidebar:
    # st.image("https://cdn-icons-png.flaticon.com/512/2503/2503508.png", width=100)
    # st.title("Filtros")
    st.markdown("""
        <div style="border-bottom: 2px solid #333; margin-bottom: 20px; padding-bottom: 10px;">
            <h2 style="
                color: white; 
                font-family: 'Courier New', Courier, monospace; 
                letter-spacing: 4px; 
                text-align: center;
                margin: 0;
            ">TAQUILLA</h2>
            <p style="
                text-align: center; 
                color: #888; 
                font-size: 0.7rem; 
                letter-spacing: 2px;
                margin: 5px 0 0 0;
            ">— CONTROL DE FILTROS —</p>
        </div>
    """, unsafe_allow_html=True)
    genero_seleccionado = st.selectbox("¿Qué género buscas?", list(GENEROS_CONFIG.keys()))
    busqueda_libre = st.text_input("Buscar por Actor, Director o Título", placeholder="Ej: Christopher Nolan")
    boton_buscar = st.button("🔍 Buscar Películas")

# st.title("MovieAI: Tu Cine Inteligente")
st.markdown("""
    <div class="marquee-container">
        <h1 class="marquee-text marquee-main-title">MOVIE AI</h1>
        <p class="marquee-text marquee-subtitle">SALA DE PROYECCIÓN • ABIERTO 24H</p>
    </div>
    """, unsafe_allow_html=True)

st.write("")


# LÓGICA DE BÚSQUEDA GLOBAL
if boton_buscar:
    termino_final = busqueda_libre.strip() if busqueda_libre.strip() else genero_seleccionado
    st.session_state.peliculas_tab1 = database.filtrar_por_genero(termino_final)
    # Guardamos en sesión que acabamos de hacer una búsqueda activa
    st.session_state.busqueda_activa_global = True
    st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["cartelera", "recomendador", "mood ai", "negociador"])    
                            
# --- PESTAÑA 1 ---
with tab1:
    if "peliculas_tab1" in st.session_state and st.session_state.peliculas_tab1:
        cols = st.columns(3)
        for i, p in enumerate(st.session_state.peliculas_tab1):
            with cols[i % 3]:
                with st.container(height=520, border=True):
                    poster_url = p.get('poster')
                    if not poster_url or poster_url == "":
                        poster_url = "https://via.placeholder.com/500x750?text=Imagen+No+Disponible"
                
                    st.image(poster_url, width='stretch')

                    st.markdown(f"<div class='movie-title'><b>{p['titulo']}</b></div>", unsafe_allow_html=True)
                    
                    # Fila de información: Puntuación y Botón alineados
                    c_rating, c_btn = st.columns([1, 1.5])
                    with c_rating:
                        st.write(f"⭐ {p.get('puntuacion', 0):.1f}")
                    with c_btn:
                        if st.button("Ver detalles", key=f"tab1_{p['id_tmdb']}"):
                            mostrar_detalle(p)

    else:
        # Texto o películas por defecto si el usuario entra por primera vez y no ha buscado nada aún
        st.markdown("<h3 style='text-align: center; color: #888; margin-top: 50px;'>🏛️ LA CARTELERA ESTÁ VACÍA</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Introduce un director o género en la izquierda para proyectar películas.</p>", unsafe_allow_html=True)

# --- PESTAÑA 2 ---
with tab2:
    # 1. INYECCIÓN DE ESTILOS CSS
    st.markdown("""
        <style>
            /* Animación en bucle para el secuenciador de ADN (Adaptado para centrado horizontal) */
            @keyframes girarADN {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            
            .dna-rotation-container {
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 40px 0;
                width: 100%;
            }
            
            .dna-rotation-container img {
                width: 100%;
                max-width: 260px;
                aspect-ratio: 1 / 1;
                object-fit: cover;
                border-radius: 50%;
                border: 2px solid #00f2ff;
                box-shadow: 0 0 25px rgba(0, 242, 255, 0.35);
                animation: girarADN 25s linear infinite;
            }

            /* Tarjetas estéticas para la cuadrícula inferior */
            .movie-card-modern {
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid #1a1a1a;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 15px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            }

            /* Estilo cyberpunk para los títulos de películas */
            .movie-title-modern {
                color: #ffffff;
                font-family: 'Urbanist', sans-serif;
                font-weight: 700;
                font-size: 1rem;
                margin: 10px 0 5px 0;
                height: 2.4rem;
                overflow: hidden;
                text-overflow: ellipsis;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
            }
            /* Fuerza el color negro en el texto de TODOS los botones nativos de esta pestaña */
            div.stButton > button {
                color: #000000 !important;
                font-weight: bold !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # 2. INICIALIZACIÓN DE CONSTANTES Y VARIABLES DE SESIÓN REALES
    if "puntero_salto" not in st.session_state: 
        st.session_state.puntero_salto = 0
    if "recomendaciones" not in st.session_state: 
        st.session_state.recomendaciones = []

    # Cabecera estética
    st.markdown("""
        <div style="text-align: center; padding: 10px; border-bottom: 2px solid #00f2ff; margin-bottom: 30px;">
            <h2 style="color: white; letter-spacing: 3px; margin: 0; text-transform: uppercase; font-family: 'Urbanist', sans-serif;">Configuración de Perfil</h2>
            <p style="color: #00f2ff; font-size: 0.8rem; margin: 5px 0 0 0; letter-spacing: 2px; font-family: monospace;">ANÁLISIS DE PREFERENCIAS PARA EL MOTOR DE IA</p>
        </div>
    """, unsafe_allow_html=True)

    # ─── BLOQUE SUPERIOR ───
    with st.container(border=True):
        with st.form("encuesta_usuario", clear_on_submit=False):
            c1, c2 = st.columns(2, gap="large")
            
            with c1:
                st.markdown("### Géneros favoritos")
                g1 = st.selectbox("Preferencia Principal", list(GENEROS_CONFIG.keys()), key="g1")
                g2 = st.selectbox("Segunda Opción", list(GENEROS_CONFIG.keys()), key="g2")
                g3 = st.selectbox("Tercera Opción", list(GENEROS_CONFIG.keys()), key="g3")
            
            with c2:
                st.markdown("### Tu Top 5 Películas")
                f1 = st.text_input("Pelicula 1", placeholder="Ej: Inception", key="f1", label_visibility="collapsed")
                f2 = st.text_input("Pelicula 2", placeholder="Ej: El Padrino", key="f2", label_visibility="collapsed")
                f3 = st.text_input("Pelicula 3", placeholder="Ej: Toy Story", key="f3", label_visibility="collapsed")
                f4 = st.text_input("Pelicula 4", placeholder="Ej: Matrix", key="f4", label_visibility="collapsed")
                f5 = st.text_input("Pelicula 5", placeholder="Ej: Pulp Fiction", key="f5", label_visibility="collapsed")
            
            st.write("")
            submitted = st.form_submit_button("GENERAR CARTELERA PERSONALIZADA", use_container_width=True)
            
            if submitted:
                st.session_state.puntero_salto = 0
                with st.spinner("Anclando preferencias y secuenciando ADN..."):
                    raw_recos = database.obtener_recomendaciones_pro([g1, g2, g3], [f1, f2, f3, f4, f5], salto=0)
                    vistas = [f1.lower().strip(), f2.lower().strip(), f3.lower().strip(), f4.lower().strip(), f5.lower().strip()]
                    st.session_state.recomendaciones = [p for p in raw_recos if p['titulo'].lower().strip() not in vistas]
                st.rerun()

    st.write("")

    # ─── BLOQUE INFERIOR: RESULTADOS O ESTADO DE ESPERA ───
    with st.container():
        if not st.session_state.recomendaciones:
            st.markdown("<p style='color: #666; font-family: monospace; font-size: 0.8rem; text-align: center;'>[ SECUENCIADOR DE ADN ACTIVO • ESPERANDO PARÁMETROS ]</p>", unsafe_allow_html=True)
            st.markdown("""
                <div class="dna-rotation-container">
                    <img src="https://images.unsplash.com/photo-1507668077129-56e32842fceb?q=80&w=600">
                </div>
            """, unsafe_allow_html=True)
        else:
            # Si ya hay películas, renderizamos la cuadrícula horizontal de 3 columnas
            st.markdown("<p style='color: #00ff41; font-family: monospace; font-size: 0.9rem; margin-bottom: 20px;'>[ RED NEURAL CALIBRADA • RECOMENDACIONES ]</p>", unsafe_allow_html=True)
            
            # Configuramos una cuadrícula de 3 columnas para aprovechar el ancho completo
            N_COLUMNAS = 3
            columnas_pelis = st.columns(N_COLUMNAS, gap="medium")
            
            for i, p in enumerate(st.session_state.recomendaciones):
                # Distribuimos cíclicamente entre las 3 columnas horizontales
                with columnas_pelis[i % N_COLUMNAS]:
                    with st.container(height=540, border=True):
                        poster_url = p.get('poster') or "https://via.placeholder.com/500x750?text=Sin+Imagen"
                        st.image(poster_url, width='stretch')
                        
                        st.markdown(f"<div class='movie-title-modern'>{p['titulo']}</div>", unsafe_allow_html=True)

                        director = p.get('director', 'Desconocido')
                        reparto = p.get('reparto', 'Desconocido')

                        if len(reparto) > 50:
                            reparto = reparto[:47] + "..."

                        c_nota, c_ver = st.columns([1, 1.5])
                        with c_nota:
                            st.write(f"{p.get('puntuacion', 0):.1f}")
                        with c_ver:
                            if st.button("DETALLES", key=f"tab2_{p['id_tmdb']}", width='stretch'):
                                mostrar_detalle(p)

            # Botón de refresco centrado abajo del todo
            st.write("")
            if st.button("MOSTRAR OTRAS OPCIONES", width='stretch'):
                with st.spinner("Cambiando el carrete de proyección..."):
                    st.session_state.recomendaciones = database.obtener_recomendaciones_pro(
                        [g1, g2, g3], 
                        [f1, f2, f3, f4, f5]
                    )
                st.rerun()
                    

# ----- PESTAÑA 3 -----
with tab3:
    # 1. ESTILOS CSS REFORZADOS
    st.markdown("""
        <style>
            /* Contenedor flexible para permitir el centrado de la 5ª imagen */
            .mood-flex-container {
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 15px;
                margin-top: 10px;
            }
            
            /* Tarjetas individuales */
            .mood-card {
                position: relative;
                border: 1px solid #1f2833;
                border-radius: 8px;
                overflow: hidden;
                width: calc(50% - 10px); /* Dos por fila */
                aspect-ratio: 16 / 9;
                background-color: #000;
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            }
            
            /* La quinta imagen (Mad Max) ocupa un ancho especial para centrarse */
            .mood-card.centered {
                width: 70%; /* Un poco más grande para destacar */
                margin-top: 5px;
                border: 1px solid #ff4b4b; /* Borde rojizo sutil para adrenalina */
            }
            
            .mood-card img {
                width: 100%;
                height: 100%;
                object-fit: cover;
                opacity: 0.5;
                transition: all 0.4s ease;
            }
            
            .mood-card:hover img {
                opacity: 0.9;
                transform: scale(1.05);
            }
            
            .mood-overlay-title {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                background: linear-gradient(transparent, rgba(0,0,0,0.95));
                color: #fff;
                font-family: 'Courier New', monospace;
                font-size: 0.75rem;
                text-align: center;
                padding: 20px 5px 8px 5px;
                letter-spacing: 1px;
                text-transform: uppercase;
            }

            .matrix-box {
                background-color: #000000;
                border: 1px solid #00ff41;
                border-radius: 4px;
                padding: 15px;
                height: 140px;
                font-family: 'Courier New', monospace;
                color: #00ff41;
                font-size: 0.8rem;
                box-shadow: 0 0 15px rgba(0, 255, 65, 0.1);
                margin: 15px 0;
            }
        </style>
    """, unsafe_allow_html=True)

    if "mood_texto" not in st.session_state:
        st.session_state.mood_texto = ""

    if "mood_respuesta" not in st.session_state:
        st.session_state.mood_respuesta = ""

    # Cabecera
    st.markdown("""
        <div style="text-align: center; margin-bottom: 25px; border-bottom: 1px solid #1f2833; padding-bottom: 15px;">
            <h2 style="color: white; font-family: 'Courier New', monospace; letter-spacing: 3px; margin: 0; font-size: 1.3rem;">
                [ DIAGNÓSTICO EMOCIONAL • CALIBRACIÓN DEL ALGORITMO ]
            </h2>
        </div>
    """, unsafe_allow_html=True)

    col_izq, col_der = st.columns([1.2, 0.8], gap="large")

    # ─── BLOQUE IZQUIERDO: MOODBOARD 5 IMÁGENES ─────────────────
    with col_izq:
        st.markdown("<p style='color: #666; font-family: monospace; font-size: 0.8rem; margin-bottom: 15px; text-align: center;'>[ Elige el estado que más se adapte a ti ]</p>", unsafe_allow_html=True)
        
        # HTML del Moodboard (4 arriba + 1 abajo centrada)
        st.markdown("""
            <div class="mood-flex-container">
                <div class="mood-card">
                    <img src="https://images.unsplash.com/photo-1536440136628-849c177e76a1?q=80&w=500">
                    <div class="mood-overlay-title">🧠 01. ESTRÉS / CANSANCIO</div>
                </div>
                <div class="mood-card">
                    <img src="https://fotografias-2.larazon.es/clipping/cmsimages02/2019/08/12/332AB248-F9B7-482C-B0D4-EBF202E67B6F/98.jpg?crop=1280,720,x0,y0&width=1900&height=1069&optimize=low&format=webply">
                    <div class="mood-overlay-title">🎬 02. FELICIDAD / RISA</div>
                </div>
                <div class="mood-card">
                    <img src="https://bearvsfilm.wordpress.com/wp-content/uploads/2015/10/lost_in_translation_by_londra.jpg?w=768&h=474&crop=1">
                    <div class="mood-overlay-title">🌧️ 03. MELANCOLÍA / NOSTALGIA</div>
                </div>
                <div class="mood-card">
                    <img src="https://images.unsplash.com/photo-1478720568477-152d9b164e26?q=80&w=500">
                    <div class="mood-overlay-title">🕵️ 04. MISTERIO / INTRIGA</div>
                </div>
                <div class="mood-card centered">
                    <img src="https://media-assets.wired.it/photos/615f17ab8c3e103a63d4dee1/master/w_1600,c_limit/1493369204_Mad-Max.jpg">
                    <div class="mood-overlay-title">🔥 05. ADRENALINA / ENERGÍA</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Botones de interacción
        st.write("")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("CARGAR 01", key="mb1", width='stretch'):
                st.session_state.mood_texto = "He tenido un día agotador. Necesito algo ligero, divertido y que no me haga pensar mucho."
                with st.spinner("Conectando con el Agente..."):
                    st.session_state.mood_respuesta = database.obtener_recomendacion_agente(st.session_state.mood_texto)
                st.rerun()
        with c2:
            if st.button("CARGAR 02", key="mb2", width='stretch'):
                st.session_state.mood_texto = "¡Me siento genial! Quiero una comedia desternillante o una peli feel-good que me haga reír."
                with st.spinner("Conectando con el Agente..."):
                    st.session_state.mood_respuesta = database.obtener_recomendacion_agente(st.session_state.mood_texto)
                st.rerun()
        with c3:
            if st.button("CARGAR 03", key="mb3", width='stretch'):
                st.session_state.mood_texto = "Me siento melancólico y algo nostálgico. Busco un drama profundo, pausado y con mucha atmósfera."
                with st.spinner("Conectando con el Agente..."):
                    st.session_state.mood_respuesta = database.obtener_recomendacion_agente(st.session_state.mood_texto)
                st.rerun()
        with c4:
            if st.button("CARGAR 04", key="mb4", width='stretch'):
                st.session_state.mood_texto = "Quiero algo que me mantenga en vilo. Un misterio psicológico, suspense o una trama llena de giros."
                with st.spinner("Conectando con el Agente..."):
                    st.session_state.mood_respuesta = database.obtener_recomendacion_agente(st.session_state.mood_texto)
                st.rerun()
        with c5:
            if st.button("CARGAR 05", key="mb5", width='stretch'):
                st.session_state.mood_texto = "¡ADRENALINA PURA! Quiero acción desenfrenada, efectos brutales y una peli que me mantenga pegado al asiento."
                with st.spinner("Conectando con el Agente..."):
                    st.session_state.mood_respuesta = database.obtener_recomendacion_agente(st.session_state.mood_texto)
                st.rerun()

    # ─── BLOQUE DERECHO: INPUT Y CONSOLA ───────────────────────────
    with col_der:
        st.markdown("<p style='color: #666; font-family: monospace; font-size: 0.8rem;'>[ ENTRADA PSICOLÓGICA ]</p>", unsafe_allow_html=True)
        
        user_input = st.text_input(
            "Entrada", value=st.session_state.mood_texto,
            placeholder="O detalla tus sensaciones aquí...",
            key="mood_matrix_input", label_visibility="collapsed"
        )
        
        st.markdown(f"""
            <div class="matrix-box">
                <span style="color: #00ff41; opacity: 0.5;">{st.session_state.mood_texto[:40]}...</span><br>
                <span style="color: #fff;">>> SCANNING NEURAL VIBRATIONS...</span><br>
                <span style="color: #00ff41;">>> MOOD_DETECTED: {st.session_state.mood_texto.split(' ')[0] if st.session_state.mood_texto else 'WAITING'}</span><br>
                <span style="color: #00ff41; font-weight: bold;">>> READY_FOR_PROJECTION_</span>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("EXECUTE NEURAL SCAN & PROJECTION", width='stretch', key="matrix_final"):
            if user_input:
                with st.spinner("Decodificando flujos de conciencia..."):
                    respuesta_agente = database.obtener_recomendacion_agente(user_input)
                    st.success("Análisis Completado.")
                    st.info(respuesta_agente)
            else:
                st.warning("Inserta parámetros emocionales.")

    # ─── SECCIÓN DE RESULTADOS GLOBAL ───────
    if st.session_state.mood_respuesta:
        st.write("")
        st.markdown("### Estas son las mejores películas para ti:")
        st.success("Análisis neuro-cinematográfico completado con éxito.")
        st.info(st.session_state.mood_respuesta)

# ----- PESTAÑA 4 -----

with tab4:
    # 1. ARQUITECTURA DE ESTILOS BLINDADOS (CSS)
    st.markdown("""
        <style>
            /* Contenedor principal en rejilla para forzar la simetría superior */
            .negotiator-grid {
                display: grid;
                grid-template-columns: 1.2fr 0.8fr 1.2fr;
                gap: 25px;
                align-items: start;
                margin-top: 10px;
            }
            
            /* Tarjetas de los litigantes */
            .litigant-card {
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid #1a1a1a;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }
            
            .litigant-header {
                font-family: 'Courier New', monospace;
                color: #ffffff;
                font-size: 0.85rem;
                font-weight: bold;
                letter-spacing: 1px;
                margin-bottom: 12px;
                border-bottom: 1px dashed #333;
                padding-bottom: 5px;
            }
            
            /* Contenedor central del Juez Holográfico */
            .judge-hologram-box {
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                background: rgba(255, 170, 0, 0.02);
                border: 1px dashed rgba(255, 170, 0, 0.2);
                border-radius: 8px;
                padding: 15px;
                height: 100%;
            }
            
            .judge-hologram-box img {
                width: 100%;
                max-width: 190px;
                aspect-ratio: 1 / 1;
                object-fit: cover;
                border-radius: 6px;
                border: 1px solid #ffaa00;
                box-shadow: 0 0 20px rgba(255, 170, 0, 0.2);
                filter: grayscale(20%) contrast(110%);
            }
            
            .judge-status {
                color: #ffaa00;
                font-family: 'Courier New', monospace;
                font-size: 0.75rem;
                margin-top: 10px;
                letter-spacing: 1px;
                font-weight: bold;
            }

            /* Consola técnica inferior */
            .arbitrator-console-box {
                background-color: #000000;
                border: 1px solid #ffaa00;
                border-radius: 4px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                color: #ffaa00;
                font-size: 0.8rem;
                box-shadow: 0 0 15px rgba(255, 170, 0, 0.08);
                line-height: 1.5;
                height: 110px;
            }
        </style>
    """, unsafe_allow_html=True)

    # Inicialización de estados de sesión para controlar la persistencia de los datos
    if "negociacion_activa" not in st.session_state:
        st.session_state.negociacion_activa = False
    if "dictamen_final" not in st.session_state:
        st.session_state.dictamen_final = ""

    # Cabecera de la Sala de Arbitraje
    st.markdown("""
        <div style="text-align: center; margin-bottom: 25px;">
            <h2 style="color: white; font-family: 'Courier New', monospace; letter-spacing: 3px; margin: 0; font-size: 1.3rem;">
                [ ARBITRAJE DE CONFLICTOS FÍLMICOS ]
            </h2>
            <p style="color: #ffaa00; font-family: monospace; font-size: 0.8rem; margin-top: 5px; letter-spacing: 2px;">
                SALA DE MEDIACIÓN NEURAL • TRIBUNAL DE CONSENSO IA
            </p>
            <div style="width: 100%; height: 1px; background: linear-gradient(90deg, transparent, #ffaa00, transparent); margin-top: 12px;"></div>
        </div>
    """, unsafe_allow_html=True)

    # ─── FILA SUPERIOR: ESTRUCTURA SIMÉTRICA (AMIGO 1 | JUEZ | AMIGO 2) ───
    # Abrimos tres columnas nativas de Streamlit para inyectar los componentes alineados
    c_izq, c_mid, c_der = st.columns([1.2, 0.8, 1.2], gap="medium")

    with c_izq:
        st.markdown("""
            <div class="litigant-card">
                <div class="litigant-header">LITIGANTE 01: DEMANDA ACTUAL</div>
            </div>
        """, unsafe_allow_html=True)
        # Ponemos label_visibility="collapsed" para eliminar el texto duplicado de arriba
        input_p1 = st.text_area(
            "¿Qué te apetece?",
            placeholder="Ej: Mucha acción, explosiones, ritmo frenético y nada de romances lentos...",
            key="text_neg_user1",
            height=140,
            label_visibility="collapsed"
        )

    # ─── JUEZ ROBOT ANIMADO (Columna Central) ───
    with c_mid:
        # COMPACTO Y SIN ESPACIOS VACÍOS
        st.markdown("""<div class="judge-center-panel"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="100%"><circle cx="150" cy="150" r="140" fill="none" stroke="#10141d" stroke-width="4"/><circle cx="150" cy="150" r="130" fill="none" stroke="#00f2ff" stroke-width="2" stroke-dasharray="10 5 2 5"/><circle cx="150" cy="150" r="120" fill="none" stroke="#ffaa00" stroke-width="1" opacity="0.4"/><path d="M 150 15 L 150 35 M 150 265 L 150 285 M 15 L 150 35 L 150 M 265 150 L 285 150" stroke="#00f2ff" stroke-width="2" opacity="0.7"/><line x1="30" y1="150" x2="270" y2="150" stroke="#00f2ff" stroke-width="2" opacity="0.5"><animate attributeName="y1" values="45;255;45" dur="4s" repeatCount="indefinite" /><animate attributeName="y2" values="45;255;45" dur="4s" repeatCount="indefinite" /></line><path d="M 120 210 L 120 250 L 180 250 L 180 210 Z" fill="#161b26" stroke="#00f2ff" stroke-width="2"/><line x1="135" y1="215" x2="135" y2="245" stroke="#ffaa00" stroke-width="2"/><line x1="150" y1="215" x2="150" y2="245" stroke="#00f2ff" stroke-width="2"/><line x1="165" y1="215" x2="165" y2="245" stroke="#ffaa00" stroke-width="2"/><path d="M 90 100 Q 90 50 150 50 Q 210 50 210 100 Q 210 160 175 200 L 125 200 Q 90 160 90 100 Z" fill="#0d1117" stroke="#00f2ff" stroke-width="3"/><path d="M 100 95 Q 100 65 150 65 Q 200 65 200 95 Q 200 135 170 165 L 130 165 Q 100 135 100 95 Z" fill="#05070a" stroke="#ffaa00" stroke-width="2"/><circle cx="125" cy="95" r="12" fill="none" stroke="#00f2ff" stroke-width="1" stroke-dasharray="3 2"/><circle cx="125" cy="95" r="4" fill="#00f2ff"/><path d="M 155 95 L 163 80 L 171 110 L 179 85 L 187 105 L 195 95" fill="none" stroke="#00ff41" stroke-width="2"><animate attributeName="d" values="M 155 95 L 163 80 L 171 110 L 179 85 L 187 105 L 195 95;M 155 95 L 163 110 L 171 80 L 179 105 L 187 85 L 195 95;M 155 95 L 163 80 L 171 110 L 179 85 L 187 105 L 195 95" dur="1.2s" repeatCount="indefinite" /></path><rect x="110" y="130" width="80" height="6" fill="#161b26" stroke="#00f2ff" stroke-width="1"/><path d="M 120 133 L 180 133" stroke="#ffaa00" stroke-width="2" stroke-dasharray="5 2"><animate attributeName="stroke-dashoffset" values="0;14" dur="1.5s" repeatCount="indefinite"/></path><text x="150" y="185" fill="#00f2ff" font-family="monospace" font-size="10" text-anchor="middle" font-weight="bold" letter-spacing="1"></text></svg><div class="judge-title"></div></div>""", unsafe_allow_html=True)

# ─── LITIGANTE 02 (Columna Derecha) ───
    with c_der:
        st.markdown("""
            <div class="litigant-card">
                <div class="litigant-header">LITIGANTE 02: DEMANDA CONTRARIA</div>
            </div>
        """, unsafe_allow_html=True)
        input_p2 = st.text_area(
            "¿Y a ti?",
            placeholder="Ej: Un drama profundo, suspense psicológico, algo lento que me haga pensar...",
            key="text_neg_user2",
            height=140,
            label_visibility="collapsed"
        )

    st.write("")

    # ─── FILA INFERIOR: PANEL DE CONTROL (BOTÓN INDUSTRIAL Y CONSOLA) ───

    c_btn, c_console = st.columns([1.2, 1.2], gap="large")

    with c_btn:
        st.write("")
        # Botón de ejecución adaptado al contenedor
        if st.button("INICIAR PROTOCOLO DE MEDIACIÓN", use_container_width=True, key="trigger_arbitraje"):
            if input_p1 and input_p2:
                with st.spinner("Procesando discrepancias conceptuales..."):
                    try:
                        # Pasamos las variables de los inputs reales
                        resultado_crew = database.ejecutar_negociacion(input_p1, input_p2)
                        
                        # Convertimos a texto limpio (Markdown)
                        st.session_state.dictamen_final = str(resultado_crew)
                        st.session_state.negociacion_activa = True
                        
                    except Exception as e:
                        # Margen de seguridad por si falla la conexión con Gemini o la query SQL
                        st.error(f"Error en la deliberación de los agentes: {e}")
                        st.session_state.dictamen_final = (
                            "### JUICIO INTERRUMPIDO\n\n"
                            "Hubo un error técnico durante la negociación de los agentes. "
                            "Verifica las credenciales de Gemini o las tablas de la base de datos.\n\n"
                            f"**Demandas retenidas:**\n"
                            f"* Litigante 01: `{input_p1}`\n"
                            f"* Litigante 02: `{input_p2}`"
                        )
                        st.session_state.negociacion_activa = True

            st.rerun()


    with c_console:
        # Estado simulado de los inputs en código de consola
        st1 = "READY" if input_p1 else "EMPTY"
        st2 = "READY" if input_p2 else "EMPTY"
        st.markdown(f"""
            <div class="arbitrator-console-box">
                >> NEURAL_CROSSMATCHER_ONLINE...<br>
                >> LITIGANTE_01_FEED: [{st1}]<br>
                >> LITIGANTE_02_FEED: [{st2}]<br>
                >> READY_FOR_VERDICT_
            </div>
        """, unsafe_allow_html=True)

    # ─── BLOQUE DE RESOLUCIÓN FINAL ──────────
    if st.session_state.negociacion_activa and st.session_state.dictamen_final:
        st.write("---")
        st.success("Mediación completada. Acuerdo de visionado disponible.")
        st.info(st.session_state.dictamen_final)
        
        if st.button("Disolver tribunal y abrir nuevo caso", use_container_width=True):
            st.session_state.negociacion_activa = False
            st.session_state.dictamen_final = ""
            st.rerun()