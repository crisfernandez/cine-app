import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

from agents import mood, negotiator
from services import movies

app = Flask(__name__)
app.config["DEBUG"] = True

TMDB_TOKEN = os.getenv("TMDB_TOKEN")


@app.route('/api/salud')
def salud():
    return jsonify({"estado": "ok"})


@app.route('/api/peliculas')
def lista_peliculas():
    termino = request.args.get('termino')
    datos = movies.filtrar_por_genero(termino)
    return jsonify(datos)


@app.route('/api/peliculas/<int:id_tmdb>/detalles')
def detalles_pelicula(id_tmdb):
    director, actores, plataformas = movies.obtener_info_extra_api(id_tmdb, TMDB_TOKEN)
    return jsonify({
        "director": director,
        "actores": actores,
        "plataformas": plataformas
    })


@app.route('/api/peliculas/<int:id_tmdb>/similares')
def peliculas_similares(id_tmdb):
    datos = movies.obtener_recomendaciones_ml(id_tmdb)
    return jsonify(datos)


@app.route('/api/recomendaciones', methods=['POST'])
def recomendaciones_perfil():
    body = request.get_json(force=True) or {}
    generos = body.get('generos', [])
    favoritos = body.get('favoritos', [])
    salto = body.get('salto', 0)
    datos = movies.obtener_recomendaciones_pro(generos, favoritos, salto=salto)
    return jsonify(datos)


@app.route('/api/agentes/mood', methods=['POST'])
def agente_mood():
    body = request.get_json(force=True) or {}
    texto = body.get('texto', '')
    respuesta = mood.obtener_recomendacion_agente(texto)
    return jsonify({"respuesta": respuesta})


@app.route('/api/agentes/negociacion', methods=['POST'])
def agente_negociacion():
    body = request.get_json(force=True) or {}
    gusto_1 = body.get('gusto_1', '')
    gusto_2 = body.get('gusto_2', '')
    veredicto = negotiator.ejecutar_negociacion(gusto_1, gusto_2)
    return jsonify({"veredicto": str(veredicto)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
