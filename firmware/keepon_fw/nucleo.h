// Núcleo del firmware de Keepon: protocolo serie, trayectoria, STOP, watchdog y sonidos.
//
// Es C++ portable (sin Arduino): el mismo código corre en la ESP32-C3 (keepon_fw.ino) y en la
// notebook (firmware/pruebas_host/arnes.cpp), donde se compara contra keepon/sim_esp32.py, que es
// la especificación ejecutable. Si cambia el comportamiento de uno, tiene que cambiar el otro.
//
// El núcleo no lee relojes: quien lo usa le pasa el tiempo en ms. La trayectoria avanza de a un
// paso fijo de 10 ms (lazo de 100 Hz), igual que SimLink.advance().
#pragma once
#include <stdint.h>
#include <stddef.h>

#include "generado.h"

namespace keepon {

const int FW_VERSION = 1;
const int PROTO_VERSION = 1;
const int MAX_LINEA = 64;          // como protocol.MAX_LINE: cuenta también el '\n'
const uint32_t PASO_MS = 10;       // período del lazo de trayectoria
const double DT = PASO_MS / 1000.0;
const uint32_t PASO_TONO_MS = 5;   // cada cuánto se actualiza la frecuencia en un barrido

enum Estado { RUN, STOPPED, WATCHDOG };

// Un eje del cuello: copia de keepon/trajectory.py (Axis), en double para dar los mismos números.
struct Eje {
  double lo, hi, vmax, amax;
  double pos, vel, target;

  bool set_target(double t);       // true si hubo que recortarlo a los límites
  double v_max_to_stop(double dist) const;
  void step();
  double stopping_distance() const;
  double brake_target() const;
};

class Nucleo {
 public:
  Nucleo();

  // Arranque o reinicio: cuello en HOME, sin sonido, sesión nueva. Anuncia "HELLO 0 fw proto".
  void reiniciar(uint32_t ahora_ms);
  // Una línea recibida (sin el '\n'). Las respuestas quedan en salida().
  void linea(const char *texto, uint32_t ahora_ms);
  // La línea era más larga que el buffer de recepción: se responde TOO_LONG, como a cualquier larga.
  void linea_demasiado_larga(uint32_t ahora_ms);
  // Un paso del lazo de 100 Hz: watchdog, fin del sonido y trayectoria (mismo orden que SimESP32.tick).
  void paso(uint32_t ahora_ms);

  // Frecuencia que tiene que sonar ahora en el buzzer [Hz]; 0 = callado.
  uint16_t frecuencia(uint32_t ahora_ms) const;
  // Pulsos de los servos [µs] para la postura actual (yaw, pitch, roll).
  void pulsos(uint16_t us[3]) const;

  // Respuestas pendientes, separadas por '\n'. Quien las manda llama a vaciar_salida().
  const char *salida() const { return sal_; }
  size_t largo_salida() const { return n_sal_; }
  void vaciar_salida() { n_sal_ = 0; sal_[0] = '\0'; }

  // Para las pruebas
  Estado estado() const { return estado_; }
  const Eje &eje(int i) const { return ejes_[i]; }
  const char *sonido() const { return sonido_ < 0 ? "NONE" : gen::SONIDOS[sonido_].nombre; }

 private:
  void manejar(const char *nombre, long long seq, char **args, int nargs, uint32_t ahora_ms);
  void cortar_sonido() { sonido_ = -1; sonido_seq_ = -1; }
  void frenar();
  void responder(const char *fmt, ...);
  void err(long long seq, const char *motivo) { responder("ERR %lld %s", seq, motivo); }

  Eje ejes_[3];
  Estado estado_;
  uint32_t ultimo_rx_ms_;
  int sonido_;                 // índice en gen::SONIDOS, -1 = ninguno
  long long sonido_seq_;
  uint32_t sonido_inicio_ms_;
  long long max_sonido_seq_;   // un S con seq <= a éste es un reenvío o un comando viejo
  char sal_[512];
  size_t n_sal_;
};

// Grados → µs con la calibración de config.yaml (neck.servos). Público para poder probarlo.
uint16_t grados_a_us(int eje, double grados);

}  // namespace keepon
