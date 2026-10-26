// Prueba de banco del módulo de buzzer pasivo (MH-FMD) en el GPIO10 de la ESP32-C3.
// Separa el hardware del firmware: repite cada 4 s
//   1) 1 s de tono de 2 kHz hecho a mano con digitalWrite (sin LEDC): si no suena, es el cableado o el módulo;
//   2) 1 s de silencio con el pin en ALTO (el módulo se activa por nivel bajo);
//   3) 1 s de tono de 2 kHz por LEDC con la salida invertida, igual que el firmware del robot;
//   4) 1 s de silencio.
// Cada etapa se anuncia por el puerto serie (115200). Conexión: VCC → 3V3, I/O → GPIO10, GND → GND.
// Para volver al robot, cargar otra vez firmware/keepon_fw (bash scripts/cargar_firmware.sh --local).

const uint8_t PIN_BUZZER = 10;
const uint32_t FREC_HZ = 2000;

void tono_a_mano(uint32_t ms) {
  pinMode(PIN_BUZZER, OUTPUT);
  uint32_t medio_us = 500000UL / FREC_HZ;
  uint32_t fin = millis() + ms;
  while ((int32_t)(millis() - fin) < 0) {
    digitalWrite(PIN_BUZZER, LOW);
    delayMicroseconds(medio_us);
    digitalWrite(PIN_BUZZER, HIGH);
    delayMicroseconds(medio_us);
  }
  digitalWrite(PIN_BUZZER, HIGH);       // callado = ALTO
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, HIGH);
}

void loop() {
  Serial.println("1 tono a mano (digitalWrite)");
  tono_a_mano(1000);

  Serial.println("2 silencio");
  delay(1000);

  Serial.println("3 tono LEDC invertido");
  ledcAttach(PIN_BUZZER, FREC_HZ, 10);
  ledcOutputInvert(PIN_BUZZER, true);
  ledcWriteTone(PIN_BUZZER, FREC_HZ);
  delay(1000);
  ledcWriteTone(PIN_BUZZER, 0);         // invertido: duty 0 = pin en ALTO

  Serial.println("4 silencio");
  delay(1000);
  ledcDetach(PIN_BUZZER);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, HIGH);
}
