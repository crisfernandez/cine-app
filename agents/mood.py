from crewai import Agent, Task, Crew

from agents.tools import consultar_cine_db


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
