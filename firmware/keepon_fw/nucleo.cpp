// Núcleo del firmware (ver nucleo.h). Cada parte indica de qué función de Python es copia.
#include "nucleo.h"

#include <ctype.h>
#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace keepon {

static double recortar(double x, double lo, double hi) { return x < lo ? lo : x > hi ? hi : x; }

// ------------------------------------------------------------------------------------------------
// Trayectoria: copia de keepon/trajectory.py (Axis). Ver allí la deducción de la fórmula cerrada.
// ------------------------------------------------------------------------------------------------
bool Eje::set_target(double t) {
  target = recortar(t, lo, hi);
  return target != t;
}

// Mayor velocidad (>= 0) con la que se puede avanzar este paso y todavía frenar en `dist`.
double Eje::v_max_to_stop(double dist) const {
  double A = amax * DT;
  double n = floor((sqrt(1.0 + 8.0 * dist / (DT * A)) - 1.0) / 2.0);
  return (dist / DT + A * n * (n + 1) / 2.0) / (n + 1);
}

void Eje::step() {
  double e = target - pos;
  double A = amax * DT;
  double v_des = e != 0.0 ? copysign(fmin(vmax, v_max_to_stop(fabs(e))), e) : 0.0;
  vel += recortar(v_des - vel, -A, A);
  pos = recortar(pos + vel * DT, lo, hi);
  if (fabs(target - pos) < 1e-9 && fabs(vel) <= A) pos = target;  // solo absorbe el redondeo
}

// Recorrido si frena a tope desde ahora: dt · Σ max(0, |v| − k·a·dt).
double Eje::stopping_distance() const {
  double A = amax * DT, v = fabs(vel);
  double n = floor(v / A);
  return DT * (n * v - A * n * (n + 1) / 2.0);
}

// Punto donde se detiene frenando con amax (STOP y watchdog suaves, sin golpe).
double Eje::brake_target() const { return recortar(pos + copysign(stopping_distance(), vel), lo, hi); }

// ------------------------------------------------------------------------------------------------
// Servos: grados → µs con la calibración de config.yaml (neck.servos).
// ------------------------------------------------------------------------------------------------
uint16_t grados_a_us(int eje, double grados) {
  double d = gen::SIGNO[eje] * grados;
  double gpu = gen::GPU[eje][d < 0 ? 0 : 1];  // lado de pulsos < 1500 o > 1500
  double us = floor(gen::CENTRO_US[eje] + d / gpu + 0.5);
  return (uint16_t)recortar(us, gen::MIN_US[eje], gen::MAX_US[eje]);
}

// ------------------------------------------------------------------------------------------------
// Máquina de estados: copia de keepon/sim_esp32.py (SimESP32).
// ------------------------------------------------------------------------------------------------
Nucleo::Nucleo() { reiniciar(0); }

void Nucleo::reiniciar(uint32_t ahora_ms) {
  for (int i = 0; i < 3; i++) {
    ejes_[i] = Eje{gen::LIM_MIN[i], gen::LIM_MAX[i], gen::VMAX[i], gen::AMAX[i], gen::HOME[i], 0.0, gen::HOME[i]};
  }
  estado_ = RUN;
  ultimo_rx_ms_ = ahora_ms;
  cortar_sonido();
  max_sonido_seq_ = -1;
  vaciar_salida();
  responder("HELLO 0 %d %d", FW_VERSION, PROTO_VERSION);
}

void Nucleo::responder(const char *fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  int n = vsnprintf(sal_ + n_sal_, sizeof(sal_) - n_sal_, fmt, ap);
  va_end(ap);
  if (n < 0 || n_sal_ + n + 2 > sizeof(sal_)) {  // no entra: se descarta la respuesta entera
    sal_[n_sal_] = '\0';
    return;
  }
  n_sal_ += n;
  sal_[n_sal_++] = '\n';
  sal_[n_sal_] = '\0';
}

void Nucleo::frenar() {
  for (int i = 0; i < 3; i++) ejes_[i].target = ejes_[i].brake_target();
}

// Cantidad de argumentos después de seq (protocol.COMMANDS).
static int argumentos(const char *nombre) {
  if (!strcmp(nombre, "J")) return 3;
  if (!strcmp(nombre, "S") || !strcmp(nombre, "CANCEL")) return 1;
  if (!strcmp(nombre, "PING") || !strcmp(nombre, "STOP") || !strcmp(nombre, "RESUME") || !strcmp(nombre, "HOME"))
    return 0;
  return -1;
}

static void mayusculas(char *s) {
  for (; *s; s++) *s = (char)toupper((unsigned char)*s);
}

static bool solo_digitos(const char *s) {
  if (!*s) return false;
  for (; *s; s++)
    if (!isdigit((unsigned char)*s)) return false;
  return true;
}

// Como int() de Python para un token: signo opcional y dígitos. false si no es un entero.
static bool leer_entero(const char *s, long long *v) {
  const char *p = (*s == '+' || *s == '-') ? s + 1 : s;
  if (!solo_digitos(p) || strlen(p) > 18) return false;
  *v = strtoll(s, NULL, 10);
  return true;
}

void Nucleo::linea_demasiado_larga(uint32_t) { err(-1, "TOO_LONG"); }

// Validación: copia de protocol.parse_command, con los mismos códigos y en el mismo orden.
void Nucleo::linea(const char *texto, uint32_t ahora_ms) {
  if (strlen(texto) + 1 > (size_t)MAX_LINEA) {  // +1: en Python la línea incluye el '\n'
    err(-1, "TOO_LONG");
    return;
  }
  char buf[MAX_LINEA + 1];
  strncpy(buf, texto, sizeof(buf) - 1);
  buf[sizeof(buf) - 1] = '\0';
  char *tok[8];
  int n = 0;
  for (char *p = strtok(buf, " \t\r\n\v\f"); p && n < 8; p = strtok(NULL, " \t\r\n\v\f")) tok[n++] = p;
  if (n == 0) {
    err(-1, "EMPTY");
    return;
  }
  mayusculas(tok[0]);
  if (!strcmp(tok[0], "HELLO")) {  // HELLO <versión>: la Pi abre sesión
    if (n != 2 || !solo_digitos(tok[1])) {
      err(-1, "BAD_ARGS");
      return;
    }
    manejar("HELLO", 0, &tok[1], 1, ahora_ms);
    return;
  }
  int esperados = argumentos(tok[0]);
  if (esperados < 0) {
    err(-1, "UNKNOWN_CMD");
    return;
  }
  if (n < 2) {
    err(-1, "BAD_ARGS");
    return;
  }
  long long seq;
  if (!leer_entero(tok[1], &seq) || seq < 0) {
    err(-1, "BAD_SEQ");
    return;
  }
  if (n - 2 != esperados) {
    err(seq, "BAD_ARGS");
    return;
  }
  char **args = &tok[2];
  if (!strcmp(tok[0], "J")) {
    for (int i = 0; i < 3; i++) {
      char *fin;
      double v = strtod(args[i], &fin);
      if (fin == args[i] || *fin != '\0' || !isfinite(v)) {
        err(seq, "BAD_NUMBER");
        return;
      }
    }
  } else {
    for (int i = 0; i < esperados; i++) mayusculas(args[i]);
    if (!strcmp(tok[0], "CANCEL") && strcmp(args[0], "SOUND")) {
      err(seq, "BAD_ARGS");
      return;
    }
  }
  manejar(tok[0], seq, args, esperados, ahora_ms);
}

// Comando válido (SimESP32.feed + _handle).
void Nucleo::manejar(const char *c, long long seq, char **args, int, uint32_t ahora_ms) {
  ultimo_rx_ms_ = ahora_ms;
  if (estado_ == WATCHDOG) estado_ = RUN;

  if (!strcmp(c, "HELLO")) {  // nueva sesión de la Pi: reinicia la numeración de sonidos
    if (atoll(args[0]) != PROTO_VERSION) {
      err(0, "BAD_VERSION");
      return;
    }
    max_sonido_seq_ = -1;
    responder("HELLO 1 %d %d", FW_VERSION, PROTO_VERSION);  // seq 1 = sesión aceptada
  } else if (!strcmp(c, "PING")) {
    responder("ACK %lld", seq);
    const char *nombres[] = {"RUN", "STOPPED", "WATCHDOG"};
    responder("STATE %lld %s %.1f %.1f %.1f %s", seq, nombres[estado_], ejes_[0].pos, ejes_[1].pos, ejes_[2].pos,
              sonido());
  } else if (!strcmp(c, "STOP")) {
    estado_ = STOPPED;
    cortar_sonido();
    frenar();
    responder("ACK %lld", seq);
  } else if (!strcmp(c, "RESUME")) {
    estado_ = RUN;
    responder("ACK %lld", seq);
  } else if (estado_ == STOPPED) {  // J, S, HOME y CANCEL rechazados mientras el STOP está enclavado
    err(seq, "STOP_ACTIVE");
  } else if (!strcmp(c, "J")) {
    bool recortado = false;
    for (int i = 0; i < 3; i++) recortado |= ejes_[i].set_target(strtod(args[i], NULL));
    responder(recortado ? "ACK %lld CLIPPED" : "ACK %lld", seq);
  } else if (!strcmp(c, "HOME")) {
    for (int i = 0; i < 3; i++) ejes_[i].set_target(gen::HOME[i]);
    responder("ACK %lld", seq);
  } else if (!strcmp(c, "S")) {
    int k = -1;
    for (int i = 0; i < gen::NUM_SONIDOS; i++)
      if (!strcmp(args[0], gen::SONIDOS[i].nombre)) k = i;
    if (k < 0) {
      err(seq, "UNKNOWN_SOUND");
      return;
    }
    responder("ACK %lld", seq);
    if (seq <= max_sonido_seq_) return;  // reenvío o comando viejo: no se reproduce de nuevo
    max_sonido_seq_ = seq;
    sonido_ = k;
    sonido_seq_ = seq;
    sonido_inicio_ms_ = ahora_ms;
  } else if (!strcmp(c, "CANCEL")) {
    cortar_sonido();
    responder("ACK %lld", seq);
  }
}

// Un paso del lazo (SimESP32.tick): watchdog, fin del sonido y trayectoria.
void Nucleo::paso(uint32_t ahora_ms) {
  if (estado_ == RUN && ahora_ms - ultimo_rx_ms_ > gen::WATCHDOG_MS) {
    estado_ = WATCHDOG;
    cortar_sonido();
    frenar();
    err(0, "WATCHDOG");
  }
  if (sonido_ >= 0 && ahora_ms - sonido_inicio_ms_ >= gen::SONIDOS[sonido_].total_ms) {
    responder("DONE %lld", sonido_seq_);
    cortar_sonido();
  }
  for (int i = 0; i < 3; i++) ejes_[i].step();
}

// Frecuencia del buzzer: igual que el simulador (pruebas_buzzer/simulador_sonidos.html).
// Nota fija: una frecuencia; barrido: interpolación lineal que cambia cada PASO_TONO_MS; 0: silencio.
uint16_t Nucleo::frecuencia(uint32_t ahora_ms) const {
  if (sonido_ < 0) return 0;
  const gen::Sonido &s = gen::SONIDOS[sonido_];
  uint32_t e = ahora_ms - sonido_inicio_ms_, acumulado = 0;
  for (int i = 0; i < s.n; i++) {
    const gen::Segmento &g = s.seg[i];
    if (e < acumulado + g.ms) {
      if (g.f0 == 0 || g.f0 == g.f1) return g.f0;
      uint32_t t = (e - acumulado) / PASO_TONO_MS * PASO_TONO_MS;
      return (uint16_t)floor(g.f0 + ((double)g.f1 - g.f0) * t / g.ms + 0.5);
    }
    acumulado += g.ms;
  }
  return 0;
}

void Nucleo::pulsos(uint16_t us[3]) const {
  for (int i = 0; i < 3; i++) us[i] = grados_a_us(i, ejes_[i].pos);
}

}  // namespace keepon
