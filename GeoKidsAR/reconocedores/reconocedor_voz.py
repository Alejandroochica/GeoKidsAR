import speech_recognition as sr
class Respuesta:
    def __init__(self, texto, es_correcta):  
        self.texto = texto
        self.es_correcta = es_correcta

def normalizar_comparacion(texto):
    """Normaliza texto para comparación ignorando tildes y mayúsculas"""
    texto = texto.lower()
    replacements = (
        ("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
        ("ü", "u"), ("-", ""), (" ", "")
    )
    for a, b in replacements:
        texto = texto.replace(a, b)
    return texto

def procesar_respuesta(pregunta):   

    r = sr.Recognizer()
    r.energy_threshold = 4000  # Ajuste del umbral de energía para filtrar ruido ambiental

    with sr.Microphone() as source:
        print("\nDi tu respuesta...")
        try:
            r.adjust_for_ambient_noise(source, duration=0.5) # Ajuste para ruido de fondo
            audio = r.listen(source, timeout=5, phrase_time_limit=3) # Escuchar la respuesta
             # Reconocimiento usando Google Speech Recognition en español 
            texto_reconocido = r.recognize_google(audio, language='es-ES')
            print(f"Has dicho: {texto_reconocido}")

            # Normalizamos para comparación 
            texto_comparar = normalizar_comparacion(texto_reconocido)

            # Comparamos la respuesta reconocida con las opciones proporcionadas
            for opcion in pregunta['opciones']:
                opcion_comparar = normalizar_comparacion(opcion)
                respuesta_correcta = normalizar_comparacion(pregunta['respuesta_correcta'])

                # Si coincide con alguna opción, devolvemos si es correcta o no
                if opcion_comparar == texto_comparar:
                    return Respuesta(opcion, opcion_comparar == respuesta_correcta)
            
            # Si no coincide con ninguna opción, devolvemos como incorrecta
            return Respuesta(texto_reconocido, False)

        except sr.WaitTimeoutError:
            print("Tiempo de espera agotado") # No se detectó respuesta a tiempo
            return Respuesta("", False)
        except sr.UnknownValueError:
            print("No se pudo entender el audio") 
            return Respuesta("", False)
        except Exception as e:
            print(f"Error inesperado: {str(e)}") # Captura cualquier otro error inesperado
            return Respuesta("", False)