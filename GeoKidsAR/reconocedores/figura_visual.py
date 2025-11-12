import cv2
import numpy as np

def mostrar_figura(frame, nombre_figura, posicion, tamano=100):
    """
    Muestra una figura geométrica en la posición especificada
    Args:
        frame: Imagen donde dibujar
        nombre_figura: Nombre de la figura a dibujar
        posicion: Tupla (x, y) con las coordenadas centrales
        tamano: Tamaño base de la figura (por defecto 100)
    """
    cx, cy = posicion
    
    if nombre_figura == "cuadrado":
        cv2.rectangle(frame, (cx - tamano, cy - tamano), 
                     (cx + tamano, cy + tamano), (0, 255, 0), -1)
    elif nombre_figura == "rectangulo":
        cv2.rectangle(frame, (cx - int(tamano*1.5), cy - tamano), 
                     (cx + int(tamano*1.5), cy + tamano), (255, 0, 0), -1)
    elif nombre_figura == "triangulo":
        pts = np.array([[cx, cy - tamano], 
                       [cx - tamano, cy + tamano], 
                       [cx + tamano, cy + tamano]], np.int32)
        cv2.fillPoly(frame, [pts], (0, 0, 255))
    elif nombre_figura == "circulo":
        cv2.circle(frame, (cx, cy), tamano, (255, 255, 0), -1)
    elif nombre_figura == "trapecio":
        # Puntos corregidos para el trapecio
        pts = np.array([
            [cx - int(tamano*1.2), cy - int(tamano*0.6)],  # Esquina superior izquierda
            [cx + int(tamano*1.2), cy - int(tamano*0.6)],  # Esquina superior derecha
            [cx + int(tamano*0.8), cy + int(tamano*0.6)],  # Esquina inferior derecha
            [cx - int(tamano*0.8), cy + int(tamano*0.6)]   # Esquina inferior izquierda
        ], np.int32)
        cv2.fillPoly(frame, [pts], (128, 0, 255))
    elif nombre_figura == "rombo":
        pts = np.array([[cx, cy - tamano], 
                       [cx + int(tamano*0.8), cy], 
                       [cx, cy + tamano], 
                       [cx - int(tamano*0.8), cy]], np.int32)
        cv2.fillPoly(frame, [pts], (0, 255, 255))
    elif nombre_figura == "pentagono":
        pts = np.array([[cx, cy - tamano], 
                       [cx + int(tamano*0.95), cy - int(tamano*0.3)], 
                       [cx + int(tamano*0.6), cy + int(tamano*0.9)], 
                       [cx - int(tamano*0.6), cy + int(tamano*0.9)], 
                       [cx - int(tamano*0.95), cy - int(tamano*0.3)]], np.int32)
        cv2.fillPoly(frame, [pts], (255, 150, 0))
    elif nombre_figura == "hexagono":
        pts = np.array([[cx - int(tamano*0.6), cy - tamano], 
                       [cx + int(tamano*0.6), cy - tamano], 
                       [cx + int(tamano*1.2), cy], 
                       [cx + int(tamano*0.6), cy + tamano], 
                       [cx - int(tamano*0.6), cy + tamano], 
                       [cx - int(tamano*1.2), cy]], np.int32)
        cv2.fillPoly(frame, [pts], (0, 128, 255))
    elif nombre_figura == "forma_generica":
        cv2.putText(frame, "Figura", (cx - tamano, cy), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (200, 200, 200), 4)
        
import cv2
import numpy as np

def dibujar_cubo(frame, rvec, tvec, matriz_camara, coef_distorsion, tamano=0.05, color=(255, 0, 0), alpha=0.4):
    # Definir vértices del cubo en coordenadas 3D
    mitad = tamano / 2
    puntos_objeto = np.float32([
        [-mitad, -mitad, 0],
        [ mitad, -mitad, 0],
        [ mitad,  mitad, 0],
        [-mitad,  mitad, 0],
        [-mitad, -mitad, tamano],
        [ mitad, -mitad, tamano],
        [ mitad,  mitad, tamano],
        [-mitad,  mitad, tamano],
    ])

    # Proyectar puntos 3D a la imagen
    puntos_img, _ = cv2.projectPoints(puntos_objeto, rvec, tvec, matriz_camara, coef_distorsion)
    puntos_img = puntos_img.reshape(-1, 2).astype(int)

    # Definir las caras del cubo (índices en sentido antihorario)
    caras = [
        [0, 1, 2, 3],  # base
        [4, 5, 6, 7],  # top
        [0, 1, 5, 4],  # lateral frente
        [1, 2, 6, 5],  # lateral derecha
        [2, 3, 7, 6],  # lateral atrás
        [3, 0, 4, 7],  # lateral izquierda
    ]

    # Dibujar las caras con relleno semitransparente
    overlay = frame.copy()
    for cara in caras:
        pts = puntos_img[cara].reshape((-1, 1, 2))
        cv2.fillConvexPoly(overlay, pts, color)

    # Aplicar transparencia
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    # Dibujar las aristas por encima
    aristas = [
        (0, 1), (1, 2), (2, 3), (3, 0),  # base
        (4, 5), (5, 6), (6, 7), (7, 4),  # top
        (0, 4), (1, 5), (2, 6), (3, 7)   # verticales
    ]
    for i, j in aristas:
        cv2.line(frame, tuple(puntos_img[i]), tuple(puntos_img[j]), (0, 0, 0), 2)

    return frame

def dibujar_piramide(frame, rvec, tvec, matriz_camara, coef_distorsion, tamano=0.05, altura=0.05, color=(0, 255, 0), alpha=0.5):
    mitad = tamano / 2

    # Vértices 3D de la base y el vértice superior
    puntos_objeto = np.float32([
        [-mitad, -mitad, 0],  # 0: esquina inferior izquierda
        [ mitad, -mitad, 0],  # 1: esquina inferior derecha
        [ mitad,  mitad, 0],  # 2: esquina superior derecha
        [-mitad,  mitad, 0],  # 3: esquina superior izquierda
        [    0,     0,  altura]  # 4: vértice superior (punta)
    ])

    # Proyectar a la imagen
    puntos_img, _ = cv2.projectPoints(puntos_objeto, rvec, tvec, matriz_camara, coef_distorsion)
    puntos_img = puntos_img.reshape(-1, 2).astype(int)

    # Caras (base cuadrada y 4 triángulos)
    caras = [
        [0, 1, 2, 3],    # base
        [0, 1, 4],       # frente
        [1, 2, 4],       # derecha
        [2, 3, 4],       # atrás
        [3, 0, 4]        # izquierda
    ]

    overlay = frame.copy()

    # Dibujar caras
    for cara in caras:
        pts = puntos_img[cara].reshape((-1, 1, 2))
        cv2.fillConvexPoly(overlay, pts, color)

    # Transparencia
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    # Dibujar líneas por encima
    aristas = [
        (0, 1), (1, 2), (2, 3), (3, 0),  # base
        (0, 4), (1, 4), (2, 4), (3, 4)   # lados hacia la punta
    ]
    for i, j in aristas:
        cv2.line(frame, tuple(puntos_img[i]), tuple(puntos_img[j]), (0, 0, 0), 2)

    return frame
