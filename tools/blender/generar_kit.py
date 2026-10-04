# -*- coding: utf-8 -*-
"""
generar_kit.py - Regenera las texturas y los 12 .blend del kit modular de TheSaac.

Uso, desde la raiz del repositorio (Blender 5.1):
    blender --background --factory-startup --python tools/blender/generar_kit.py
    blender --background --factory-startup --python tools/blender/generar_kit.py -- --muestra

Con --muestra tambien arma docs/capturas/sala_muestra.blend y renderiza las capturas.
En modo --background Blender no genera miniaturas: se regeneran desde el Asset Browser
(clic derecho sobre el asset -> Generate Preview).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_isaac as kit
import kit_piezas as piezas

kit.preparar()
kit.generar_texturas()
piezas.borde_superior("T_Muro_Piedra")
piezas.borde_superior("T_Pilar_Piedra")
for i, (archivo, _) in enumerate(piezas.PIEZAS):
    piezas.construir(i)
    piezas.guardar_pendiente()
    print("Guardado", archivo)
if "--muestra" in sys.argv:
    import kit_muestra as muestra
    muestra.armar()
    muestra.render("Cam_Vista_Aerea", "kit_vista_aerea.png", sin_techo=True)
    muestra.render("Cam_Fila_A", "kit_props_a.png")
    muestra.render("Cam_Fila_B", "kit_props_b.png")
    muestra.render("Cam_Primera_Persona", "kit_primera_persona.png", motor='BLENDER_EEVEE')
kit.restaurar()
