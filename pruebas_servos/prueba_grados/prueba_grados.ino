// Código de un compañero para mover un servo de posición escribiendo el ángulo
// por el monitor serie (115200). Probado por él con sus servos.
//
// Cambios respecto del original:
//   1. Pin 0 en lugar de 18 (en la ESP32-C3 el GPIO18 es el USB D-).
//   2. Se lee la línea completa y se ignora si no es un número entero.
//      El original usaba Serial.parseInt(), que devuelve 0 con un Enter vacío
//      o una letra, y eso mandaba el servo a 0° a máxima velocidad.
//
// Ojo: ESP32Servo usa por defecto 544–2400 µs para 0–180°, y no hay rampa:
// cada ángulo nuevo es un salto a la velocidad máxima del servo.

#include <ESP32Servo.h>

Servo myServo;
const int servoPin = 0;

void setup() {
  Serial.begin(115200); // Inicializar comunicación serie
  myServo.attach(servoPin);

  // Posición inicial (90° ≈ 1472 µs con los límites por defecto)
  myServo.write(90);

  // Mensaje de bienvenida en el monitor serie
  Serial.println("--- Control de servo de posición con ESP32-C3 ---");
  Serial.println("Ingresa un valor entre 0 y 180 grados:");
}

void loop() {
  // Comprobar si hay datos disponibles en el puerto serie
  if (Serial.available() > 0) {
    // Leer la línea completa (hasta el Enter) y quitar espacios y '\r'
    String linea = Serial.readStringUntil('\n');
    linea.trim();
    if (linea.length() == 0) {
      return;  // Enter vacío: no hacer nada
    }

    // Aceptar solo dígitos: "abc", "90.5" o "-5" se rechazan sin mover el servo
    for (unsigned int i = 0; i < linea.length(); i++) {
      if (!isDigit(linea[i])) {
        Serial.println("¡Error! Escribí solo un número entero entre 0 y 180.");
        return;
      }
    }
    int grados = linea.toInt();

    // Validar el rango (0 a 180 grados)
    if (grados >= 0 && grados <= 180) {
      myServo.write(grados);
      Serial.print("Moviendo servo a: ");
      Serial.print(grados);
      Serial.print(" grados (");
      Serial.print(myServo.readMicroseconds());
      Serial.println(" us).");
    } else {
      Serial.println("¡Error! El ángulo tiene que estar entre 0 y 180.");
    }
  }
}
