# Main.py
import json
import cv2
import os
import unicodedata
from reconocedores import detector_marcadores, reconocedor_cara, reconocedor_voz
from reconocedores.figura_visual import mostrar_figura, dibujar_cubo, dibujar_piramide


# Configuración para evitar errores de Qt en Linux
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class RespuestaCorrecta:
    def __init__(self, texto, es_correcta):
        self.texto = texto
        self.es_correcta = es_correcta

# Reemplazar la clase problemática
reconocedor_voz.Respuesta = RespuestaCorrecta

def mostrar_menu_inicial(cap):
    """
    Muestra el menú inicial y captura la selección del usuario
    Retorna: 'iniciar_sesion', 'registrar' o None
    """
    while True:
        ret, frame = cap.read()
        if not ret:
            return None
        
         # Oscurecer fondo para mejor legibilidad del texto
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Título
        y_pos = frame.shape[0] // 3
        cv2.putText(frame, "Bienvenido a GeoKids", (frame.shape[1]//2 - 200, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
        
        # Opciones
        y_pos += 100
        cv2.putText(frame, "Pulse 1 para iniciar sesion", (frame.shape[1]//2 - 150, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        y_pos += 60
        cv2.putText(frame, "Pulse 2 para registrarte", (frame.shape[1]//2 - 150, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        y_pos += 100
        cv2.putText(frame, "Pulse ESC para salir", (frame.shape[1]//2 - 120, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 255), 1)
        
        cv2.imshow("GeoKids AR", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC para salir
            return None
        elif key == ord('1'):
            return 'iniciar_sesion'
        elif key == ord('2'):
            return 'registrar'

def inicializar_aplicacion():
    """
    Inicializa la cámara y carga las preguntas desde un archivo JSON.
    Retorna: objeto VideoCapture y diccionario con preguntas.
    """
    cap = cv2.VideoCapture(0)
    
    # Ajustar resolución de captura
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Cargar preguntas desde archivo JSON; si falla, cargar datos por defecto
    try:
        with open("datos/preguntas.json", "r", encoding="utf-8") as f:
            preguntas = json.load(f)
    except Exception:
        preguntas = {"modo_test": {"1": {"10": {"figura": "forma_generica", "preguntas": []}}}}
    
    return cap, preguntas


        
def mostrar_pregunta(frame, pregunta, correcta=None):
    """
    Muestra una pregunta con sus opciones en la imagen de la cámara.
    """
    overlay = frame.copy()
    # Fondo oscuro para la zona de texto
    cv2.rectangle(overlay, (20, 20), (frame.shape[1] - 20, 220), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    y_pos = 50
    # Mostrar enunciado de la pregunta
    cv2.putText(frame, pregunta["pregunta"], (50, y_pos), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Mostrar opciones numeradas
    for i, opcion in enumerate(pregunta["opciones"]):
        y_pos += 40
        cv2.putText(frame, f"{i+1}. {opcion}", (70, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    y_pos += 60
    cv2.putText(frame, "Presiona 1-4 para responder o 'v' para voz", 
               (50, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 255), 1)
    
    # Mostrar feedback de respuesta correcta/incorrecta si se pasa parámetro correcta
    if correcta is not None:
        color = (0, 255, 0) if correcta else (0, 0, 255)
        texto = "Correcto" if correcta else "Incorrecto"
        cv2.putText(frame, texto, (frame.shape[1]//2 - 100, y_pos + 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

def mostrar_resultado_nivel(frame, nivel, correctas, total, usuario=None, base_preguntas=None):
    """
    Muestra estadísticas del nivel completado y opciones de navegación
    Integra el manejo completo de estadísticas del primer código
    """
    porcentaje = (correctas / total) * 100
    overlay = frame.copy()
    cv2.rectangle(overlay, (50, 50), (frame.shape[1] - 50, frame.shape[0] - 50), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

    y_pos = 100
    # Título
    cv2.putText(frame, f"RESULTADOS NIVEL {nivel}", (frame.shape[1]//2 - 200, y_pos),
               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

    y_pos += 80
    # Estadísticas principales
    cv2.putText(frame, f"Respuestas correctas: {correctas}/{total}", (frame.shape[1]//2 - 180, y_pos),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    y_pos += 50
    cv2.putText(frame, f"Porcentaje de acierto: {porcentaje:.1f}%", (frame.shape[1]//2 - 180, y_pos),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Guardar progreso del usuario 
    if usuario:
        usuarios = reconocedor_cara.cargar_usuarios()
        if usuario in usuarios:
            if "progreso" not in usuarios[usuario]:
                usuarios[usuario]["progreso"] = {}
            
            # Guardar estadísticas del nivel
            usuarios[usuario]["progreso"][str(nivel)] = {
                "correctas": correctas,
                "total": total,
                "porcentaje": porcentaje,
                "completado": True
            }
            
            # Actualizar nivel del usuario si cumple requisitos - LÓGICA DEL PRIMER CÓDIGO
            if nivel == 1 and porcentaje >= 70:
                usuarios[usuario]["nivel"] = max(usuarios[usuario].get("nivel", 1), 2)
                print(f"Usuario {usuario} ha avanzado al nivel 2")
            elif nivel == 2 and porcentaje >= 70:
                usuarios[usuario]["nivel"] = max(usuarios[usuario].get("nivel", 2), 1)
                print(f"Usuario {usuario} ha superado el último nivel")
            
            reconocedor_cara.guardar_usuarios(usuarios)

    y_pos += 80
    
    # Verificar si hay más niveles disponibles
    niveles_disponibles = list(base_preguntas.get("modo_test", {}).keys()) if base_preguntas else []
    max_nivel = max([int(n) for n in niveles_disponibles]) if niveles_disponibles else 1
    es_ultimo_nivel = nivel >= max_nivel
    
    # Determinar si puede avanzar 
    puede_avanzar = False
    mensaje_nivel = ""
    
    if not es_ultimo_nivel:
        if nivel == 1:
            if porcentaje >= 70:
                puede_avanzar = True
                mensaje_nivel = "Felicidades. Pasas al nivel 2"
                color_mensaje = (0, 255, 0)
            else:
                mensaje_nivel = "Sigue practicando. Repetirás el nivel 1"
                color_mensaje = (0, 165, 255)
        elif nivel == 2:
            if porcentaje >= 70:
                puede_avanzar = True
                mensaje_nivel = "Excelente. Puedes avanzar al siguiente nivel"
                color_mensaje = (0, 255, 0)
            else:
                mensaje_nivel = "Necesitas ≥70% para avanzar al siguiente nivel"
                color_mensaje = (0, 165, 255)
        else:
            if porcentaje >= 70:
                puede_avanzar = True
                mensaje_nivel = "Excelente.Puedes avanzar al siguiente nivel"
                color_mensaje = (0, 255, 0)
            else:
                mensaje_nivel = "Necesitas ≥70% para avanzar al siguiente nivel"
                color_mensaje = (0, 165, 255)
    else:
        # Es el último nivel 
        if porcentaje >= 70:
            mensaje_nivel = "FELICITACIONES. Has completado todos los niveles"
            color_mensaje = (0, 255, 0)
        else:
            mensaje_nivel = "Puedes seguir practicando este nivel"
            color_mensaje = (255, 255, 0)

    cv2.putText(frame, mensaje_nivel, (frame.shape[1]//2 - 300, y_pos),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_mensaje, 2)

    y_pos += 80
    
    # Opciones disponibles 
    cv2.putText(frame, "OPCIONES DISPONIBLES:", (frame.shape[1]//2 - 150, y_pos),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 255), 2)
    
    y_pos += 40
    opciones_texto = []
    
    # Opciones con voz y teclado
    opciones_texto.append("R / 'reiniciar' - Repetir este nivel")
    
    if puede_avanzar and not es_ultimo_nivel:
        opciones_texto.append("S / 'siguiente' - Siguiente nivel")
    
    opciones_texto.append("ESC / 'salir' - Salir del juego")
    
    for opcion in opciones_texto:
        cv2.putText(frame, opcion, (frame.shape[1]//2 - 200, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        y_pos += 30

    cv2.imshow("GeoKids AR", frame)

    # Loop para capturar la decisión del usuario 
    while True:
        key = cv2.waitKey(1) & 0xFF
        
        # Tecla ESC para salir
        if key == 27:
            return "salir"
        
        # Tecla R para repetir
        if key == ord('r'):
            return "reiniciar"
        
        # Tecla S para siguiente (solo if puede avanzar y no es el último nivel)
        if key == ord('s') and puede_avanzar and not es_ultimo_nivel:
            return "siguiente"
        

def mostrar_estadisticas_usuario(frame, usuario):
    """
    Muestra estadísticas generales del usuario 
    """
    
    usuarios = reconocedor_cara.cargar_usuarios()
    if usuario not in usuarios or "progreso" not in usuarios[usuario]:
        return
    
    progreso = usuarios[usuario]["progreso"]
    
    # Dibujar un recuadro oscuro para mostrar las estadísticas
    overlay = frame.copy()
    cv2.rectangle(overlay, (100, 100), (frame.shape[1] - 100, 400), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
    
    # Título de la sección
    y_pos = 150
    cv2.putText(frame, f"Estadisticas de {usuario}", (frame.shape[1]//2 - 150, y_pos),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Mostrar estadísticas por cada nivel
    y_pos += 50
    for nivel_str, stats in progreso.items():
        nivel_num = int(nivel_str)
        porcentaje = stats.get("porcentaje", 0)
        correctas = stats.get("correctas", 0)
        total = stats.get("total", 0)
        cv2.putText(frame, f"Nivel {nivel_num}: {correctas}/{total} ({porcentaje:.1f}%)", 
                   (frame.shape[1]//2 - 120, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        y_pos += 40

def manejar_fin_de_nivel(frame, nivel_actual, respuestas_correctas, total_preguntas, usuario, base_preguntas):
    """
    Maneja el flujo cuando se completa un nivel 
    """
    accion = mostrar_resultado_nivel(frame, nivel_actual, respuestas_correctas, total_preguntas, usuario, base_preguntas)
    
    if accion == "salir":
        return "salir", nivel_actual
    
    elif accion == "reiniciar":
        return "repetir", nivel_actual
    
    elif accion == "siguiente":
        # Calcular nivel máximo definido en preguntas.json
        niveles_disponibles = list(base_preguntas.get("modo_test", {}).keys()) if base_preguntas else []
        max_nivel = max([int(n) for n in niveles_disponibles]) if niveles_disponibles else 1
        
        # Si se ha completado el último nivel
        if nivel_actual >= max_nivel:
            # Manejo completo de final de juego
            print("Has completado todos los niveles.")
            while True:
                # Mostrar pantalla final del juego
                overlay = frame.copy()
                cv2.rectangle(overlay, (100, 200), (frame.shape[1] - 100, 400), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
                
                # Mensaje final y opciones
                cv2.putText(frame, "JUEGO COMPLETADO", (frame.shape[1]//2 - 150, 250),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
                cv2.putText(frame, "¿Quieres reiniciar desde el nivel 1?", (frame.shape[1]//2 - 200, 300),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(frame, "R / 'reiniciar' - Volver al nivel 1", (frame.shape[1]//2 - 180, 330),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
                cv2.putText(frame, "ESC / 'salir' - Terminar juego", (frame.shape[1]//2 - 180, 360),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
                
                cv2.imshow("GeoKids AR", frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == 27:  # ESC
                    return "salir", nivel_actual
                elif key == ord('r'):  # R
                    return "repetir", 1
                
        else:
            # Avanzar al siguiente nivel
            return "siguiente", nivel_actual + 1
    
    return "repetir", nivel_actual

def resetear_estado_juego():
    """
    Resetea todas las variables del estado del juego
    """
    return {
        "preguntas": [],
        "pregunta_actual": None,
        "figura_actual": None,
        "respuestas_correctas": 0,
        "feedback": None,
        "feedback_tiempo": 0
    }

def normalizar(texto):
    """
    Limpia y estandariza el texto eliminando mayúsculas y acentos.
    """
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFD', texto)
    return ''.join(c for c in texto if unicodedata.category(c) != 'Mn')

def procesar_respuesta(estado, respuesta_idx, nivel_actual):
    """
    Procesa una respuesta del usuario y actualiza el estado del juego
    """
    # Validación de índice
    if respuesta_idx < 0 or respuesta_idx >= len(estado["pregunta_actual"]["opciones"]):
        return

    opcion_seleccionada = estado["pregunta_actual"]["opciones"][respuesta_idx]
    respuesta_correcta = estado["pregunta_actual"]["respuesta_correcta"]
    
    # Comparación usando texto normalizado
    es_correcta = normalizar(opcion_seleccionada) == normalizar(respuesta_correcta)

    print(f"\nRespuesta: {opcion_seleccionada}")
    print(f"{' Correcta' if es_correcta else ' Incorrecta'}")

    estado["feedback"] = es_correcta
    estado["feedback_tiempo"] = 30

    if es_correcta:
        estado["respuestas_correctas"] += 1

    # Avanzar a siguiente pregunta
    pregunta_actual_idx = estado["preguntas"].index(estado["pregunta_actual"])
    siguiente_idx = pregunta_actual_idx + 1

    if siguiente_idx < len(estado["preguntas"]):
        # Cargar siguiente pregunta y su figura visual
        estado["pregunta_actual"] = estado["preguntas"][siguiente_idx]
        estado["figura_actual"] = estado["pregunta_actual"]["figura_visual"]

        # Imprimir en terminal
        print(f"\nNivel {nivel_actual} - Pregunta {siguiente_idx + 1}/{len(estado['preguntas'])}:")
        print(estado["pregunta_actual"]["pregunta"])
        for i, op in enumerate(estado["pregunta_actual"]["opciones"]):
            print(f"{i+1}. {op}")
    else:
         # Si no hay más preguntas, terminar nivel
        estado["pregunta_actual"] = None
        estado["figura_actual"] = None
        print(f"\nNivel {nivel_actual} completado")
        print(f"Respuestas correctas: {estado['respuestas_correctas']}/{len(estado['preguntas'])}")

def main():
    cap, base_preguntas = inicializar_aplicacion()
    usuario = None
    nivel_actual = 1
    estado = resetear_estado_juego()

    # Crea una ventana para mostrar el juego
    cv2.namedWindow("GeoKids AR", cv2.WINDOW_NORMAL)

    try:
        # Mostrar menú inicial 
        opcion_menu = mostrar_menu_inicial(cap)

        if opcion_menu == 'iniciar_sesion':
            print("Modo iniciar sesion seleccionado")
            ret, frame = cap.read()
            if not ret:
                print("Error al acceder a la cámara.")
                return
            try:
                # Intenta identificar al usuario por reconocimiento facial
                usuario = reconocedor_cara.identificar_usuario(frame)
                if not usuario:
                    print("No se pudo identificar al usuario.")
                    print("Pulse boton 2 para registrarse")
                    opcion_menu = mostrar_menu_inicial(cap)
            except Exception as e:
                print(f"Error al identificar usuario: {str(e)}")
                

        elif opcion_menu == 'registrar':
            print("Modo registro seleccionado")
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Error al capturar el frame de la cámara.")
                return
            # Registra un nuevo usuario
            usuario = reconocedor_cara.registrar_usuario(frame)


        else:
            # Si se elige salir
            cap.release()
            cv2.destroyAllWindows()
            return

        # Verificar usuario
        if usuario:
            usuarios = reconocedor_cara.cargar_usuarios()
            if usuario in usuarios:
                nivel_actual = usuarios[usuario].get("nivel", 1)
            else:
                nivel_actual = 1

            print(f"Usuario identificado: {usuario}")
            print(f"Nivel actual del usuario: {nivel_actual}")

            # Mostrar estadísticas solo si tenemos un frame válido
            ret, frame = cap.read()
            if ret:
                mostrar_estadisticas_usuario(frame, usuario)
                cv2.imshow("GeoKids AR", frame)
                cv2.waitKey(2000)
            else:
                print("No se pudo obtener un frame para mostrar estadísticas.")

        else:
            print("No se pudo obtener un usuario válido. Saliendo...")
            cap.release()
            cv2.destroyAllWindows()
            return

        # Bucle principal del juego
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Detectar marcador
            marcador = detector_marcadores.obtener_marcador_por_id(frame, 10, dibujar=True, estimar_pose=True)

            # Cargar preguntas si no se han cargado aún
            if marcador and usuario and not estado["preguntas"]:
                try:
                    if str(nivel_actual) in base_preguntas["modo_test"]:
                        estado["preguntas"] = base_preguntas["modo_test"][str(nivel_actual)]["10"]["preguntas"]
                        estado["respuestas_correctas"] = 0
                        estado["pregunta_actual"] = estado["preguntas"][0]
                        estado["figura_actual"] = estado["pregunta_actual"]["figura_visual"]

                        print(f"\n=== INICIANDO NIVEL {nivel_actual} ===")
                        print(f"Total de preguntas: {len(estado['preguntas'])}")
                        print(f"\nPregunta 1/{len(estado['preguntas'])}:")
                        print(estado["pregunta_actual"]["pregunta"])
                        for i, op in enumerate(estado["pregunta_actual"]["opciones"]):
                            print(f"{i+1}. {op}")
                    else:
                        print(f"Nivel {nivel_actual} no encontrado.")
                        estado["preguntas"] = []
                except Exception as e:
                    print(f"Error al cargar preguntas: {str(e)}")
                    estado["preguntas"] = []

            # Mostrar figura si hay marcador
            if marcador:
                if estado["figura_actual"] == "cubo":

                    frame = dibujar_cubo(
                        frame, marcador.rvec, marcador.tvec, 
                        marcador.matriz_camara, marcador.coef_distorsion,
                        tamano=0.05
                    )
                if estado["figura_actual"] == "piramide":

                    frame = dibujar_piramide(
                        frame,marcador.rvec, marcador.tvec,
                        marcador.matriz_camara, marcador.coef_distorsion,
                        tamano=0.05)
                else:
                    # Otras figuras 2D
                    cx = int(sum(p[0] for p in marcador.esquinas) / 4)
                    cy = int(sum(p[1] for p in marcador.esquinas) / 4)
                    mostrar_figura(frame, estado["figura_actual"], (cx, cy))

            # Mostrar pregunta y manejar respuestas
            if estado["pregunta_actual"]:
                mostrar_pregunta(frame, estado["pregunta_actual"],
                                 estado["feedback"] if estado["feedback_tiempo"] > 0 else None)

                if estado["feedback_tiempo"] > 0:
                    estado["feedback_tiempo"] -= 1

                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC para salir
                    break

                # Teclado (1-4)
                elif 49 <= key <= 52:
                    respuesta_seleccionada = key - 49
                    procesar_respuesta(estado, respuesta_seleccionada, nivel_actual)

                    if estado["pregunta_actual"] is None:
                        accion, nuevo_nivel = manejar_fin_de_nivel(
                            frame, nivel_actual, estado["respuestas_correctas"],
                            len(estado["preguntas"]), usuario, base_preguntas
                        )

                        if accion == "salir":
                            break
                        elif accion in ("repetir", "siguiente"):
                            nivel_actual = min(nuevo_nivel, 2)
                            estado = resetear_estado_juego()

                # Reconocimiento por voz
                elif key == ord('v'):
                    try:
                        respuesta_voz = reconocedor_voz.procesar_respuesta(estado["pregunta_actual"])
                        if respuesta_voz and hasattr(respuesta_voz, 'texto'):
                            print(f"\nVoz detectada: {respuesta_voz.texto}")
                            print(f"{' Correcta' if respuesta_voz.es_correcta else ' Incorrecta'}")

                            estado["feedback"] = respuesta_voz.es_correcta
                            estado["feedback_tiempo"] = 30

                            if respuesta_voz.es_correcta:
                                estado["respuestas_correctas"] += 1

                            idx = estado["preguntas"].index(estado["pregunta_actual"]) + 1
                            if idx < len(estado["preguntas"]):
                                estado["pregunta_actual"] = estado["preguntas"][idx]
                                estado["figura_actual"] = estado["pregunta_actual"]["figura_visual"]
                                print(f"\nNivel {nivel_actual} - Pregunta {idx + 1}/{len(estado['preguntas'])}:")
                                print(estado["pregunta_actual"]["pregunta"])
                                for i, op in enumerate(estado["pregunta_actual"]["opciones"]):
                                    print(f"{i+1}. {op}")
                            else:
                                estado["pregunta_actual"] = None
                                estado["figura_actual"] = None
                                print(f"\nNivel {nivel_actual} completado")
                                print(f"Respuestas correctas: {estado['respuestas_correctas']}/{len(estado['preguntas'])}")

                                accion, nuevo_nivel = manejar_fin_de_nivel(
                                    frame, nivel_actual, estado["respuestas_correctas"],
                                    len(estado["preguntas"]), usuario, base_preguntas
                                )

                                if accion == "salir":
                                    break
                                elif accion in ("repetir", "siguiente"):
                                    nivel_actual = min(nuevo_nivel, 2)
                                    estado = resetear_estado_juego()
                    except Exception as e:
                        print(f"Error en reconocimiento de voz: {str(e)}")
                        estado["feedback"] = False
                        estado["feedback_tiempo"] = 30

            # Muestra el frame con la interfaz del juego
            cv2.imshow("GeoKids AR", frame)

    finally:
         # Libera recursos al salir
        cap.release()
        cv2.destroyAllWindows()
# Ejecuta el programa
if __name__ == "__main__":
    main()
