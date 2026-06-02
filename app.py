import flask
from flask import Flask, jsonify, request
import database

app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/peliculas')
def lista_peliculas():
    # Extraemos el género de la URL (?genero=Drama)
    genero = request.args.get('genero')
    
    # Imprime esto en la consola para ver qué está recibiendo Flask realmente
    print(f"DEBUG: El género recibido es -> '{genero}'")

    if genero and genero != "None": 
        # Si hay un género válido, filtramos
        print(f"DEBUG: Entrando en modo FILTRAR por {genero}")
        datos = database.filtrar_por_genero(genero)
    else:
        # Si no hay género en la URL, damos la lista completa
        print("DEBUG: Entrando en modo LISTA COMPLETA")
        datos = database.obtener_todas()
        
    return jsonify(datos)

@app.route('/detalles/<int:id_tmdb>')
def detalles_pelicula(id_tmdb):
    # Usamos el token que ya tienes definido
    token = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0N2JkYmU1NjQwMGE5ZTFhOTlhNGE4NTEwM2VkOWE5MiIsIm5iZiI6MTc3MzkxNjI4MC40OTcsInN1YiI6IjY5YmJkMDc4ZTQxZDM1MjI4NGE5ODc1ZCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.jO4xslm-xDxqn6ij0Q1zrC6Kse8pX1IqW21EIc-OE1E" 
    director, actores, plataformas = database.obtener_info_extra_api(id_tmdb, token)
    
    return jsonify({
        "director": director,
        "actores": actores,
        "plataformas": plataformas
    })

app.run(debug=True)   