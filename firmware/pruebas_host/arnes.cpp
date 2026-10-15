// Arnés para correr el núcleo del firmware en la notebook (sin ESP32).
// Lo usa tests/test_firmware_nucleo.py para compararlo contra keepon/sim_esp32.py.
//
// Lee un guion por stdin, una orden por línea:
//   L <texto>   le pasa <texto> al firmware como línea recibida
//   T <n>       avanza n pasos de 10 ms (imprime la posición después de cada uno)
//   F <ms>      imprime la frecuencia del buzzer en el instante <ms> (relativo al arranque)
//   U           imprime los pulsos de los servos [µs]
// Salida: "R <paso> <respuesta>", "P <paso> <yaw> <pitch> <roll>", "F <ms> <Hz>", "U <yaw> <pitch> <roll>".
//
//   g++ -std=c++17 -O2 -I ../keepon_fw arnes.cpp ../keepon_fw/nucleo.cpp -o arnes
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "nucleo.h"

static int paso = 0;

static void volcar(keepon::Nucleo &n) {
  char copia[600];
  strncpy(copia, n.salida(), sizeof(copia) - 1);
  copia[sizeof(copia) - 1] = '\0';
  n.vaciar_salida();
  for (char *l = strtok(copia, "\n"); l; l = strtok(NULL, "\n")) printf("R %d %s\n", paso, l);
}

int main() {
  keepon::Nucleo n;  // el constructor arranca en t = 0 y anuncia HELLO 0
  volcar(n);
  char linea[512];
  while (fgets(linea, sizeof(linea), stdin)) {
    linea[strcspn(linea, "\n")] = '\0';
    if (linea[0] == 'L') {
      n.linea(linea[1] == ' ' ? linea + 2 : linea + 1, paso * keepon::PASO_MS);
      volcar(n);
    } else if (linea[0] == 'T') {
      int k = atoi(linea + 1);
      for (int i = 0; i < k; i++) {
        paso++;
        n.paso(paso * keepon::PASO_MS);
        volcar(n);
        printf("P %d %.12f %.12f %.12f\n", paso, n.eje(0).pos, n.eje(1).pos, n.eje(2).pos);
      }
    } else if (linea[0] == 'F') {
      unsigned ms = (unsigned)atoi(linea + 1);
      printf("F %u %u\n", ms, n.frecuencia(ms));
    } else if (linea[0] == 'U') {
      uint16_t us[3];
      n.pulsos(us);
      printf("U %u %u %u\n", us[0], us[1], us[2]);
    }
  }
  return 0;
}
