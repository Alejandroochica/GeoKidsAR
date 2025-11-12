# detectar_cara.py
import face_recognition
import numpy as np
import json
import cv2
import os
from cuia import myVideo, popup, plot  # Importamos las utilidades de cuia.py
from reconocedores import reconocedor_voz

# Configuración
RUTA_DATOS = "datos"
RUTA_USUARIOS = os.path.join(RUTA_DATOS, "usuarios_vectores.json")
UMBRAL_SIMILITUD = 0.45
MODELO_DETECCION = "hog"  # "hog" para CPU, "cnn" para GPU

def cargar_usuarios():
    """Carga los usuarios desde el archivo JSON"""
    try:
        with open(RUTA_USUARIOS, "r") as f:
            data = json.load(f)
            return {
                usuario: {
                    **datos,
                    "codificacion": np.array(datos["codificacion"]) if isinstance(datos["codificacion"], list) else datos["codificacion"],
                    "nombre": datos.get("nombre", usuario)
                } for usuario, datos in data.items()
            }
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return {}

def guardar_usuarios(usuarios):
    """Guarda los usuarios en el archivo JSON"""
    data_serializable = {
        usuario: {
            "nombre": usuario,
            "codificacion": datos["codificacion"].tolist(),  #Convierte ndarray a lista para JSON
            "nivel": datos.get("nivel", 1),
            "preferencias": datos.get("preferencias", {"idioma": "es", "voz": True}),
            "progreso": datos.get("progreso", {})
        } for usuario, datos in usuarios.items()
    }
    
    os.makedirs(RUTA_DATOS, exist_ok=True)
    with open(RUTA_USUARIOS, "w") as f:
        json.dump(data_serializable, f, indent=2)

def extraer_codificacion(frame):
    """Extrae vector facial de un frame usando las utilidades de cuia.py"""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Detección mejorada con face_locations
    face_locations = face_recognition.face_locations(rgb, model=MODELO_DETECCION)
    
    if not face_locations:
        return None
    
    # Extracción de codificaciones
    face_encodings = face_recognition.face_encodings(rgb, known_face_locations=[face_locations[0]])
    
    return face_encodings[0] if face_encodings else None


def registrar_usuario(frame, nombre=None):
    """Registra un nuevo usuario integrando reconocimiento de voz"""
    codificacion = extraer_codificacion(frame)
    if codificacion is None:
        print("No se detectó ninguna cara en el frame.")
        return None

    usuarios = cargar_usuarios()
    
    # Obtener nombre por voz
    if nombre is None:
        print("Por favor, di tu nombre para registrarte...")
        pregunta = {
            "opciones": [],
            "respuesta_correcta": ""
        }
        resultado_voz = reconocedor_voz.procesar_respuesta(pregunta)
        print("DEBUG resultado_voz:", resultado_voz, type(resultado_voz))
        nombre = resultado_voz.texto.strip() if resultado_voz and resultado_voz.texto else f"Jugador{len(usuarios) + 1}"
        print(f"Nombre registrado: {nombre}")


    # Verificar nombre único
    while nombre in usuarios:
        print(f"El nombre '{nombre}' ya existe. Por favor, di otro nombre...")
        resultado_voz = reconocedor_voz.procesar_respuesta("¿Cómo te llamas?")
        nombre = resultado_voz.texto.strip() if resultado_voz and resultado_voz.texto else f"Jugador{len(usuarios) + 1}"
        print(f"Nuevo nombre registrado: {nombre}")

    # Registrar usuario
    usuarios[nombre] = {
        "nombre": nombre,
        "codificacion": codificacion,
        "nivel": 1,
        "preferencias": {"idioma": "es", "voz": True},
        "progreso": {}
    }
    
    guardar_usuarios(usuarios)
    print(f"Usuario {nombre} registrado con éxito")
    
    # Mostrar imagen registrada
    popup(f"Usuario {nombre} registrado", frame)
    
    return nombre

def identificar_usuario(frame):
    """Identifica un usuario existente usando compare_faces"""
    codificacion = extraer_codificacion(frame)
    if codificacion is None:
        return None

    usuarios = cargar_usuarios()
    codificaciones_conocidas = [datos["codificacion"] for datos in usuarios.values()]
    nombres_conocidos = list(usuarios.keys())

    # Comparación eficiente con compare_faces
    matches = face_recognition.compare_faces(
        codificaciones_conocidas,
        codificacion,
        tolerance=UMBRAL_SIMILITUD
    )

    # Devolver el primer match encontrado
    for nombre, match in zip(nombres_conocidos, matches):
        if match:
            return nombre

    return None


