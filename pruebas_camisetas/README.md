# Pruebas del detector de camisetas

La guía (§ T2 y Tabla 1) pide detectar `CAMISETA_OLIMPIA` y `CAMISETA_CERRO` en el torso, **minimizando los falsos
positivos**: "una remera lisa roja o azul no es de Cerro Porteño, ni una remera blanca lisa es de Olimpia". El
evaluador puede usar otras prendas para probarlo.

## `imagenes_referencia/`

Fotos de internet de la camiseta sola, **sin personas** (regla del proyecto), bajadas el 15/10/2026. Cada carpeta
tiene un `fuentes.txt` con el origen y la licencia de cada imagen. Sirven para desarrollar y probar la lógica del
patrón (franja, rayas); **no** para ajustar los umbrales de color: son fotos de cámara normal con luz de estudio, y
el robot ve con la NoIR. Eso se ajusta grabando las camisetas reales con la luz de la demo.

| Carpeta | Qué hay | Tiene que dar |
|---|---|---|
| `olimpia/` (5) | Titular: **blanca con franja horizontal negra**, de frente, de espalda, con la franja difusa, un primer plano y un dibujo | Olimpia |
| `cerro/` (9) | Titular a **rayas verticales rojas y azul marino**, y la **titular 2026, mitad roja y mitad azul** (sin rayas) | Cerro |
| `suplentes/` (5) | Olimpia negra con rayas blancas, Olimpia negra lisa, Cerro beige con rayas finas | A decidir: no tienen el patrón titular |
| `trampas/` (8) | Remeras lisas roja y azul, azul marino, Barcelona (rayas bordó y azul), un dibujo azulgrana genérico | Nada (las del Barcelona y el dibujo, ver abajo) |

## Lo que muestran las fotos (y cambia el diseño del detector)

- **El azul de Cerro es azul marino oscuro y el rojo es casi bordó** (`cerro/cerro_varias_rayas_bordo_y_marino.jpg`).
  Con poca luz o con la NoIR, ese azul se puede confundir con negro: la regla no puede suponer un azul claro.
- **La titular 2026 de Cerro es mitad y mitad, sin rayas** (`cerro/cerro_2026_titular_mitad_y_mitad.jpg`). Una regla
  que exija rayas verticales no la detecta. Mejor pedir rojo **y** azul a la vez, cada uno en una parte grande del
  torso, separados por un borde vertical (una o más veces).
- **La franja de Olimpia también va en la espalda**, y en algún modelo tiene los bordes difusos.
- **La camiseta del Barcelona es casi igual a la de Cerro** (`trampas/barcelona_*`): por color y patrón no se
  distinguen. Es una limitación esperable; si el evaluador la usa, hay que explicarlo en la defensa.
- **Las suplentes no tienen el patrón titular.** La de Olimpia es negra con rayas blancas: no es "blanca con franja
  negra". Hay que decidir si cuentan; la guía solo describe las titulares.
- Falta una **remera blanca lisa**: no se encontró una foto con licencia clara. Se puede usar una real o una sintética.

## Grabaciones reales y resultados (04/11)

`grabar.sh` graba con la cámara del robot (robot apagado; pitido cada 20 s para cambiar de distancia) en
`~/keepon/capturas/camisetas/` en la Pi, fuera de git. `evaluar.py videos` corre Pose + `keepon/camiseta.py` sobre
esas tomas sin mostrar imágenes; `evaluar.py referencias`, sobre las fotos de esta carpeta.

Tomas de 60 s, de frente, a 1,2 / 1,8 / 2,5 m, luz del laboratorio. Colores medidos en el torso con la NoIR
(HSV de OpenCV): rojo H 0–2/178 S 190–210; **azul marino H 116–145 S 35–90 V 30–60 (se ve violeta, no negro)**;
blanco de Olimpia S < 16 V 115–170; **franja de Olimpia V 38–54, marrón violácea**, con el logo blanco adentro.

| Toma | Clase activa tras el filtro de 6 cuadros | Falsos positivos |
|---|---|---|
| Olimpia titular | 82 % (99 % desde los 10 s; antes venía caminando y muy cerca: no se ve el blanco de abajo) | 0 % |
| Cerro 2026 mitad y mitad | 98 % | 0 % |
| Roja lisa | — | 0 % |
| Azul marino lisa | — | 0 % |

Con las fotos de referencia: todas las titulares completas bien, ninguna trampa ni suplente da positivo (las del
Barcelona tampoco, con esas fotos). Fallan dos primeros planos de Cerro que son casi solo azul (esperable).
La remera blanca lisa está probada solo con una sintética (`tests/test_camiseta.py`): falta una real.
