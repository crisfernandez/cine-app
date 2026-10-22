from crewai import Agent, Task, Crew, Process

from agents.tools import consultar_cine_db


def ejecutar_negociacion(gusto_amigo_1, gusto_amigo_2):
    # AGENTE 1: El experto en el Amigo 1
    abogado_1 = Agent(
        role='Defensor del Amigo 1',
        goal=f'Extraer lo mejor de los gustos: {gusto_amigo_1}',
        backstory='Eres un experto en encontrar la esencia de lo que le gusta a la primera persona, en el contexto de la cinematográfica.',
        llm="gemini/gemini-2.5-flash",
        allow_delegation=False
    )

    # AGENTE 2: El experto en el Amigo 2
    abogado_2 = Agent(
        role='Defensor del Amigo 2',
        goal=f'Extraer lo mejor de los gustos: {gusto_amigo_2}',
        backstory='Eres un experto en defender los intereses de la segunda persona, en el contexto de la cinematográfica.',
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
        agent=abogado_1  # El primer abogado inicia la propuesta
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
