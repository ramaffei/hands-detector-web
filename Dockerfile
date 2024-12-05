# Usa una imagen base oficial de Python
FROM python:3.10-slim

# Instala dependencias del sistema necesarias para OpenCV
RUN apt-get update && apt-get install -y \
    libsm6 libxext6 libxrender-dev ffmpeg \
    && apt-get clean

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo de dependencias y el script al contenedor
COPY requirements.txt requirements.txt
COPY app.py app.py

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto (si la aplicación necesita comunicar hacia afuera, como con Flask)
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]
