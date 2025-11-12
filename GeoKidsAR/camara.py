import numpy as np

# Parámetros de calibración de la cámara
# Resolución utilizada: 640x480
# Error medio de reproyección: 0.225 píxeles
# Número de capturas utilizadas: 20

cameraMatrix = np.array([[668.9921186764669, 0.0, 230.57869967908437], [0.0, 668.9921186764669, 142.632889363315], [0.0, 0.0, 1.0]])
distCoeffs = np.array([[-4.0014590444927824], [23.07436720471521], [0.00041236626207114403], [-0.00017920689507846884], [-61.461148276597925], [-4.0624060876642565], [25.499974704659685], [-68.33886753621606], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0]])

# Tamaño de imagen
imageSize = (640, 480)
