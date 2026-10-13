// Prueba de banco de servos para Keepon (ESP32-C3-DevKitM-1, núcleo Arduino-ESP32 3.x).
//
// No es el firmware del robot: sirve para comprobar que cada servo funciona,
// medir sus pulsos útiles (grados por µs, extremos, centro) y probar el conexionado.
// Se maneja por el monitor serie a 115200 baud, con fin de línea "Nueva línea".
// Instrucciones y planilla de resultados en ../README.md.
//
// Los servos arrancan SIN pulso (flojos). Un servo empieza a moverse recién
// cuando recibe una orden; la primera vez salta al pulso pedido, porque el
// ESP32 no sabe en qué posición quedó el servo. Por eso: primero sin carga.

#include <Arduino.h>

// --- Pines y PWM (recomendados en docs/REVISION_CODEX_HW.md, sección C) ---
const int NUM_EJES = 3;
const int PINES[NUM_EJES] = {0, 1, 4};                  // GPIO de la señal
const char *NOMBRES[NUM_EJES] = {"yaw", "pitch", "roll"};
const uint32_t FREC_HZ = 50;                             // los servos esperan un pulso cada 20 ms
const uint8_t RES_BITS = 14;                             // 1,22 µs por paso de duty
const float PERIODO_US = 1000000.0f / FREC_HZ;           // 20000 µs
const float PASOS_DUTY = (float)(1UL << RES_BITS);

// Límites absolutos: ningún comando puede salir de acá, aunque se cambien los límites.
const int LIM_ABS_MIN = 500;
const int LIM_ABS_MAX = 2500;

const uint32_t PERIODO_LAZO_MS = 10;                     // rampa a 100 Hz, igual que la trayectoria del robot

struct Eje {
  bool activo;      // true = emite pulsos; false = servo flojo
  float pos_us;     // pulso que se está emitiendo
  float obj_us;     // pulso al que se quiere llegar
  int min_us;       // límites de esta prueba (empiezan conservadores)
  int max_us;
  bool barrido;     // ida y vuelta entre bar_a y bar_b
  int bar_a;
  int bar_b;
};

Eje ejes[NUM_EJES];
int sel = 0;                  // eje seleccionado
float vel_us_s = 300.0f;      // velocidad de la rampa en µs/s (~54 °/s si 0,18 °/µs)
uint32_t t_ant_ms = 0;
char linea[64];
int largo = 0;

// Convierte µs de pulso a duty de LEDC y lo escribe. Duty 0 = sin pulso.
void escribir(int i) {
  uint32_t duty = 0;
  if (ejes[i].activo) {
    duty = (uint32_t)(ejes[i].pos_us * PASOS_DUTY / PERIODO_US + 0.5f);
  }
  ledcWrite(PINES[i], duty);
}

int recortar(int us, const Eje &e) {
  if (us < e.min_us) return e.min_us;
  if (us > e.max_us) return e.max_us;
  return us;
}

void estado() {
  Serial.printf("vel=%.0f us/s  seleccionado=%d (%s)\n", vel_us_s, sel, NOMBRES[sel]);
  for (int i = 0; i < NUM_EJES; i++) {
    const Eje &e = ejes[i];
    Serial.printf("  %d %-5s GPIO%d %s pos=%.0f obj=%.0f lim=[%d,%d]%s\n", i, NOMBRES[i], PINES[i],
                  e.activo ? "ON " : "OFF", e.pos_us, e.obj_us, e.min_us, e.max_us,
                  e.barrido ? " barriendo" : "");
  }
}

void ayuda() {
  Serial.println("Comandos (el eje es el seleccionado con 'e'):");
  Serial.println("  e <0|1|2>       seleccionar eje (0 yaw GPIO0, 1 pitch GPIO1, 2 roll GPIO4)");
  Serial.println("  p <us>          ir al pulso <us> con rampa (recortado a los limites)");
  Serial.println("  c               ir al centro (1500 us)");
  Serial.println("  + / -           mover 10 us (para buscar extremos y banda muerta)");
  Serial.println("  b <us1> <us2>   barrido continuo ida y vuelta");
  Serial.println("  s               detener barrido (mantiene la posicion)");
  Serial.println("  o               apagar pulsos de este eje (servo flojo)");
  Serial.println("  O               apagar todos los ejes");
  Serial.println("  v <us/s>        velocidad de la rampa (20..5000)");
  Serial.println("  l <min> <max>   limites del eje (dentro de 500..2500)");
  Serial.println("  ?               estado      h  esta ayuda");
}

// Ordena ir a un pulso. Si el eje estaba apagado, arranca directamente ahí (salto inevitable).
void ir_a(int us) {
  Eje &e = ejes[sel];
  us = recortar(us, e);
  if (!e.activo) {
    e.activo = true;
    e.pos_us = us;
  }
  e.obj_us = us;
  e.barrido = false;
  Serial.printf("%s -> %d us\n", NOMBRES[sel], us);
}

void procesar(char *cmd) {
  int a = 0, b = 0;
  Eje &e = ejes[sel];
  switch (cmd[0]) {
    case 'e':
      if (sscanf(cmd + 1, "%d", &a) == 1 && a >= 0 && a < NUM_EJES) {
        sel = a;
        Serial.printf("eje %d (%s), GPIO%d\n", sel, NOMBRES[sel], PINES[sel]);
      } else Serial.println("ERR: e <0|1|2>");
      break;
    case 'p':
      if (sscanf(cmd + 1, "%d", &a) == 1) ir_a(a);
      else Serial.println("ERR: p <us>");
      break;
    case 'c': ir_a(1500); break;
    case '+': ir_a((int)(e.activo ? e.obj_us : 1500) + 10); break;
    case '-': ir_a((int)(e.activo ? e.obj_us : 1500) - 10); break;
    case 'b':
      if (sscanf(cmd + 1, "%d %d", &a, &b) == 2) {
        a = recortar(a, e);
        b = recortar(b, e);
        ir_a(a);
        e.barrido = true;
        e.bar_a = a;
        e.bar_b = b;
        Serial.printf("barrido %d <-> %d us\n", a, b);
      } else Serial.println("ERR: b <us1> <us2>");
      break;
    case 's':
      e.barrido = false;
      e.obj_us = e.pos_us;
      Serial.printf("barrido detenido en %.0f us\n", e.pos_us);
      break;
    case 'o':
      e.activo = false;
      e.barrido = false;
      Serial.printf("%s apagado\n", NOMBRES[sel]);
      break;
    case 'O':
      for (int i = 0; i < NUM_EJES; i++) {
        ejes[i].activo = false;
        ejes[i].barrido = false;
      }
      Serial.println("todos apagados");
      break;
    case 'v':
      if (sscanf(cmd + 1, "%d", &a) == 1 && a >= 20 && a <= 5000) {
        vel_us_s = a;
        Serial.printf("vel = %d us/s\n", a);
      } else Serial.println("ERR: v <20..5000>");
      break;
    case 'l':
      if (sscanf(cmd + 1, "%d %d", &a, &b) == 2 && LIM_ABS_MIN <= a && a < b && b <= LIM_ABS_MAX) {
        e.min_us = a;
        e.max_us = b;
        Serial.printf("%s limites [%d, %d] us\n", NOMBRES[sel], a, b);
      } else Serial.println("ERR: l <min> <max>, dentro de 500..2500");
      break;
    case '?': estado(); break;
    case 'h': ayuda(); break;
    default: Serial.println("comando desconocido (h = ayuda)");
  }
}

// Lee el puerto serie sin bloquear y procesa cada línea completa.
void leer_serie() {
  while (Serial.available() > 0) {
    char ch = (char)Serial.read();
    if (ch == '\r') continue;
    if (ch == '\n') {
      linea[largo] = '\0';
      if (largo > 0) procesar(linea);
      largo = 0;
    } else if (largo < (int)sizeof(linea) - 1) {
      linea[largo++] = ch;
    }
  }
}

// Avanza cada eje hacia su objetivo a velocidad constante (rampa) y escribe el PWM.
void paso_rampa(float dt) {
  float max_paso = vel_us_s * dt;
  for (int i = 0; i < NUM_EJES; i++) {
    Eje &e = ejes[i];
    if (e.activo) {
      float error = e.obj_us - e.pos_us;
      if (fabsf(error) <= max_paso) {
        e.pos_us = e.obj_us;
        if (e.barrido) e.obj_us = (e.obj_us == e.bar_a) ? e.bar_b : e.bar_a;
      } else {
        e.pos_us += (error > 0) ? max_paso : -max_paso;
      }
    }
    escribir(i);
  }
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < NUM_EJES; i++) {
    ejes[i] = {false, 1500, 1500, 1000, 2000, false, 1500, 1500};
    if (!ledcAttach(PINES[i], FREC_HZ, RES_BITS)) {
      Serial.printf("ERR: no se pudo configurar LEDC en GPIO%d\n", PINES[i]);
    }
    escribir(i);  // duty 0: sin pulso
  }
  delay(500);
  Serial.println("\nPrueba de servos Keepon. Todos los ejes empiezan apagados.");
  ayuda();
  t_ant_ms = millis();
}

void loop() {
  leer_serie();
  uint32_t ahora = millis();
  if (ahora - t_ant_ms >= PERIODO_LAZO_MS) {
    paso_rampa((ahora - t_ant_ms) / 1000.0f);
    t_ant_ms = ahora;
  }
}
