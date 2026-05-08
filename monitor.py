import cv2
import numpy as np

CAMERA_INDEX = 1

cap = cv2.VideoCapture(CAMERA_INDEX)

AREAS = {

    "LED VERDE": {
        "rect": (106, 78, 32, 34),
        "cor": "verde",
        "botao": 1
    },

    "LED VERMELHO": {
        "rect": (246, 220, 33, 32),
        "cor": "vermelho",
        "botao": 2
    },

    "LED AMARELO": {
        "rect": (404, 110, 40, 43),
        "cor": "amarelo",
        "botao": 3
    },

    "LED AZUL": {
        "rect": (536, 242, 33, 32),
        "cor": "verde",
        "botao": 4
    }
}

ultimo_estado = {
    nome: None
    for nome in AREAS
}

# brilho médio dos LEDs apagados
brilho_base = {
    nome: None
    for nome in AREAS
}


def detectar_cor_roi(roi, cor_esperada, nome):

    hsv = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2HSV
    )

    h, s, v = cv2.split(hsv)

    brilho_medio = np.mean(v)

    if brilho_base[nome] is None:
        brilho_base[nome] = brilho_medio

    diferenca_brilho = (
        brilho_medio - brilho_base[nome]
    )

    mascaras = {}

    # VERDE
    mascaras["verde"] = cv2.inRange(
        hsv,
        np.array([40, 120, 200]),
        np.array([85, 255, 255])
    )

    # VERMELHO
    vermelho1 = cv2.inRange(
        hsv,
        np.array([0, 120, 200]),
        np.array([10, 255, 255])
    )

    vermelho2 = cv2.inRange(
        hsv,
        np.array([170, 120, 200]),
        np.array([180, 255, 255])
    )

    mascaras["vermelho"] = (
        vermelho1 + vermelho2
    )

    # AMARELO
    mascaras["amarelo"] = cv2.inRange(
        hsv,
        np.array([20, 120, 200]),
        np.array([35, 255, 255])
    )

    # AZUL
    mascaras["azul"] = cv2.inRange(
        hsv,
        np.array([90, 120, 200]),
        np.array([130, 255, 255])
    )

    pixels_detectados = cv2.countNonZero(
        mascaras[cor_esperada]
    )

    total_pixels = (
        roi.shape[0] * roi.shape[1]
    )

    percentual = (
        pixels_detectados / total_pixels
    )

    # precisa ter cor E brilho
    if (
        percentual > 0.04
        and diferenca_brilho > 25
    ):

        return (
            "ON",
            percentual,
            brilho_medio,
            diferenca_brilho
        )

    return (
        "OFF",
        percentual,
        brilho_medio,
        diferenca_brilho
    )


print("Monitorando areas...")
print("Aperte Q para sair")
print(
    "Aperte R para recalibrar "
    "com LEDs apagados"
)

while True:

    ret, frame = cap.read()

    if not ret:
        print("Erro webcam")
        break

    for nome, dados in AREAS.items():

        x, y, w, h = dados["rect"]

        cor_esperada = dados["cor"]

        roi = frame[
            y:y+h,
            x:x+w
        ]

        estado, percentual, brilho, diff = detectar_cor_roi(
            roi,
            cor_esperada,
            nome
        )

        # LOGA APENAS QUANDO MUDA
        if estado != ultimo_estado[nome]:

            print(
                f"{nome}: {estado} | "
                f"cor={percentual:.3f} | "
                f"brilho={brilho:.1f} | "
                f"diff={diff:.1f}"
            )

            ultimo_estado[nome] = estado

        cor_borda = (
            (0, 255, 0)
            if estado == "ON"
            else (0, 0, 255)
        )

        cv2.rectangle(
            frame,
            (x, y),
            (x+w, y+h),
            cor_borda,
            2
        )

        cv2.putText(
            frame,
            f"{nome}: {estado}",
            (x, y - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            cor_borda,
            1
        )

    cv2.imshow(
        "Detector Genius",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    elif key == ord("r"):

        brilho_base = {
            nome: None
            for nome in AREAS
        }

        print(
            "Recalibrando... "
            "deixe todos os LEDs apagados"
        )

cap.release()

cv2.destroyAllWindows()