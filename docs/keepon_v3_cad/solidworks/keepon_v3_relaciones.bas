Attribute VB_Name = "KeeponRelaciones"
' Relaciones de posición del ensamble Keepon pro v3.
' GENERADO por fuente/keepon_v3_cad.py: no editar a mano (se sobreescribe).
'
' Uso (ver README.md): abrir step/keepon_v3_ensamble.step en SolidWorks, guardarlo como
' ensamble (.SLDASM) sin mover nada, y ejecutar main.
'   - Cada grupo rígido (base, yaw, pitch, roll) se arma con planos coincidentes contra su
'     pieza de referencia: todas las piezas tienen el mismo origen, el del robot.
'   - Entre grupos, una bisagra por eje: concéntrica entre dos cilindros que están sobre el
'     eje + plano coincidente perpendicular al eje.
' Los planos y las caras se buscan por tipo y por geometría, no por nombre: anda igual con
' SolidWorks en español o en inglés.
Option Explicit

Const TOL_RADIO As Double = 0.00002   ' 0,02 mm (SolidWorks trabaja en metros)
Const TOL_EJE As Double = 0.0001      ' 0,1 mm

Dim swApp As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2
Dim swAssy As SldWorks.AssemblyDoc
Dim errores As String
Dim nRel As Long
Dim listadas As Boolean

Sub main()
    Set swApp = Application.SldWorks
    Set swModel = swApp.ActiveDoc
    If swModel Is Nothing Then
        MsgBox "Abrir primero el ensamble (keepon_v3_ensamble.step)."
        Exit Sub
    End If
    If swModel.GetType <> swDocASSEMBLY Then
        MsgBox "El documento activo no es un ensamble."
        Exit Sub
    End If
    Set swAssy = swModel
    errores = ""
    nRel = 0
    listadas = False

    ' 1) La caja base queda fija; lo demás se libera para que lo ubiquen las relaciones
    Fijar "caja_base", True
    Fijar "tapa_base", False
    Fijar "bateria_lipo_3s", False
    Fijar "regulador_6v_20a", False
    Fijar "regulador_5v_5a", False
    Fijar "interruptor", False
    Fijar "servo_yaw_rds3218", False
    Fijar "horn_yaw", False
    Fijar "plato_yaw", False
    Fijar "esp32c3", False
    Fijar "cuna_esp32", False
    Fijar "porta_buzzer", False
    Fijar "buzzer", False
    Fijar "soporte_pitch_izq", False
    Fijar "soporte_pitch_der", False
    Fijar "servo_pitch_hs7955tg", False
    Fijar "horn_pitch", False
    Fijar "horquilla_cabeza", False
    Fijar "servo_roll_mg996r", False
    Fijar "horn_roll", False
    Fijar "placa_roll", False
    Fijar "pi5_pcb", False
    Fijar "pi5_puertos", False
    Fijar "pi5_conectores_csi", False
    Fijar "pi5_active_cooler", False
    Fijar "camara_pcb", False
    Fijar "camara_lente", False
    Fijar "camara_conector", False
    Fijar "cinta_ffc", False
    Fijar "caja_cabeza", False
    Fijar "nariz_camara", False
    Fijar "ojo_izq", False
    Fijar "ojo_der", False

    ' 2) Grupos rígidos: tres planos coincidentes con la pieza de referencia del grupo
    Rigida "tapa_base", "caja_base"
    Rigida "bateria_lipo_3s", "caja_base"
    Rigida "regulador_6v_20a", "caja_base"
    Rigida "regulador_5v_5a", "caja_base"
    Rigida "interruptor", "caja_base"
    Rigida "servo_yaw_rds3218", "caja_base"
    Rigida "horn_yaw", "plato_yaw"
    Rigida "esp32c3", "plato_yaw"
    Rigida "cuna_esp32", "plato_yaw"
    Rigida "porta_buzzer", "plato_yaw"
    Rigida "buzzer", "plato_yaw"
    Rigida "soporte_pitch_izq", "plato_yaw"
    Rigida "soporte_pitch_der", "plato_yaw"
    Rigida "servo_pitch_hs7955tg", "plato_yaw"
    Rigida "horn_pitch", "horquilla_cabeza"
    Rigida "servo_roll_mg996r", "horquilla_cabeza"
    Rigida "horn_roll", "placa_roll"
    Rigida "pi5_pcb", "placa_roll"
    Rigida "pi5_puertos", "placa_roll"
    Rigida "pi5_conectores_csi", "placa_roll"
    Rigida "pi5_active_cooler", "placa_roll"
    Rigida "camara_pcb", "placa_roll"
    Rigida "camara_lente", "placa_roll"
    Rigida "camara_conector", "placa_roll"
    Rigida "cinta_ffc", "placa_roll"
    Rigida "caja_cabeza", "placa_roll"
    Rigida "nariz_camara", "placa_roll"
    Rigida "ojo_izq", "placa_roll"
    Rigida "ojo_der", "placa_roll"

    ' 3) Bisagras: yaw (eje Z), pitch (eje Y) y roll (eje X)
    Bisagra "yaw", "plato_yaw", 3.5000, "servo_yaw_rds3218", 3.0000, 0.0000, 0.0000, 0.0000, 0, 0, 1, "plato_yaw", "caja_base"
    Bisagra "pitch", "horquilla_cabeza", 2.1500, "soporte_pitch_der", 2.1500, 20.0000, 0.0000, 157.0000, 0, 1, 0, "horquilla_cabeza", "plato_yaw"
    Bisagra "roll", "horn_roll", 4.5000, "servo_roll_mg996r", 3.0000, 0.0000, 0.0000, 157.0000, 1, 0, 0, "placa_roll", "horquilla_cabeza"

    swModel.ClearSelection2 True
    swModel.EditRebuild3
    If errores = "" Then
        MsgBox nRel & " relaciones de posición creadas. El robot se mueve en yaw, pitch y roll."
    Else
        MsgBox nRel & " relaciones creadas. Problemas:" & vbCrLf & errores
    End If
End Sub

' Busca un componente por nombre: acepta 'plato_yaw-1' o 'algo/plato_yaw-1'.
Function Pieza(nombre As String) As SldWorks.Component2
    Dim v As Variant, i As Long, c As SldWorks.Component2, n As String, p As Long
    v = swAssy.GetComponents(False)
    If IsEmpty(v) Then Exit Function
    For i = 0 To UBound(v)
        Set c = v(i)
        n = c.Name2
        p = InStrRev(n, "/")
        If p > 0 Then n = Mid(n, p + 1)
        p = InStrRev(n, "-")
        If p > 0 And IsNumeric(Mid(n, p + 1)) Then n = Left(n, p - 1)
        If n = nombre Then
            Set Pieza = c
            Exit Function
        End If
    Next i
    ' Segunda pasada: SolidWorks a veces les agrega un prefijo al importar ('ensamble - caja_base-1').
    ' Se acepta el nombre dentro del de la pieza si no está pegado a otra palabra (buzzer no es porta_buzzer).
    For i = 0 To UBound(v)
        Set c = v(i)
        n = c.Name2
        p = InStr(n, nombre)
        Do While p > 0
            If Borde(n, p - 1) And Borde(n, p + Len(nombre)) Then
                Set Pieza = c
                Exit Function
            End If
            p = InStr(p + 1, n, nombre)
        Loop
    Next i
    errores = errores & "No se encontró la pieza " & nombre & vbCrLf
    If Not listadas Then
        listadas = True
        errores = errores & "  (nombres que tiene el ensamble: "
        For i = 0 To UBound(v)
            If i < 8 Then
                Set c = v(i): errores = errores & c.Name2 & ", "
            End If
        Next i
        errores = errores & "...)" & vbCrLf
    End If
End Function

' ¿El carácter k de n es un borde de palabra (o está fuera del texto)?
Function Borde(n As String, k As Long) As Boolean
    Dim ch As String
    If k < 1 Or k > Len(n) Then
        Borde = True
    Else
        ch = Mid(n, k, 1)
        Borde = Not (ch Like "[A-Za-z0-9_]")
    End If
End Function

Sub Fijar(nombre As String, fija As Boolean)
    Dim c As SldWorks.Component2
    Set c = Pieza(nombre)
    If c Is Nothing Then Exit Sub
    swModel.ClearSelection2 True
    c.Select4 False, Nothing, False
    If fija Then
        swAssy.FixComponent
    Else
        swAssy.UnfixComponent
    End If
End Sub

' k-ésimo plano de referencia del componente: 1 = Alzado (XY), 2 = Planta (XZ), 3 = Vista lateral (YZ).
Function Plano(c As SldWorks.Component2, k As Long) As SldWorks.Feature
    Dim f As SldWorks.Feature, i As Long
    Set f = c.FirstFeature
    Do While Not f Is Nothing
        If f.GetTypeName2 = "RefPlane" Then
            i = i + 1
            If i = k Then
                Set Plano = f
                Exit Function
            End If
        End If
        Set f = f.GetNextFeature
    Loop
End Function

' Índice del plano de referencia perpendicular a la dirección (ex, ey, ez).
Function PlanoNormal(c As SldWorks.Component2, ex As Double, ey As Double, ez As Double) As Long
    Dim k As Long, f As SldWorks.Feature, rp As SldWorks.RefPlane, d As Variant
    For k = 1 To 3
        Set f = Plano(c, k)
        If Not f Is Nothing Then
            Set rp = f.GetSpecificFeature2
            d = rp.Transform.ArrayData   ' (6-8): normal del plano
            If Abs(d(6) * ex + d(7) * ey + d(8) * ez) > 0.99 Then
                PlanoNormal = k
                Exit Function
            End If
        End If
    Next k
    ' Si no se pudo leer: el orden estándar de los planos
    If ez <> 0 Then
        PlanoNormal = 1
    ElseIf ey <> 0 Then
        PlanoNormal = 2
    Else
        PlanoNormal = 3
    End If
End Function

' Cara cilíndrica de radio r (mm) cuyo eje pasa por (px, py, pz) (mm) con dirección (ex, ey, ez).
Function Cilindro(c As SldWorks.Component2, r As Double, px As Double, py As Double, pz As Double, _
                  ex As Double, ey As Double, ez As Double) As SldWorks.Face2
    Dim cuerpos As Variant, info As Variant, i As Long, b As SldWorks.Body2
    Dim f As SldWorks.Face2, s As SldWorks.Surface, p As Variant
    Dim n As Double, ax As Double, ay As Double, az As Double
    Dim dx As Double, dy As Double, dz As Double, t As Double
    cuerpos = c.GetBodies3(swSolidBody, info)
    If IsEmpty(cuerpos) Then Exit Function
    For i = 0 To UBound(cuerpos)
        Set b = cuerpos(i)
        Set f = b.GetFirstFace
        Do While Not f Is Nothing
            Set s = f.GetSurface
            If s.IsCylinder Then
                p = s.CylinderParams   ' origen (0-2), eje (3-5), radio (6), en metros
                If Abs(p(6) - r / 1000#) < TOL_RADIO Then
                    n = Sqr(p(3) ^ 2 + p(4) ^ 2 + p(5) ^ 2)
                    ax = p(3) / n: ay = p(4) / n: az = p(5) / n
                    If Abs(ax * ex + ay * ey + az * ez) > 0.9999 Then
                        dx = px / 1000# - p(0): dy = py / 1000# - p(1): dz = pz / 1000# - p(2)
                        t = dx * ax + dy * ay + dz * az
                        If dx ^ 2 + dy ^ 2 + dz ^ 2 - t ^ 2 < TOL_EJE ^ 2 Then
                            Set Cilindro = f
                            Exit Function
                        End If
                    End If
                End If
            End If
            Set f = f.GetNextFace
        Loop
    Next i
End Function

Function SelPlano(c As SldWorks.Component2, k As Long) As Boolean
    Dim f As SldWorks.Feature
    Set f = Plano(c, k)
    If f Is Nothing Then Exit Function
    SelPlano = f.Select2(True, 1)
End Function

Function SelCara(f As SldWorks.Face2) As Boolean
    Dim e As SldWorks.Entity, sd As SldWorks.SelectData
    Set sd = swModel.SelectionManager.CreateSelectData
    sd.Mark = 1
    Set e = f
    SelCara = e.Select4(True, sd)
End Function

' Crea la relación con lo que está seleccionado y le pone nombre.
Sub Relacion(tipo As Long, nombre As String)
    Dim est As Long, m As SldWorks.Mate2, f As SldWorks.Feature
    Set m = swAssy.AddMate5(tipo, swMateAlignCLOSEST, False, 0, 0, 0, 1, 1, 0, 0, 0, False, False, 0, est)
    If m Is Nothing Then
        errores = errores & nombre & " (error " & est & ")" & vbCrLf
    Else
        Set f = m
        f.Name = nombre
        nRel = nRel + 1
    End If
    swModel.ClearSelection2 True
End Sub

Sub Rigida(nombre As String, ref As String)
    Dim a As SldWorks.Component2, b As SldWorks.Component2, k As Long, ok As Boolean
    Dim planos As Variant
    planos = Array("", "XY", "XZ", "YZ")
    Set a = Pieza(nombre)
    Set b = Pieza(ref)
    If a Is Nothing Or b Is Nothing Then Exit Sub
    For k = 1 To 3
        swModel.ClearSelection2 True
        ok = SelPlano(a, k)
        ok = SelPlano(b, k) And ok
        If ok Then
            Relacion swMateCOINCIDENT, nombre & " = " & ref & " (" & planos(k) & ")"
        Else
            errores = errores & "No se pudieron seleccionar los planos de " & nombre & vbCrLf
        End If
    Next k
End Sub

Sub Bisagra(eje As String, movil As String, rMovil As Double, fija As String, rFija As Double, _
            px As Double, py As Double, pz As Double, ex As Double, ey As Double, ez As Double, _
            planoMovil As String, planoFija As String)
    Dim cm As SldWorks.Component2, cf As SldWorks.Component2, fm As SldWorks.Face2, ff As SldWorks.Face2
    Dim qm As SldWorks.Component2, qf As SldWorks.Component2, k As Long, ok As Boolean
    Set cm = Pieza(movil)
    Set cf = Pieza(fija)
    Set qm = Pieza(planoMovil)
    Set qf = Pieza(planoFija)
    If cm Is Nothing Or cf Is Nothing Or qm Is Nothing Or qf Is Nothing Then Exit Sub
    ' Eje: concéntrica entre los dos cilindros
    Set fm = Cilindro(cm, rMovil, px, py, pz, ex, ey, ez)
    Set ff = Cilindro(cf, rFija, px, py, pz, ex, ey, ez)
    If fm Is Nothing Or ff Is Nothing Then
        errores = errores & "Bisagra " & eje & ": no se encontraron las caras del eje" & vbCrLf
    Else
        swModel.ClearSelection2 True
        ok = SelCara(fm)
        ok = SelCara(ff) And ok
        If ok Then Relacion swMateCONCENTRIC, "Bisagra " & eje & ": eje (" & movil & " - " & fija & ")"
    End If
    ' Plano perpendicular al eje: traba el deslizamiento a lo largo del eje
    k = PlanoNormal(qm, ex, ey, ez)
    swModel.ClearSelection2 True
    ok = SelPlano(qm, k)
    ok = SelPlano(qf, k) And ok
    If ok Then Relacion swMateCOINCIDENT, "Bisagra " & eje & ": plano (" & planoMovil & " - " & planoFija & ")"
End Sub
