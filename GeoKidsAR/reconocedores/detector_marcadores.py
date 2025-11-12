import cv2
import cv2.aruco as aruco
import numpy as np
import os
from cuia import  popup, proyeccion  # Importamos las utilidades de cuia.py
from camara import cameraMatrix, distCoeffs

# Configuración ArUco
DICCIONARIO = aruco.getPredefinedDictionary(aruco.DICT_4X4_250)
PARAMS = aruco.DetectorParameters()
PARAMS.cornerRefinementMethod = aruco.CORNER_REFINE_SUBPIX
DETECTOR = aruco.ArucoDetector(DICCIONARIO, PARAMS)

# Usar los parámetros reales de calibración
MATRIZ_CAMARA = cameraMatrix
COEF_DISTORSION = distCoeffs

class Marcador:
    """
    Representa un marcador ArUco detectado en la imagen.
    Contiene su ID, esquinas detectadas, centro calculado y vectores de pose 3D (rvec, tvec).
    """
    def __init__(self, id, esquinas):
        self.id = id
        self.esquinas = esquinas
        self.centro = self._calcular_centro()
        self.rvec = None
        self.tvec = None
        self.tamano = 0.05  # Cambiar a 5cm (igual que en tu calibración)
        # Agregar los parámetros de cámara como atributos del marcador
        self.matriz_camara = MATRIZ_CAMARA
        self.coef_distorsion = COEF_DISTORSION
        
    def _calcular_centro(self):
        """Calcula el centro promedio de las esquinas del marcador"""
        return np.mean(self.esquinas, axis=0)
    
    def estimar_pose(self, matriz_camara=None, coef_distorsion=None):
        """Estima la pose del marcador """
        # Usar parámetros del objeto si no se proporcionan otros
        if matriz_camara is None:
            matriz_camara = self.matriz_camara
        if coef_distorsion is None:
            coef_distorsion = self.coef_distorsion
            
        obj_points = np.array([[-self.tamano/2, self.tamano/2, 0],
                              [self.tamano/2, self.tamano/2, 0],
                              [self.tamano/2, -self.tamano/2, 0],
                              [-self.tamano/2, -self.tamano/2, 0]], dtype=np.float32)
        
        ret, self.rvec, self.tvec = cv2.solvePnP(obj_points, 
                                                self.esquinas.astype(np.float32),
                                                matriz_camara, 
                                                coef_distorsion)
        return ret

def cargar_imagen_marcador(id_marcador, mostrar=True):
    """Carga y muestra la imagen del marcador """
    ruta = os.path.join("datos", "marcadores", f"aruco_{id_marcador}.png")
    img = cv2.imread(ruta) if os.path.exists(ruta) else None
    if img is not None and mostrar:
        popup(f"Marcador {id_marcador}", img)
    return img

def detectar_marcadores(frame, dibujar=True, estimar_pose=False):
    """Calcula la posición y orientación del marcador"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    esquinas, ids, _ = DETECTOR.detectMarkers(gray)
    
    marcadores = []
    if ids is not None:
        for i in range(len(ids)):
            marcador = Marcador(int(ids[i][0]), esquinas[i][0])
            
            if estimar_pose:
                marcador.estimar_pose()
                if dibujar:
                    cv2.drawFrameAxes(frame, MATRIZ_CAMARA, COEF_DISTORSION,
                                    marcador.rvec, marcador.tvec, 0.05)
            
            marcadores.append(marcador)
            
            if dibujar:
                cv2.aruco.drawDetectedMarkers(frame, [esquinas[i]], np.array([ids[i]]))
                info = f"ID: {marcador.id}"
                cv2.putText(frame, info, 
                          (int(marcador.centro[0]), int(marcador.centro[1]) - 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    return marcadores

def obtener_marcador_por_id(frame, id_buscado, dibujar=True, estimar_pose=True):
    """
    Busca un marcador específico y opcionalmente estima su pose 3D
    """
    marcadores = detectar_marcadores(frame, dibujar, estimar_pose)
    for m in marcadores:
        if m.id == id_buscado:
            if dibujar:
                cv2.drawMarker(frame, 
                             (int(m.centro[0]), int(m.centro[1])),
                             (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
                if estimar_pose and m.rvec is not None:
                    # Proyectar información 3D usando la función proyeccion de cuia.py
                    texto_pos = f"Pos: {m.tvec.flatten()[:3].round(2)}"
                    punto_texto = proyeccion([0, 0, 0], m.rvec, m.tvec, MATRIZ_CAMARA, COEF_DISTORSION)
                    cv2.putText(frame, texto_pos, 
                              (int(punto_texto[0]), int(punto_texto[1])),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            return m
    return None