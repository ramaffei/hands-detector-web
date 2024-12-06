from flask import Flask, Response, render_template, send_from_directory, request
import cv2
import mediapipe as mp
import numpy as np
import time
from pathlib import Path

app = Flask(__name__)

# Crear un directorio para almacenar las imágenes capturadas
IMAGE_FOLDER = Path("captured_images")
IMAGE_FOLDER.mkdir(exist_ok=True)

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Variable global para controlar el reinicio de la cámara
cap = None

def get_camera():
    """Obtiene una nueva instancia de la cámara."""
    global cap
    if cap is not None:
        cap.release()  # Asegurarse de liberar recursos
    cap = cv2.VideoCapture(0)  # Crear una nueva instancia
    return cap

# Función para procesar el video y enviar los frames
def generate_frames():
    global cap
    cap = get_camera()  # Siempre usar una nueva instancia de la cámara
    fps = 15  # Establece un FPS de 15
    frame_rate_delay = 1.0 / fps
    last_time = time.time()

    with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
        while True:
            success, image = cap.read()
            if not success:
                break

            # Reducción de resolución (por ejemplo 640x480)
            image = cv2.resize(image, (640, 480))

            # Solo enviar un frame cada cierto tiempo (control del FPS)
            current_time = time.time()
            if current_time - last_time >= frame_rate_delay:
                last_time = current_time

                # Procesar la imagen
                image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = hands.process(image)

                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Comprimir la imagen a JPEG con calidad ajustada (50%)
                _, buffer = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                frame = buffer.tobytes()

                # Enviar el frame al navegador
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

# Ruta para transmitir el video
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Ruta para capturar una imagen y guardarla en el servidor
@app.route('/capture_image')
def capture_image():
    global cap
    if cap is None:
        cap = get_camera()

    # Procesar la imagen desde la cámara
    success, image = cap.read()
    if success:
        with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
            # Procesar la imagen
            image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = hands.process(image)

            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Dibujar puntos de las manos si se detectan
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Guardar la imagen procesada
            timestamp = int(time.time())
            image_path = IMAGE_FOLDER / f"{timestamp}.png"
            cv2.imwrite(str(image_path), image)

        return f'Imagen capturada con éxito y guardada como {image_path.name}!'
    else:
        return 'No se pudo capturar la imagen.', 500


# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para mostrar la galería de imágenes capturadas
@app.route('/gallery')
def gallery():
    image_files = list(IMAGE_FOLDER.glob("*.png"))
    image_files = [f.name for f in image_files]
    return render_template('gallery.html', image_files=image_files)

# Ruta para servir las imágenes desde el servidor
@app.route('/captured_images/<filename>')
def send_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
