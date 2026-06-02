# 1. Usamos una imagen de Python ligera
FROM python:3.11-slim

# 2. Evitamos que Python genere archivos .pyc y forzamos logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Instalamos dependencias del sistema necesarias para SQLite y herramientas de red
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 4. Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# 5. Copiamos el archivo de requerimientos e instalamos las librerías
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiamos todo el resto del código (incluyendo cine.db)
COPY . .

# 7. Exponemos el puerto que usa Streamlit
EXPOSE 8501

# 8. Comando para arrancar la app
CMD ["streamlit", "run", "interface.py", "--server.port=8501", "--server.address=0.0.0.0"]