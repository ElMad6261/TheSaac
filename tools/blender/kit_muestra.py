# -*- coding: utf-8 -*-
"""kit_muestra.py - Arma docs/capturas/sala_muestra.blend con copias de las piezas y saca capturas."""
import bpy, os, math
from mathutils import Matrix, Vector

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))   # raiz del repo TheSaac
BLEND = os.path.join(RAIZ, "assets", "blend")
OUT = os.path.join(RAIZ, "docs", "capturas")
ARCH = ["muro_estandar", "muro_vano", "pilar", "piso_sala", "techo_tragaluz", "puerta", "antorcha",
        "interruptor", "rocas", "pedestal", "trampilla"]
SRC = {}

def limpiar():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for _ in range(3):
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

def anexar():
    SRC.clear()
    for a in ARCH:
        with bpy.data.libraries.load(os.path.join(BLEND, a + ".blend"), link=False) as (src, dst):
            dst.objects = list(src.objects)
        for o in dst.objects:
            SRC[o.name] = o
    for coll in (bpy.data.materials, bpy.data.images, bpy.data.node_groups):
        for d in list(coll):
            base, _, suf = d.name.rpartition('.')
            if base and suf.isdigit() and base in coll:
                d.user_remap(coll[base])
                coll.remove(d)
    for l in list(bpy.data.libraries):
        bpy.data.libraries.remove(l)

def col(nombre):
    c = bpy.data.collections.get(nombre) or bpy.data.collections.new(nombre)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c

def copia(o, M, c, padre=None):
    n = o.copy()
    if n.asset_data:
        n.asset_clear()
    c.objects.link(n)
    if padre is None:
        n.parent = None
        n.matrix_world = M @ o.matrix_basis    # matrix_world de lo anexado no esta evaluado
    else:
        n.parent = padre
        n.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        n.matrix_basis = o.matrix_basis.copy()
    for ch in o.children:
        copia(ch, M, c, n)
    return n

def poner(nombres, loc, rotz=0.0, c=None, centrar=False):
    M = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(math.radians(rotz), 4, 'Z')
    if centrar:   # las rocas estan separadas en su archivo: se quita ese desplazamiento
        return {nm: copia(SRC[nm], M @ Matrix.Translation(-SRC[nm].location), c) for nm in nombres}
    return {nm: copia(SRC[nm], M, c) for nm in nombres}

def abrir_trampilla(t):
    t["Trampilla_Tapa_I"].rotation_euler.y += math.radians(-110)
    t["Trampilla_Tapa_D"].rotation_euler.y += math.radians(110)

PUERTA = ["Puerta_Marco", "Puerta_Hoja"]
TRAMPILLA = ["Trampilla", "Trampilla_Hueco", "Trampilla_Tapa_I", "Trampilla_Tapa_D"]

def sala():
    s = col("Sala")
    poner(["Piso_Sala"], (0, 0, 0), c=s)
    poner(["Techo_Tragaluz"], (0, 0, 3), c=s)
    for x in (-5.5, 5.5):
        for y in (-3.5, 3.5):
            poner(["Pilar"], (x, y, 0), c=s)
    for x in (-4, -2, 2, 4):
        poner(["Muro_Estandar"], (x, 3.5, 0), c=s)
        poner(["Muro_Estandar"], (x, -3.5, 0), c=s)
    for y in (-2, 0, 2):
        poner(["Muro_Estandar"], (-5.5, y, 0), 90, c=s)
    for y in (-2, 2):
        poner(["Muro_Estandar"], (5.5, y, 0), -90, c=s)
    poner(["Muro_Vano"], (0, 3.5, 0), c=s)                       # norte: puerta cerrada
    poner(PUERTA, (0, 3.5, 0), c=s)
    poner(["Muro_Vano"], (0, -3.5, 0), 180, c=s)                  # sur: puerta abierta
    d = poner(PUERTA, (0, -3.5, 0), 180, c=s)
    d["Puerta_Hoja"].rotation_euler.z += math.radians(90)
    poner(["Muro_Vano"], (5.5, 0, 0), -90, c=s)                   # este: puerta cerrada
    poner(PUERTA, (5.5, 0, 0), -90, c=s)
    poner(["Antorcha"], (-2, 3.25, 1.35), c=s)
    poner(["Antorcha"], (2, 3.25, 1.35), c=s)
    poner(["Interruptor"], (-5.25, 0, 1.0), 90, c=s)
    for nm, loc, rz in (("Roca_01", (-3.6, 1.6, 0), 20), ("Roca_02", (-2.6, -1.9, 0), 70),
                        ("Roca_03", (3.4, -1.7, 0), 140), ("Roca_04", (3.7, 1.9, 0), 210)):
        poner([nm], loc, rz, c=s, centrar=True)
    poner(["Pedestal"], (-1.4, 0.6, 0), c=s)
    abrir_trampilla(poner(TRAMPILLA, (1.6, 0.3, 0), c=s))
    a = col("Fila_A")
    poner(PUERTA, (-3.0, -12, 0), c=a)
    poner(["Antorcha"], (-1.45, -12, 1.0), c=a)
    poner(["Interruptor"], (-0.45, -12, 0.75), c=a)
    poner(["Pedestal"], (0.85, -12, 0), c=a)
    b = col("Fila_B")
    for k in range(4):
        poner(["Roca_%02d" % (k + 1)], (-3.3 + 1.45 * k, -24, 0), 25 * k, c=b, centrar=True)
    abrir_trampilla(poner(TRAMPILLA, (3.2, -24, 0), c=b))

def camara(nombre, loc, mira, lente):
    sc = bpy.context.scene
    c = bpy.data.objects.get(nombre)
    if c is None:
        c = bpy.data.objects.new(nombre, bpy.data.cameras.new(nombre))
        sc.collection.objects.link(c)
    c.location = loc
    c.rotation_euler = (Vector(mira) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    c.data.lens = lente
    c.data.clip_start = 0.05
    return c

def luz(nombre, tipo, loc=(0, 0, 0), rot=(0, 0, 0), energia=1.0, color=(1, 1, 1), **kw):
    sc = bpy.context.scene
    o = bpy.data.objects.get(nombre)
    if o is None:
        o = bpy.data.objects.new(nombre, bpy.data.lights.new(nombre, tipo))
        sc.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    o.data.energy = energia
    o.data.color = color
    for k, v in kw.items():
        setattr(o.data, k, v)
    return o

def escena():
    sc = bpy.context.scene
    camara("Cam_Primera_Persona", (-3.9, -2.6, 1.6), (1.0, 3.2, 1.2), 20)
    camara("Cam_Vista_Aerea", (-9.5, -11.0, 11.0), (0.0, -0.4, 0.0), 30)
    camara("Cam_Fila_A", (-1.05, -17.4, 1.5), (-1.05, -12, 1.05), 30)
    camara("Cam_Fila_B", (0.0, -31.0, 2.8), (0.0, -24, 0.3), 30)
    mundo = sc.world or bpy.data.worlds.new("Mundo")
    sc.world = mundo
    mundo.color = (0.012, 0.01, 0.009)
    luz("Sol_Tragaluz", 'SUN', rot=(math.radians(28), math.radians(-12), math.radians(20)), energia=5.0,
        color=(1.0, 0.95, 0.85), angle=math.radians(1.0))
    k = 0
    for o in bpy.data.objects:
        if o.name.startswith("Antorcha_PuntoLuz") and o.users_collection and o.users_collection[0].name == "Sala":
            luz("Luz_Antorcha_%d" % k, 'POINT', loc=o.matrix_world.translation, energia=120.0,
                color=(1.0, 0.55, 0.22), shadow_soft_size=0.05)
            k += 1
    luz("Relleno", 'AREA', loc=(0, 0, 2.9), energia=120.0, color=(1.0, 0.85, 0.7), size=6.0)
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'Standard'

def render(camara_nombre, archivo, motor='BLENDER_WORKBENCH', sin_techo=False):
    sc = bpy.context.scene
    sc.render.engine = motor
    if motor == 'BLENDER_WORKBENCH':
        sh = sc.display.shading
        sh.light = 'STUDIO'
        sh.color_type = 'TEXTURE'
        sh.show_backface_culling = True
        sh.show_cavity = False
        sh.show_shadows = False
        sc.display.render_aa = 'OFF'
    else:
        try:
            sc.eevee.taa_render_samples = 32
        except Exception:
            pass
    techo = [o for o in bpy.data.objects if o.name.startswith("Techo_Tragaluz")]
    for o in techo:
        o.hide_render = sin_techo
    sc.camera = bpy.data.objects[camara_nombre]
    sc.render.filepath = os.path.join(OUT, archivo)
    bpy.ops.render.render(write_still=True)
    for o in techo:
        o.hide_render = False
    return sc.render.filepath

def armar():
    os.makedirs(OUT, exist_ok=True)
    limpiar()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "sala_muestra.blend"))
    anexar()
    sala()
    for o in list(bpy.data.objects):          # quitar los originales anexados que no se usan
        if not o.users_collection:
            bpy.data.objects.remove(o)
    escena()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "sala_muestra.blend"), relative_remap=True)
