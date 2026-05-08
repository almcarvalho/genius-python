import cv2
import numpy as np
import time
import random
import serial

CAMERA_INDEX = 0

ARDUINO_PORT = "COM3"
BAUDRATE = 9600

cap = cv2.VideoCapture(CAMERA_INDEX)

arduino = serial.Serial(
    ARDUINO_PORT,
    BAUDRATE,
    timeout=1
)

time.sleep(2)

TEMPO_IGNORAR_INICIO = 3.0
TEMPO_SEM_FLASH = 0.55
TEMPO_ANTES_DE_RESPONDER = 0.25
TEMPO_ENTRE_BOTOES = 0.45
DEBOUNCE_LED = 0.25
TEMPO_MAX_SEM_JOGADA = 10

AREAS = {

    "LED VERDE": {
        "rect": (162, 170, 19, 22),
        "cor": "verde",
        "botao": 1
    },

    "LED VERMELHO": {
        "rect": (226, 224, 15, 20),
        "cor": "vermelho",
        "botao": 2
    },

    "LED AMARELO": {
        "rect": (287, 182, 22, 19),
        "cor": "amarelo",
        "botao": 3
    },

    # LED físico verde no lugar do azul
    "LED AZUL": {
        "rect": (348, 233, 10, 13),
        "cor": "verde",
        "botao": 4
    }
}

ultimo_estado = {
    nome: "OFF"
    for nome in AREAS
}

ultimo_flash_led = {
    nome: 0
    for nome in AREAS
}

brilho_base = {
    nome: None
    for nome in AREAS
}

sequencia_atual = []

ultimo_flash = 0
ultimo_evento_jogo = time.time()

monitorando = False
respondendo = False

tempo_inicio_programa = time.time()


def pressionar_botao(numero):

    try:

        comando = f"{numero}\n"

        arduino.write(
            comando.encode()
        )

        arduino.flush()

        print(f"SERIAL -> BOTAO {numero}")

    except Exception as e:

        print(f"ERRO SERIAL BOTAO {numero}: {e}")


def reiniciar_jogo():

    global sequencia_atual
    global monitorando
    global respondendo
    global tempo_inicio_programa
    global ultimo_estado
    global ultimo_flash_led
    global ultimo_evento_jogo

    print("\n================================")
    print("REINICIANDO JOGO")
    print("================================\n")

    sequencia_atual.clear()

    monitorando = False
    respondendo = False

    ultimo_estado = {
        nome: "OFF"
        for nome in AREAS
    }

    ultimo_flash_led = {
        nome: 0
        for nome in AREAS
    }

    time.sleep(1)

    botao = random.randint(1, 4)

    print(
        f"Iniciando novamente com botão {botao}"
    )

    pressionar_botao(botao)

    tempo_inicio_programa = time.time()

    ultimo_evento_jogo = time.time()


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

    mascaras["verde"] = cv2.inRange(
        hsv,
        np.array([40, 120, 200]),
        np.array([85, 255, 255])
    )

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

    mascaras["amarelo"] = cv2.inRange(
        hsv,
        np.array([20, 120, 200]),
        np.array([35, 255, 255])
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

    if (
        percentual > 0.04
        and diferenca_brilho > 25
    ):

        return "ON"

    return "OFF"


def tocar_sequencia(sequencia):

    global respondendo
    global ultimo_evento_jogo

    respondendo = True

    print("\n==============================")
    print("REPETINDO:", sequencia)
    print("==============================")

    time.sleep(TEMPO_ANTES_DE_RESPONDER)

    for botao in sequencia:

        pressionar_botao(botao)

        time.sleep(TEMPO_ENTRE_BOTOES)

    print("SEQUENCIA ENVIADA\n")

    ultimo_evento_jogo = time.time()

    respondendo = False


print("Detector Genius iniciado")
print("Controle direto pela COM3")
print("O programa vai apertar um botão aleatório para começar")
print("Q = sair | R = recalibrar")

time.sleep(1)

botao_inicial = random.randint(1, 4)

print(
    f"Iniciando com botão aleatório: "
    f"{botao_inicial}"
)

pressionar_botao(botao_inicial)

tempo_inicio_programa = time.time()

while True:

    ret, frame = cap.read()

    if not ret:
        print("Erro webcam")
        break

    agora = time.time()

    if (
        not monitorando
        and agora - tempo_inicio_programa
        > TEMPO_IGNORAR_INICIO
    ):

        monitorando = True

        sequencia_atual.clear()

        ultimo_estado = {
            nome: "OFF"
            for nome in AREAS
        }

        print("\nMONITORANDO JOGO...\n")

    leds_ligados = []

    for nome, dados in AREAS.items():

        x, y, w, h = dados["rect"]

        cor_esperada = dados["cor"]

        roi = frame[
            y:y+h,
            x:x+w
        ]

        estado = detectar_cor_roi(
            roi,
            cor_esperada,
            nome
        )

        if estado == "ON":
            leds_ligados.append(nome)

        # erro: múltiplos LEDs
        if (
            len(leds_ligados) >= 2
            and monitorando
            and not respondendo
        ):

            print(
                "\nERRO: múltiplos LEDs detectados"
            )

            reiniciar_jogo()

            break

        # transição OFF -> ON
        if (
            estado == "ON"
            and ultimo_estado[nome] == "OFF"
        ):

            tempo_desde_ultimo = (
                agora - ultimo_flash_led[nome]
            )

            if (
                tempo_desde_ultimo
                > DEBOUNCE_LED
            ):

                ultimo_flash_led[nome] = agora

                if (
                    monitorando
                    and not respondendo
                ):

                    botao = dados["botao"]

                    sequencia_atual.append(botao)

                    ultimo_flash = agora

                    ultimo_evento_jogo = agora

                    print(
                        f"DETECTADO: "
                        f"{nome} -> {botao}"
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

    # terminou sequência
    if (
        monitorando
        and not respondendo
        and len(sequencia_atual) > 0
    ):

        tempo_sem_novo_flash = (
            time.time() - ultimo_flash
        )

        if (
            tempo_sem_novo_flash
            > TEMPO_SEM_FLASH
        ):

            sequencia_para_tocar = (
                sequencia_atual.copy()
            )

            sequencia_atual.clear()

            tocar_sequencia(
                sequencia_para_tocar
            )

    # travou / ficou parado
    if (
        monitorando
        and not respondendo
        and time.time() - ultimo_evento_jogo
        > TEMPO_MAX_SEM_JOGADA
    ):

        print(
            "\nTempo máximo sem jogada atingido"
        )

        reiniciar_jogo()

    cv2.imshow(
        "Detector Genius Bot",
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

        reiniciar_jogo()

        print(
            "Recalibrado e reiniciado."
        )

cap.release()

arduino.close()

cv2.destroyAllWindows()