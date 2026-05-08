#define RELE_VERDE    2
#define RELE_VERMELHO 3
#define RELE_AMARELO  4
#define RELE_AZUL     5

#define TEMPO_PRESSIONADO 180
#define TEMPO_SOLTO       80

void setup() {
  Serial.begin(9600);

  pinMode(RELE_VERDE, OUTPUT);
  pinMode(RELE_VERMELHO, OUTPUT);
  pinMode(RELE_AMARELO, OUTPUT);
  pinMode(RELE_AZUL, OUTPUT);

  desligarTodos();

  Serial.println("READY");
}

void loop() {
  if (Serial.available() > 0) {
    char comando = Serial.read();

    if (comando == '\n' || comando == '\r' || comando == ' ') {
      return;
    }

    switch (comando) {

      case '1':
        acionarRele(RELE_VERDE);
        Serial.println("OK 1");
        break;

      case '2':
        acionarRele(RELE_VERMELHO);
        Serial.println("OK 2");
        break;

      case '3':
        acionarRele(RELE_AMARELO);
        Serial.println("OK 3");
        break;

      case '4':
        acionarRele(RELE_AZUL);
        Serial.println("OK 4");
        break;

      default:
        Serial.print("ERRO ");
        Serial.println(comando);
        break;
    }
  }
}

void acionarRele(int pino) {
  desligarTodos();

  digitalWrite(pino, HIGH);
  delay(TEMPO_PRESSIONADO);

  digitalWrite(pino, LOW);
  delay(TEMPO_SOLTO);
}

void desligarTodos() {
  digitalWrite(RELE_VERDE, LOW);
  digitalWrite(RELE_VERMELHO, LOW);
  digitalWrite(RELE_AMARELO, LOW);
  digitalWrite(RELE_AZUL, LOW);
}
