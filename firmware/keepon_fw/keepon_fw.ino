// Firmware del robot Keepon pro (ESP32-C3-DevKitM-1, núcleo Arduino-ESP32 3.x).
//
// Esta capa solo hace lo que depende del hardware: el puerto serie (CH340, 115200 baud), los pulsos
// de los servos y el tono del buzzer. Toda la lógica (protocolo de docs/PROTOCOLO.md, trayectoria,
// STOP, watchdog y sonidos) está en nucleo.cpp, que se prueba en la notebook contra keepon/sim_esp32.py
// (tests/test_firmware_nucleo.py). Los parámetros salen de config.yaml vía generado.h
// (scripts/generar_firmware.py).
//
// No bloqueante: no hay delay(). El lazo de trayectoria avanza de a 10 ms con millis().

#include <Arduino.h>

#include "nucleo.h"

// --- Pines (docs/REVISION_CODEX_HW.md; evitar 2/8/9 de strapping, 18/19 del USB y 20/21 del UART0) ---
const uint8_t PIN_SERVO[3] = {0, 1, 4};  // yaw, pitch, roll
const uint8_t PIN_BUZZER = 10;

// --- PWM. Servos y buzzer en timers LEDC distintos: cambiar la nota no altera el pulso de los servos.
// Los tres servos (50 Hz, 14 bits) comparten un timer; el buzzer se configura con otra frecuencia y
// resolución, así que el núcleo le asigna otro timer libre, y ledcWriteTone() solo cambia ese.
const uint32_t SERVO_HZ = 50;
const uint8_t SERVO_BITS = 14;            // 1,22 µs por paso de duty
const float PERIODO_US = 1000000.0f / SERVO_HZ;
const uint8_t CANAL_SERVO[3] = {0, 1, 2};
const uint8_t CANAL_BUZZER = 4;
const uint32_t BUZZER_HZ_INICIAL = 2000;
const uint8_t BUZZER_BITS = 10;

const size_t BUF_RX = 128;                // más largo que MAX_LINEA: lo que no entra es TOO_LONG

keepon::Nucleo nucleo;
char rx[BUF_RX];
size_t n_rx = 0;
bool rx_desbordado = false;
uint32_t t_paso = 0;                      // instante del último paso del lazo [ms]
uint16_t f_buzzer = 0;                    // frecuencia que está sonando [Hz]

void escribir_servos() {
  uint16_t us[3];
  nucleo.pulsos(us);
  for (int i = 0; i < 3; i++) {
    ledcWrite(PIN_SERVO[i], (uint32_t)(us[i] * (float)(1UL << SERVO_BITS) / PERIODO_US + 0.5f));
  }
}

void enviar_respuestas() {
  if (nucleo.largo_salida()) {
    Serial.write((const uint8_t *)nucleo.salida(), nucleo.largo_salida());
    nucleo.vaciar_salida();
  }
}

void setup() {
  Serial.setTxBufferSize(1024);           // las respuestas no frenan el lazo
  Serial.begin(115200);
  for (int i = 0; i < 3; i++) ledcAttachChannel(PIN_SERVO[i], SERVO_HZ, SERVO_BITS, CANAL_SERVO[i]);
  ledcAttachChannel(PIN_BUZZER, BUZZER_HZ_INICIAL, BUZZER_BITS, CANAL_BUZZER);
  // El módulo del buzzer (MH-FMD) se activa por nivel bajo: su transistor PNP conduce con el I/O en 0 V.
  // Con la salida invertida, duty 0 (callado) deja el pin en ALTO y el buzzer sin corriente; si no,
  // callado sería 0 V fijo y la bobina quedaría con corriente continua. Las notas (50 %) no cambian.
  ledcOutputInvert(PIN_BUZZER, true);
  ledcWrite(PIN_BUZZER, 0);

  // Arranca en HOME. Los servos no tienen realimentación: el primer pulso los lleva a HOME a toda
  // velocidad desde donde hayan quedado (el HS-7955TG salta). Por eso se enciende con la cabeza cerca
  // de HOME y los 6 V después que la Pi (README de docs/keepon_v4_cad).
  t_paso = millis();
  nucleo.reiniciar(t_paso);
  escribir_servos();
  enviar_respuestas();                    // "HELLO 0 fw proto": la Pi sabe que el ESP32 (re)arrancó
}

void leer_serie() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c != '\n') {
      if (n_rx < BUF_RX - 1) rx[n_rx++] = c;
      else rx_desbordado = true;
      continue;
    }
    rx[n_rx] = '\0';
    if (rx_desbordado) nucleo.linea_demasiado_larga(millis());
    else nucleo.linea(rx, millis());
    n_rx = 0;
    rx_desbordado = false;
    enviar_respuestas();
  }
}

void loop() {
  leer_serie();

  // Lazo de trayectoria a 100 Hz. Si se atrasó (no debería), recupera hasta 10 pasos y después se resincroniza.
  uint32_t ahora = millis();
  int pasos = 0;
  while (ahora - t_paso >= keepon::PASO_MS && pasos < 10) {
    t_paso += keepon::PASO_MS;
    nucleo.paso(t_paso);
    pasos++;
  }
  if (pasos) {
    if (ahora - t_paso >= keepon::PASO_MS) t_paso = ahora;
    escribir_servos();                    // en STOP y watchdog se sigue mandando el pulso (el MG996R sin pulso queda flojo)
    enviar_respuestas();
  }

  // Buzzer: solo se toca el timer cuando cambia la nota.
  uint16_t f = nucleo.frecuencia(millis());
  if (f != f_buzzer) {
    ledcWriteTone(PIN_BUZZER, f);         // 0 = callado
    f_buzzer = f;
  }
}
