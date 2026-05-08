import cv2
import numpy as np
import time
import random
import serial

CAMERA_INDEX = 1

ARDUINO_PORT = "COM3"
BAUDRATE = 9600

cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 60)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

arduino = serial.Serial(
    ARDUINO_PORT,
    BAUDRATE,
    timeout=0,
    write_timeout=0
)

time.sleep(2)

TEMPO_IGNORAR_INICIO = 3.0

TEMPO_ANTES_DE_RESPONDER = 1.0
TEMPO_ENTRE_BOTOES = 0.55

# PAUSA EXTRA QUANDO REPETE O MESMO BOTÃO
TEMPO_EXTRA_BOTAO_REPETIDO = 0.25

DEBOUNCE_LED = 0.16
TEMPO_MIN_ENTRE_MESMO_LED = 0.28

TEMPO_MAX_SEM_JOGADA = 15

TEMPO_SEM_FLASH_MIN = 1.45
TEMPO_SEM_FLASH_NIVEL_MEDIO = 1.70
TEMPO_SEM_FLASH_NIVEL_ALTO = 1.95
TEMPO_SEM_FLASH_NIVEL_EXTREMO = 2.20

NIVEL_MEDIO = 8
NIVEL_ALTO = 18
NIVEL_EXTREMO = 28

LIMIAR_BRILHO = 24
LIMIAR_PERCENTUAL = 0.035

AREAS = {

    "LED VERDE": {
        "rect": (36, 82, 47, 48),
        "cor": "verde",
        "botao": 1
    },

    "LED VERMELHO": {
        "rect": (198, 256, 37, 47),
        "cor": "vermelho",
        "botao": 2
    },

    "LED AMARELO": {
        "rect": (396, 129, 37, 52),
        "cor": "amarelo",
        "botao": 3
    },

    "LED AZUL": {
        "rect": (579, 302, 40, 47),
        "cor": "verde",
        "botao": 4
    }
}

ultimo_estado = {nome: False for nome in AREAS}
ultimo_flash_led = {nome: 0 for nome in AREAS}
brilho_base = {nome: None for nome in AREAS}
brilho_anterior = {nome: 0 for nome in AREAS}

sequencia_atual = []

ultimo_flash = 0
ultimo_evento_jogo = time.perf_counter()

monitorando = False
respondendo = False

tempo_inicio_programa = time.perf_counter()


def agora():
    return time.perf_counter()


def tempo_sem_flash_atual():
    nivel = len(sequencia_atual)

    if nivel >= NIVEL_EXTREMO:
        return TEMPO_SEM_FLASH_NIVEL_EXTREMO

    if nivel >= NIVEL_ALTO:
        return TEMPO_SEM_FLASH_NIVEL_ALTO

    if nivel >= NIVEL_MEDIO:
        return TEMPO_SEM_FLASH_NIVEL_MEDIO

    return TEMPO_SEM_FLASH_MIN


def pressionar_botao(numero):
    try:
        comando = f"{numero}\n"

        arduino.write(comando.encode())

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
    global ultimo_flash
    global brilho_base
    global brilho_anterior

    print("\n================================")
    print("REINICIANDO JOGO")
    print("================================\n")

    sequencia_atual.clear()

    monitorando = False
    respondendo = False

    ultimo_estado = {nome: False for nome in AREAS}
    ultimo_flash_led = {nome: 0 for nome in AREAS}
    brilho_base = {nome: None for nome in AREAS}
    brilho_anterior = {nome: 0 for nome in AREAS}

    ultimo_flash = 0

    time.sleep(1)

    botao = random.randint(1, 4)

    print(f"Iniciando novamente com botão {botao}")

    pressionar_botao(botao)

    tempo_inicio_programa = agora()
    ultimo_evento_jogo = agora()


def detectar_led(frame, nome, dados):
    x, y, w, h = dados["rect"]
    cor_esperada = dados["cor"]

    roi = frame[y:y+h, x:x+w]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    h_channel = hsv[:, :, 0]
    s_channel = hsv[:, :, 1]
    v_channel = hsv[:, :, 2]

    brilho_medio = float(np.mean(v_channel))

    if brilho_base[nome] is None:
        brilho_base[nome] = brilho_medio
        brilho_anterior[nome] = brilho_medio
        return False, brilho_medio, 0

    diferenca_brilho = brilho_medio - brilho_base[nome]

    if cor_esperada == "verde":
        mask = (
            (h_channel >= 38) &
            (h_channel <= 98) &
            (s_channel >= 55) &
            (v_channel >= 100)
        )

    elif cor_esperada == "vermelho":
        mask = (
            (
                ((h_channel >= 0) & (h_channel <= 14)) |
                ((h_channel >= 166) & (h_channel <= 180))
            ) &
            (s_channel >= 55) &
            (v_channel >= 100)
        )

    elif cor_esperada == "amarelo":
        mask = (
            (h_channel >= 15) &
            (h_channel <= 45) &
            (s_channel >= 55) &
            (v_channel >= 100)
        )

    else:
        return False, brilho_medio, diferenca_brilho

    pixels_detectados = int(np.count_nonzero(mask))
    percentual = pixels_detectados / (w * h)

    ligado = (
        percentual > LIMIAR_PERCENTUAL
        and diferenca_brilho > LIMIAR_BRILHO
    )

    return ligado, brilho_medio, diferenca_brilho


def registrar_flash(nome, botao, t):
    global ultimo_flash
    global ultimo_evento_jogo

    sequencia_atual.append(botao)

    ultimo_flash_led[nome] = t
    ultimo_flash = t
    ultimo_evento_jogo = t

    print(
        f"DETECTADO: {nome} -> {botao} | "
        f"tamanho={len(sequencia_atual)}"
    )


def tocar_sequencia(sequencia):
    global respondendo
    global ultimo_evento_jogo

    respondendo = True

    nivel = len(sequencia)

    print("\n==============================")
    print("REPETINDO:", sequencia)
    print("NIVEL:", nivel)
    print("==============================")

    time.sleep(TEMPO_ANTES_DE_RESPONDER)

    intervalo = TEMPO_ENTRE_BOTOES

    if nivel >= 30:
        intervalo = 0.35

    elif nivel >= 20:
        intervalo = 0.40

    elif nivel >= 10:
        intervalo = 0.48

    botao_anterior = None

    for botao in sequencia:

        pressionar_botao(botao)

        # PAUSA EXTRA PARA BOTÃO REPETIDO
        if botao == botao_anterior:
            pausa = intervalo + TEMPO_EXTRA_BOTAO_REPETIDO

            print(
                f"BOTAO REPETIDO {botao} -> "
                f"PAUSA EXTRA {pausa:.2f}s"
            )

            time.sleep(pausa)

        else:
            time.sleep(intervalo)

        botao_anterior = botao

    print("SEQUENCIA ENVIADA\n")

    ultimo_evento_jogo = agora()
    respondendo = False


print("Detector Genius iniciado")
print("Q = sair | R = recalibrar")

time.sleep(1)

botao_inicial = random.randint(1, 4)

print(f"Iniciando com botão aleatório: {botao_inicial}")

pressionar_botao(botao_inicial)

tempo_inicio_programa = agora()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Erro webcam")
        break

    t = agora()

    if (
        not monitorando
        and t - tempo_inicio_programa > TEMPO_IGNORAR_INICIO
    ):
        monitorando = True
        sequencia_atual.clear()

        ultimo_estado = {nome: False for nome in AREAS}
        ultimo_flash_led = {nome: 0 for nome in AREAS}
        brilho_anterior = {nome: 0 for nome in AREAS}
        ultimo_flash = 0

        print("\nMONITORANDO JOGO...\n")

    leds_ligados = []

    for nome, dados in AREAS.items():

        ligado, brilho_medio, diferenca_brilho = detectar_led(
            frame,
            nome,
            dados
        )

        if ligado:
            leds_ligados.append(nome)

        if monitorando and not respondendo:

            botao = dados["botao"]

            tempo_desde_ultimo = t - ultimo_flash_led[nome]

            subida_brilho = brilho_medio - brilho_anterior[nome]

            novo_flash_por_transicao = (
                ligado
                and not ultimo_estado[nome]
                and tempo_desde_ultimo > DEBOUNCE_LED
            )

            novo_flash_por_pico = (
                ligado
                and ultimo_estado[nome]
                and subida_brilho > 18
                and tempo_desde_ultimo > TEMPO_MIN_ENTRE_MESMO_LED
            )

            if (
                novo_flash_por_transicao
                or novo_flash_por_pico
            ):
                registrar_flash(nome, botao, t)

        ultimo_estado[nome] = ligado
        brilho_anterior[nome] = brilho_medio

        x, y, w, h = dados["rect"]

        cor_borda = (0, 255, 0) if ligado else (0, 0, 255)

        cv2.rectangle(
            frame,
            (x, y),
            (x+w, y+h),
            cor_borda,
            2
        )

        cv2.putText(
            frame,
            f"{nome}: {'ON' if ligado else 'OFF'}",
            (x, y - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            cor_borda,
            1
        )

    if (
        len(leds_ligados) >= 2
        and monitorando
        and not respondendo
    ):
        print("\nERRO: múltiplos LEDs detectados")
        reiniciar_jogo()
        continue

    todos_apagados = len(leds_ligados) == 0

    if (
        monitorando
        and not respondendo
        and len(sequencia_atual) > 0
        and todos_apagados
        and ultimo_flash > 0
    ):
        tempo_sem_novo_flash = t - ultimo_flash
        tempo_espera = tempo_sem_flash_atual()

        if tempo_sem_novo_flash > tempo_espera:

            sequencia_para_tocar = sequencia_atual.copy()

            sequencia_atual.clear()

            tocar_sequencia(sequencia_para_tocar)

    if (
        monitorando
        and not respondendo
        and agora() - ultimo_evento_jogo > TEMPO_MAX_SEM_JOGADA
    ):
        print("\nTempo máximo sem jogada atingido")
        reiniciar_jogo()

    cv2.imshow("Detector Genius Bot", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    elif key == ord("r"):

        brilho_base = {nome: None for nome in AREAS}
        brilho_anterior = {nome: 0 for nome in AREAS}

        reiniciar_jogo()

        print("Recalibrado e reiniciado.")

cap.release()
arduino.close()
cv2.destroyAllWindows()