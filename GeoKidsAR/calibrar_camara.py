import cv2
import numpy as np
import time
import cv2.aruco as aruco

# Configuración del detector ArUco
DICCIONARIO = aruco.getPredefinedDictionary(aruco.DICT_4X4_250)
PARAMS = aruco.DetectorParameters()
PARAMS.cornerRefinementMethod = aruco.CORNER_REFINE_SUBPIX
DETECTOR = aruco.ArucoDetector(DICCIONARIO, PARAMS)

# Tamaño del marcador en metros (ajusta según tu impresión real)
MARKER_SIZE = 0.05  # 5cm - ajusta según el tamaño real de tu marcador impreso

# Definir las esquinas 3D del marcador (en coordenadas del objeto)
def get_marker_3d_points(marker_size):
    half_size = marker_size / 2
    return np.array([
        [-half_size, -half_size, 0],
        [half_size, -half_size, 0],
        [half_size, half_size, 0],
        [-half_size, half_size, 0]
    ], dtype=np.float32)

CPS = 0.5  # capturas cada 2 segundos para dar tiempo a mover el marcador
object_points = []  # puntos 3D en el mundo real
image_points = []   # puntos 2D en la imagen
tiempo = 1.0 / CPS

# Puntos 3D del marcador
marker_3d_points = get_marker_3d_points(MARKER_SIZE)

cap = cv2.VideoCapture(0)

if cap.isOpened():
    wframe = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    hframe = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    final = False
    n = 0
    antes = time.time()

    print("=== CALIBRACIÓN DE CÁMARA CON ARUCO ===")
    print("Instrucciones:")
    print("1. Mantén el marcador ArUco visible frente a la cámara")
    print("2. Mueve el marcador a diferentes posiciones y ángulos")
    print("3. El sistema capturará automáticamente cada 2 segundos")
    print("4. Necesitas al menos 10-15 capturas para una buena calibración")
    print("5. Presiona ESC para finalizar y calibrar")
    print("6. Presiona 'r' para resetear y empezar de nuevo")
    print()

    while not final:
        ret, frame = cap.read()
        if not ret:
            final = True
            break

        # Detectar marcadores ArUco
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejectedImgPoints = DETECTOR.detectMarkers(gray)
        
        # Dibujar marcadores detectados
        if ids is not None and len(ids) > 0:
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            
            # Capturar puntos si ha pasado el tiempo suficiente
            if time.time() - antes > tiempo:
                # Tomar el primer marcador detectado
                corner = corners[0]  # corners[0] es el primer marcador
                corner_reshaped = corner.reshape(4, 2)  # Reshape para tener formato correcto
                
                # Agregar puntos a las listas
                object_points.append(marker_3d_points)
                image_points.append(corner_reshaped)
                n += 1
                antes = time.time()
                
                print(f"Captura {n} realizada - ID detectado: {ids[0][0]}")
                
                # Feedback visual
                cv2.circle(frame, (int(corner_reshaped[0][0]), int(corner_reshaped[0][1])), 10, (0, 255, 0), -1)
        
        # Información en pantalla
        cv2.putText(frame, f"Capturas: {n}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Minimo recomendado: 15", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        if n < 15:
            cv2.putText(frame, "Mueve el marcador a diferentes posiciones", (50, 130), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        else:
            cv2.putText(frame, "Suficientes capturas - Presiona ESC para calibrar", (50, 130), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.imshow("Calibracion ArUco", frame)

        key = cv2.waitKey(20) & 0xFF
        if key == 27:  # ESC para salir
            final = True
        elif key == ord('r'):  # Reset
            object_points = []
            image_points = []
            n = 0
            print("Reset realizado - empezando de nuevo")

    cap.release()
    cv2.destroyAllWindows()

    if n < 5:
        print(f"Error: Solo se capturaron {n} imágenes. Se necesitan al menos 5 para calibrar.")
    else:
        print(f"Iniciando calibración con {n} capturas...")
        
        # Verificar que los datos tienen el formato correcto
        print(f"Formato object_points: {len(object_points)} elementos")
        print(f"Formato image_points: {len(image_points)} elementos")
        if len(object_points) > 0:
            print(f"Shape de object_points[0]: {object_points[0].shape}")
            print(f"Shape de image_points[0]: {image_points[0].shape}")

        # Estimación inicial de parámetros intrínsecos
        cameraMatrixInit = np.array([[wframe, 0, wframe / 2],
                                     [0, wframe, hframe / 2],
                                     [0, 0, 1]], dtype=np.float64)
        distCoeffsInit = np.zeros((5, 1))

        # Flags para calibración
        flags = (cv2.CALIB_USE_INTRINSIC_GUESS + 
                cv2.CALIB_RATIONAL_MODEL + 
                cv2.CALIB_FIX_ASPECT_RATIO)

        try:
            # Calibración de la cámara
            ret, cameraMatrix, distCoeffs, rvecs, tvecs = cv2.calibrateCamera(
                objectPoints=object_points,
                imagePoints=image_points,
                imageSize=(wframe, hframe),
                cameraMatrix=cameraMatrixInit,
                distCoeffs=distCoeffsInit,
                flags=flags
            )

            if ret:
                # Calcular error de reproyección
                total_error = 0
                for i in range(len(object_points)):
                    imgpoints2, _ = cv2.projectPoints(object_points[i], rvecs[i], tvecs[i], 
                                                    cameraMatrix, distCoeffs)
                    imgpoints2 = imgpoints2.reshape(-1, 2)
                    error = cv2.norm(image_points[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
                    total_error += error

                mean_error = total_error / len(object_points)
                
                print(f"Calibración completada exitosamente!")
                print(f"Error medio de reproyección: {mean_error:.3f} píxeles")
                
                if mean_error < 1.0:
                    print("¡Excelente calibración!")
                elif mean_error < 2.0:
                    print("Buena calibración")
                else:
                    print("Calibración aceptable, pero podrías mejorarla con más capturas")

                # Guardar parámetros de calibración
                with open('camara.py', 'w') as f:
                    f.write("import numpy as np\n\n")
                    f.write("# Parámetros de calibración de la cámara\n")
                    f.write(f"# Resolución utilizada: {wframe}x{hframe}\n")
                    f.write(f"# Error medio de reproyección: {mean_error:.3f} píxeles\n")
                    f.write(f"# Número de capturas utilizadas: {n}\n\n")
                    f.write(f"cameraMatrix = np.array({repr(cameraMatrix.tolist())})\n")
                    f.write(f"distCoeffs = np.array({repr(distCoeffs.tolist())})\n\n")
                    f.write(f"# Tamaño de imagen\n")
                    f.write(f"imageSize = ({wframe}, {hframe})\n")
                
                print("Parámetros guardados en 'camara.py'")
                
                # Mostrar matriz de cámara
                print("\nMatriz de cámara:")
                print(cameraMatrix)
                print("\nCoeficientes de distorsión:")
                print(distCoeffs.ravel())
                
            else:
                print("Error: La calibración falló.")
                
        except Exception as e:
            print(f"Error durante la calibración: {e}")
            print("Intentando con parámetros más simples...")
            
            # Intentar calibración más simple
            try:
                flags_simple = cv2.CALIB_USE_INTRINSIC_GUESS
                ret, cameraMatrix, distCoeffs, rvecs, tvecs = cv2.calibrateCamera(
                    objectPoints=object_points,
                    imagePoints=image_points,
                    imageSize=(wframe, hframe),
                    cameraMatrix=cameraMatrixInit,
                    distCoeffs=distCoeffsInit,
                    flags=flags_simple
                )
                
                if ret:
                    print("Calibración simple exitosa!")
                    
                    # Guardar parámetros de calibración
                    with open('camara.py', 'w') as f:
                        f.write("import numpy as np\n\n")
                        f.write("# Parámetros de calibración de la cámara (calibración simple)\n")
                        f.write(f"# Resolución utilizada: {wframe}x{hframe}\n")
                        f.write(f"# Número de capturas utilizadas: {n}\n\n")
                        f.write(f"cameraMatrix = np.array({repr(cameraMatrix.tolist())})\n")
                        f.write(f"distCoeffs = np.array({repr(distCoeffs.tolist())})\n\n")
                        f.write(f"# Tamaño de imagen\n")
                        f.write(f"imageSize = ({wframe}, {hframe})\n")
                    
                    print("Parámetros guardados en 'camara.py'")
                else:
                    print("Error: También falló la calibración simple.")
                    
            except Exception as e2:
                print(f"Error en calibración simple: {e2}")

else:
    print("Error: No se pudo abrir la cámara.")
    print("Verifica que:")
    print("1. La cámara esté conectada")
    print("2. No esté siendo usada por otra aplicación")
    print("3. Tienes permisos para acceder a la cámara")