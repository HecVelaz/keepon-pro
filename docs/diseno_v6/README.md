# Keepon V6 · revisión vigente R4

Abrir **[Keepon_V6_R4.SLDASM](revision_R4/SOLIDWORKS_R4/Keepon_V6_R4.SLDASM)**, conservando los cuatroSLDPRT de esa carpeta. El paquete de entrega es `Keepon_V6_R4.zip`.

- Disco rojo25T según el croquis del usuario: Ø19.8, cuatroØ3 aR7 (14 entre opuestos), paso centralØ3, cuboØ9, disco2.45 y altura total4.5. Carcasa y retención ajustadas al conjunto.
- Retención de pitch anterior4.3 eliminada, junto con sus cuatro tornillos, pasos y cajeados. Brazo simple y bolsillo invertidos180°.
- Cuatro postes PiØ9×8 mm; placa, cooler y reserva de cinta acompañan el nuevo asiento.
- Módulo buzzer31.8×12.8×1.5/altura total10 fijado directamente detrás de cara con unM3×5 en poste ciego integrado. Sin bastidor ni arandela impresa.
- Cara y ojos siguen siendo una sola pieza. Cuerpos, operaciones importadas y grupos tienen nombres identificables en español.

[Vista de cambios](revision_R4/vistas/01_R4_cambios.png) · [Detalle del disco](revision_R4/vistas/02_R4_disco_roll.png) · [Montaje y límites](revision_R4/README.md).

Fuentes y parámetros activos en `revision_R4/`. Los SLDPRT contienen cuerpos importados: el modelo paramétrico se regenera desde Python/config.yaml. El estriado25T y el diámetro/centro del transductor conservan referencias nominales; comprobar encastres y componentes físicos antes de fabricar.

Las carpetas `SOLIDWORKS_V6`, `SOLIDWORKS_V6_R3`, los ZIP R1/R2/R3 y sus informes son antecedentes. El README R3 anterior está conservado en `HISTORIAL/README_R3.md`. Para trabajar con los cambios actuales, usar la R4 enlazada arriba.
