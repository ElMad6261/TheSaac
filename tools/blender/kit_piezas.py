# -*- coding: utf-8 -*-
"""
kit_piezas.py - Las 13 piezas del kit de TheSaac (matriz del taller de preproduccion).
Usa kit_isaac.py (texturas, materiales, contorno). Convenciones:
  * Escala 1:1, metros. Frente hacia -Y. Origen abajo al centro, salvo piezas que giran
    (hoja de puerta, palanca, tapas de trampilla): origen en la bisagra.
  * Contorno negro (casco invertido de 1 texel) en piezas que se ven de bulto.
    Muros, pisos y techos se repiten lado a lado: su linea negra va pintada en la textura,
    porque el casco dejaria una raya en cada union de modulos.
"""
import bpy, bmesh, math, os
import numpy as np
from mathutils import Matrix
import kit_isaac as kit
from kit_isaac import caja, prisma_partes, torre, losa_hueco, aro, objeto

ESTADO = {}

def M(nombre, tex=None, **kw):
    kw.setdefault('culling', True)
    return kit.mat_t(nombre, tex, **kw)

def hierro():  return M('M_Hierro', 'T_Hierro', rough=0.55, metal=0.4)
def laton():   return M('M_Laton', 'T_Laton', rough=0.45, metal=0.6)
def brea():    return M('M_Brea', 'T_Brea')
def madera():  return M('M_Madera', 'T_Madera')
def madera_o():return M('M_Madera_Oscura', 'T_Madera_Oscura')
def piedra_c():return M('M_Piedra_Clara', 'T_Piedra_Clara')
def negro():   return kit.mat_contorno()

def borde_superior(nombre):
    """Pinta de negro la fila de arriba de una textura de muro: linea dura contra el techo."""
    ruta = os.path.join(kit.DIR_TEX, nombre + ".png")
    img = bpy.data.images.load(ruta, check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    a = a.reshape(h, w, 4)
    a[h - 1, :, :3] = kit.hx(kit.LINEA)
    img.pixels.foreach_set(a.ravel())
    img.save()
    bpy.data.images.remove(img)

def afinar(ob, detalle, factor=0.35):
    """Contorno mas fino (factor x 1 texel) en detalles pequenos: argollas, pernos, tiradores."""
    detalle = set(detalle)
    vg = ob.vertex_groups.new(name="Contorno_Grueso")
    vg.add([i for i in range(len(ob.data.vertices)) if i not in detalle], 1.0, 'REPLACE')
    md = ob.modifiers["Contorno"]
    md.vertex_group = vg.name
    md.thickness_vertex_group = factor
    return ob

def hijo(ob, padre, loc):
    ob.parent = padre
    ob.location = loc
    return ob

# ------------------------------------------------------------------ MUROS
def p_muro_estandar():
    col = kit.coleccion("Muros")
    bm = bmesh.new()
    caja(bm, -1, 1, -0.25, 0.25, 0, 3)
    ob = objeto("Muro_Estandar", bm, [M('M_Muro_Piedra', 'T_Muro_Piedra')], col,
                uv={0: dict(tam=(64, 96), origen=(-1, -0.25, 0))}, con_contorno=False)
    return [ob], [(ob, "Muros", "Muro recto 2 x 3 x 0.5 m. Origen abajo al centro; frente -Y.", ("muro", "estructura"))]

def p_muro_vano():
    col = kit.coleccion("Muros")
    bm = bmesh.new()
    prisma_partes(bm, [[(-1, 0), (-0.75, 0), (-0.75, 2.5), (-1, 2.5)],                       # pie izquierdo
                       [(0.75, 0), (1, 0), (1, 2.5), (0.75, 2.5)],                           # pie derecho
                       [(-1, 2.5), (-0.75, 2.5), (0.75, 2.5), (1, 2.5), (1, 3), (-1, 3)]],  # dintel
                  -0.25, 0.25)
    ob = objeto("Muro_Vano", bm, [M('M_Muro_Piedra', 'T_Muro_Piedra')], col,
                uv={0: dict(tam=(64, 96), origen=(-1, -0.25, 0))}, con_contorno=False)
    return [ob], [(ob, "Muros", "Muro 2 x 3 x 0.5 m con vano de 1.5 x 2.5 m para Puerta_Marco.", ("muro", "puerta", "estructura"))]

def p_pilar():
    col = kit.coleccion("Muros")
    bm = bmesh.new()
    caja(bm, -0.5, 0.5, -0.5, 0.5, 0, 3)
    ob = objeto("Pilar", bm, [M('M_Pilar_Piedra', 'T_Pilar_Piedra')], col,
                uv={0: dict(tam=(32, 96), origen=(-0.5, -0.5, 0))})
    return [ob], [(ob, "Muros", "Pilar 1 x 3 x 1 m para cada union de muros.", ("pilar", "estructura"))]

# ------------------------------------------------------------------ PISOS Y TECHOS
def p_piso():
    col = kit.coleccion("Pisos")
    bm = bmesh.new()
    caja(bm, -5.5, 5.5, -3.5, 3.5, -0.1, 0)
    ob = objeto("Piso_Sala", bm, [M('M_Piso_Sotano', 'T_Piso_Sotano')], col,
                uv={0: dict(tam=(64, 64), origen=(-5.5, -3.5, -0.1))}, con_contorno=False)
    return [ob], [(ob, "Pisos", "Piso de sala 11 x 7 m. La cara de arriba esta en z = 0.", ("piso", "estructura"))]

def p_techo():
    col = kit.coleccion("Pisos")
    bm = bmesh.new()
    caja(bm, -5.5, 5.5, -3.5, 3.5, 0, 0.1)
    ob = objeto("Techo_Sala", bm, [M('M_Techo_Tablas', 'T_Techo_Tablas')], col,
                uv={0: dict(tam=(64, 64), origen=(-5.5, -3.5, 0))}, con_contorno=False)
    return [ob], [(ob, "Pisos", "Techo de sala 11 x 7 m. La cara de abajo esta en z = 0 (colocar a 3 m).", ("techo", "estructura"))]

def p_tragaluz():
    col = kit.coleccion("Pisos")
    bm = bmesh.new()
    losa_hueco(bm, [-5.5, -1, 1, 5.5], [-3.5, -1, 1, 3.5], 0, 0.1, (1, 1), 0)
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        if abs(c.x) <= 1.001 and abs(c.y) <= 1.001 and abs(f.normal.z) < 0.5:
            f.material_index = 1          # canto del hueco: negro duro
    for x in (-0.5, 0.0, 0.5):           # barrotes: rayas de sombra con la luz direccional
        caja(bm, x - 0.03, x + 0.03, -1.1, 1.1, 0.02, 0.08, 2)
    ob = objeto("Techo_Tragaluz", bm, [M('M_Techo_Tablas', 'T_Techo_Tablas'), negro(), hierro()], col,
                uv={None: dict(tam=(64, 64), origen=(-5.5, -3.5, 0)), 2: dict(tam=(16, 16))}, con_contorno=False)
    return [ob], [(ob, "Pisos", "Techo 11 x 7 m con abertura de 2 x 2 m y tres barrotes para la luz direccional.", ("techo", "tragaluz", "estructura"))]

# ------------------------------------------------------------------ PUERTA
def p_puerta():
    col = kit.coleccion("Puerta")
    bm = bmesh.new()
    prisma_partes(bm, [[(-0.75, 0), (-0.6, 0), (-0.6, 2.3), (-0.75, 2.3)],                     # jamba izquierda 15 cm
                       [(0.6, 0), (0.75, 0), (0.75, 2.3), (0.6, 2.3)],                         # jamba derecha 15 cm
                       [(-0.75, 2.3), (-0.6, 2.3), (0.6, 2.3), (0.75, 2.3), (0.75, 2.5), (-0.75, 2.5)]],  # dintel 20 cm
                  -0.25, 0.25)
    marco = objeto("Puerta_Marco", bm, [M('M_Puerta_Marco', 'T_Puerta_Marco')], col,
                   uv={0: dict(tam=(64, 80), origen=(-0.75, -0.25, 0), reglas={'X': (48, 0), 'Z': (48, 0, True)})})

    bm = bmesh.new()
    caja(bm, 0, 1.2, -0.05, 0.05, 0, 2.3, 0)                  # tablero (origen = bisagra)
    for z in (0.35, 1.85):                                    # flejes de hierro, cara frontal y trasera
        caja(bm, 0.03, 1.17, -0.062, -0.045, z, z + 0.1, 1)
        caja(bm, 0.03, 1.17, 0.045, 0.062, z, z + 0.1, 1)
    i0 = len(bm.verts)
    for s in (-1, 1):                                         # argolla de laton a cada lado
        caja(bm, 0.99, 1.03, min(s * 0.045, s * 0.08), max(s * 0.045, s * 0.08), 1.13, 1.18, 2)
        aro(bm, (1.01, s * 0.07, 1.08), 0.06, 0.01, seg=8, plano='XZ', mat=2)
    det = range(i0, len(bm.verts))
    hoja = objeto("Puerta_Hoja", bm, [M('M_Puerta_Hoja', 'T_Puerta_Hoja'), hierro(), laton()], col, loc=(-0.6, 0, 0),
                  uv={0: dict(tam=(48, 80), origen=(0, -0.05, 0), reglas={'X': (40, 0), 'Z': (40, 0, True)}),
                      None: dict(tam=(16, 16))})
    afinar(hoja, det)

    bm = bmesh.new()                                          # origen en el centro de la barra
    caja(bm, -0.62, 0.62, -0.025, 0.025, -0.05, 0.05, 0)       # barra que cruza el vano
    caja(bm, -0.06, 0.06, -0.045, 0.005, -0.21, -0.07, 1)      # candado
    i0 = len(bm.verts)
    aro(bm, (0, -0.02, -0.06), 0.04, 0.008, seg=8, plano='XZ', mat=1)
    det = range(i0, len(bm.verts))
    cerrojo = objeto("Puerta_Cerrojo", bm, [hierro(), laton()], col, loc=(0, -0.095, 1.25),
                     uv={None: dict(tam=(16, 16))})
    afinar(cerrojo, det)
    return [marco, hoja, cerrojo], [(col, "Puertas",
            "Puerta completa: marco 1.5 x 2.5 x 0.5 m, hoja 1.2 x 2.3 x 0.1 m con origen en la bisagra "
            "(gira +90 en Z de Blender / Y de Godot) y cerrojo con candado (visible = bloqueada).", ("puerta", "interactivo"))]

# ------------------------------------------------------------------ ANTORCHA
def p_antorcha():
    col = kit.coleccion("Antorcha")
    bm = bmesh.new()                                          # origen: punto de apoyo en el muro, abajo
    caja(bm, -0.06, 0.06, -0.03, 0.0, 0.08, 0.3, 0)            # placa
    caja(bm, -0.025, 0.025, -0.13, -0.025, 0.16, 0.21, 0)      # brazo
    caja(bm, -0.055, 0.055, -0.225, -0.115, 0.15, 0.22, 0)     # abrazadera
    caja(bm, -0.03, 0.03, -0.2, -0.14, 0.0, 0.36, 1)           # mango
    caja(bm, -0.055, 0.055, -0.225, -0.115, 0.35, 0.43, 2)     # cabeza con brea
    ant = objeto("Antorcha", bm, [hierro(), madera_o(), brea()], col,
                 uv={0: dict(tam=(16, 16)), 1: dict(tam=(32, 32)), 2: dict(tam=(8, 8))})
    bm = bmesh.new()
    kit.llama(bm)
    bmesh.ops.scale(bm, vec=(1.3, 1.3, 1.5), verts=bm.verts)  # 13 x 18 cm
    llama = objeto("Antorcha_Llama", bm, [M('M_Fuego', 'T_Fuego', emision=4.0)], col,
                   uv={0: dict(tam=(8, 16), origen=(-0.065, -0.065, 0))}, con_contorno=False)
    hijo(llama, ant, (0, -0.17, 0.42))
    luz = bpy.data.objects.new("Antorcha_PuntoLuz", None)
    luz.empty_display_type = 'SPHERE'
    luz.empty_display_size = 0.04
    col.objects.link(luz)
    hijo(luz, ant, (0, -0.17, 0.5))
    return [ant, llama, luz], [(col, "Detalles",
            "Antorcha de muro 0.3 x 0.6 x 0.3 m. Antorcha_Llama se oculta cuando esta apagada; "
            "Antorcha_PuntoLuz marca donde va el OmniLight3D.", ("antorcha", "luz", "interactivo"))]

# ------------------------------------------------------------------ INTERRUPTOR
def p_interruptor():
    col = kit.coleccion("Interruptor")
    bm = bmesh.new()
    caja(bm, -0.15, 0.15, -0.06, 0, 0, 0.5, 0)                 # placa de piedra
    caja(bm, -0.025, 0.025, -0.07, -0.05, 0.08, 0.42, 1)       # guia oscura
    caja(bm, -0.05, 0.05, -0.1, -0.05, 0.21, 0.29, 2)          # bisagra
    i0 = len(bm.verts)
    for x in (-0.11, 0.11):                                   # pernos
        for z in (0.06, 0.44):
            caja(bm, x - 0.02, x + 0.02, -0.075, -0.05, z - 0.02, z + 0.02, 2)
    base = objeto("Interruptor", bm, [piedra_c(), brea(), hierro()], col,
                  uv={0: dict(tam=(32, 32), origen=(-0.15, -0.06, 0)), 1: dict(tam=(8, 8)), 2: dict(tam=(16, 16))})
    afinar(base, range(i0, i0 + 32))
    bm = bmesh.new()                                          # origen en el eje de giro
    caja(bm, -0.015, 0.015, -0.015, 0.015, -0.02, 0.15, 0)     # varilla
    caja(bm, -0.035, 0.035, -0.035, 0.035, 0.13, 0.2, 1)       # pomo rojo
    bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.radians(35), 4, 'X'), verts=bm.verts)
    palanca = objeto("Interruptor_Palanca", bm, [hierro(), M('M_Rojo', 'T_Rojo')], col,
                     uv={0: dict(tam=(16, 16)), 1: dict(tam=(8, 8))})
    hijo(palanca, base, (0, -0.08, 0.25))
    return [base, palanca], [(col, "Detalles",
            "Interruptor de palanca 0.3 x 0.5 x 0.2 m. La palanca gira en X: 0 = arriba (apagado), +110 = abajo (activado).",
            ("interruptor", "palanca", "interactivo"))]

# ------------------------------------------------------------------ ROCAS (Geometry Nodes)
def gn_roca():
    viejo = bpy.data.node_groups.get("GN_Roca")
    if viejo:
        bpy.data.node_groups.remove(viejo)
    ng = bpy.data.node_groups.new("GN_Roca", 'GeometryNodeTree')
    if hasattr(ng, "is_modifier"):
        ng.is_modifier = True
    it = ng.interface
    it.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    s = it.new_socket("Semilla", in_out='INPUT', socket_type='NodeSocketInt'); s.default_value = 1
    s = it.new_socket("Variacion", in_out='INPUT', socket_type='NodeSocketFloat'); s.default_value = 0.3; s.min_value = 0.0; s.max_value = 0.5
    s = it.new_socket("Rugosidad", in_out='INPUT', socket_type='NodeSocketFloat'); s.default_value = 0.16; s.min_value = 0.0; s.max_value = 0.4
    s = it.new_socket("Escala_Ruido", in_out='INPUT', socket_type='NodeSocketFloat'); s.default_value = 1.8; s.min_value = 0.1; s.max_value = 10.0
    it.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    def nodo(tipo, x, y, **props):
        n = N.new(tipo); n.location = (x, y)
        for k, v in props.items():
            setattr(n, k, v)
        return n
    def mate(op, x, y, a=None, b=None):
        n = nodo('ShaderNodeMath', x, y, operation=op)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n
    gi = nodo('NodeGroupInput', -1400, 0)
    go = nodo('NodeGroupOutput', 900, 0)
    # 1) Bultos: desplaza cada vertice sobre su normal con ruido 4D (W = semilla)
    pos = nodo('GeometryNodeInputPosition', -1200, 300)
    nor = nodo('GeometryNodeInputNormal', -1200, 420)
    w = mate('MULTIPLY', -1200, 160, gi.outputs['Semilla'], 1.618)
    nz = nodo('ShaderNodeTexNoise', -1000, 300, noise_dimensions='4D')
    L.new(pos.outputs['Position'], nz.inputs['Vector'])
    L.new(w.outputs[0], nz.inputs['W'])
    L.new(gi.outputs['Escala_Ruido'], nz.inputs['Scale'])
    nz.inputs['Detail'].default_value = 1.5
    centro = mate('SUBTRACT', -800, 300, nz.outputs['Fac'] if 'Fac' in nz.outputs else nz.outputs[0], 0.5)
    amp = mate('MULTIPLY', -800, 140, gi.outputs['Rugosidad'], 4.0)
    desp = mate('MULTIPLY', -620, 260, centro.outputs[0], amp.outputs[0])
    off = nodo('ShaderNodeVectorMath', -440, 360, operation='SCALE')
    L.new(nor.outputs['Normal'], off.inputs[0])
    L.new(desp.outputs[0], off.inputs['Scale'])
    sp = nodo('GeometryNodeSetPosition', -240, 0)
    L.new(gi.outputs['Geometry'], sp.inputs['Geometry'])
    L.new(off.outputs['Vector'], sp.inputs['Offset'])
    # 2) Tamano: escala aleatoria por eje dentro de +-Variacion, y giro aleatorio en Z
    lo = mate('SUBTRACT', -800, -200, 1.0, gi.outputs['Variacion'])
    hi = mate('ADD', -800, -360, 1.0, gi.outputs['Variacion'])
    cmin = nodo('ShaderNodeCombineXYZ', -620, -200)
    cmax = nodo('ShaderNodeCombineXYZ', -620, -360)
    for i in range(3):
        L.new(lo.outputs[0], cmin.inputs[i])
        L.new(hi.outputs[0], cmax.inputs[i])
    rnd = nodo('FunctionNodeRandomValue', -440, -260, data_type='FLOAT_VECTOR')
    L.new(cmin.outputs[0], rnd.inputs[0])
    L.new(cmax.outputs[0], rnd.inputs[1])
    L.new(gi.outputs['Semilla'], rnd.inputs['ID'])
    rnd.inputs['Seed'].default_value = 11
    ang = nodo('FunctionNodeRandomValue', -440, -480, data_type='FLOAT')
    ang.inputs[2].default_value = 0.0
    ang.inputs[3].default_value = 2 * math.pi
    L.new(gi.outputs['Semilla'], ang.inputs['ID'])
    ang.inputs['Seed'].default_value = 5
    eul = nodo('ShaderNodeCombineXYZ', -240, -480)
    L.new(ang.outputs[1], eul.inputs['Z'])
    e2r = nodo('FunctionNodeEulerToRotation', -60, -480)
    L.new(eul.outputs[0], e2r.inputs[0])
    tr = nodo('GeometryNodeTransform', 120, 0)
    L.new(sp.outputs['Geometry'], tr.inputs['Geometry'])
    L.new(e2r.outputs[0], tr.inputs['Rotation'])
    L.new(rnd.outputs[0], tr.inputs['Scale'])
    # 3) Apoyar en el suelo: sube la roca hasta que su punto mas bajo quede en z = 0
    bb = nodo('GeometryNodeBoundBox', 300, -240)
    L.new(tr.outputs['Geometry'], bb.inputs['Geometry'])
    sep = nodo('ShaderNodeSeparateXYZ', 480, -240)
    L.new(bb.outputs['Min'], sep.inputs[0])
    neg = mate('MULTIPLY', 640, -240, sep.outputs['Z'], -1.0)
    sube = nodo('ShaderNodeCombineXYZ', 640, -80)
    L.new(neg.outputs[0], sube.inputs['Z'])
    tr2 = nodo('GeometryNodeTransform', 720, 0)
    L.new(tr.outputs['Geometry'], tr2.inputs['Geometry'])
    L.new(sube.outputs[0], tr2.inputs['Translation'])
    L.new(tr2.outputs['Geometry'], go.inputs['Geometry'])
    return ng

def ids_entrada(ng):
    return {i.name: i.identifier for i in ng.interface.items_tree
            if getattr(i, 'item_type', 'SOCKET') == 'SOCKET' and i.in_out == 'INPUT'}

def p_rocas():
    col = kit.coleccion("Rocas")
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
    bmesh.ops.scale(bm, vec=(1, 1, 0.8), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, 0.4), verts=bm.verts)
    base = objeto("Roca_01", bm, [M('M_Roca', 'T_Roca')], col,
                  uv={0: dict(tam=(32, 32), origen=(-0.5, -0.5, 0))}, con_contorno=False)
    base.data.name = "Roca_Base"
    ng = gn_roca()
    ids = ids_entrada(ng)
    rocas = []
    for k, (sem, rug, esc) in enumerate(((1, 0.16, 1.4), (2, 0.20, 1.8), (3, 0.14, 1.2), (4, 0.18, 2.0))):
        if k == 0:
            ob = base
        else:
            ob = bpy.data.objects.new("Roca_%02d" % (k + 1), base.data)
            col.objects.link(ob)
        md = ob.modifiers.new("GN_Roca", 'NODES')
        md.node_group = ng
        md[ids['Semilla']] = sem
        md[ids['Rugosidad']] = rug
        md[ids['Escala_Ruido']] = esc
        kit.contorno(ob)
        ob.location = (-2.4 + 1.6 * k, 0, 0)
        rocas.append(ob)
    marcas = [(ob, "Detalles", "Roca generada con GN_Roca (semilla %d). Base 1 x 0.8 x 1 m, +-30 %%." % (k + 1),
               ("roca", "geometry nodes")) for k, ob in enumerate(rocas)]
    marcas.append((ng, "Detalles", "Generador de rocas: Semilla, Variacion (+-), Rugosidad, Escala_Ruido.", ("roca", "geometry nodes")))
    return rocas, marcas

# ------------------------------------------------------------------ PEDESTAL
def p_pedestal():
    col = kit.coleccion("Pedestal")
    bm = bmesh.new()
    torre(bm, [(0.4, 0.4, 0.0), (0.4, 0.4, 0.15), (0.3, 0.3, 0.15), (0.3, 0.3, 0.85),
               (0.4, 0.4, 0.85), (0.4, 0.4, 1.0)])
    ob = objeto("Pedestal", bm, [piedra_c()], col, uv={0: dict(tam=(32, 32), origen=(-0.4, -0.4, 0))})
    return [ob], [(ob, "Detalles", "Pedestal de piedra 0.8 x 1 x 0.8 m (sala del tesoro).", ("pedestal", "tesoro"))]

# ------------------------------------------------------------------ TRAMPILLA
def p_trampilla():
    col = kit.coleccion("Trampilla")
    bm = bmesh.new()
    losa_hueco(bm, [-0.75, -0.55, 0.55, 0.75], [-0.75, -0.55, 0.55, 0.75], 0, 0.15, (1, 1), 0)
    marco = objeto("Trampilla", bm, [madera_o()], col, uv={0: dict(tam=(32, 32), origen=(-0.75, -0.75, 0))})
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in ((-0.55, -0.55, 0.005), (0.55, -0.55, 0.005), (0.55, 0.55, 0.005), (-0.55, 0.55, 0.005))]
    bm.faces.new(v)
    hueco = objeto("Trampilla_Hueco", bm, [negro()], col, con_contorno=False, recalc=False)
    hueco.data.polygons[0].flip() if hueco.data.polygons[0].normal.z < 0 else None
    tapas = []
    for nombre, lado in (("Trampilla_Tapa_I", -1), ("Trampilla_Tapa_D", 1)):
        x0, x1 = (0.0, 0.55) if lado < 0 else (-0.55, 0.0)
        bm = bmesh.new()
        caja(bm, x0, x1, -0.55, 0.55, -0.02, 0.02, 0)              # tablero
        bx = 0.33 if lado < 0 else -0.33
        caja(bm, bx - 0.035, bx + 0.035, -0.5, 0.5, 0.015, 0.03, 1)  # fleje
        tx = 0.47 if lado < 0 else -0.47
        i0 = len(bm.verts)
        aro(bm, (tx, 0, 0.03), 0.04, 0.008, seg=8, plano='XY', mat=2)  # tirador
        t = objeto(nombre, bm, [madera(), hierro(), laton()], col, loc=(lado * 0.55, 0, 0.13),
                   uv={0: dict(tam=(32, 32), origen=(x0, -0.55, -0.02)), None: dict(tam=(16, 16))})
        afinar(t, range(i0, len(t.data.vertices)))
        tapas.append(t)
    return [marco, hueco] + tapas, [(col, "Detalles",
            "Trampilla de salida 1.5 x 0.15 x 1.5 m. Tapas con origen en su bisagra: abrir girando en Y "
            "(Tapa_I -110, Tapa_D +110). Trampilla_Hueco es el fondo negro.", ("trampilla", "meta", "interactivo"))]

PIEZAS = [
    ("muro_estandar.blend", p_muro_estandar),
    ("muro_vano.blend", p_muro_vano),
    ("pilar.blend", p_pilar),
    ("piso_sala.blend", p_piso),
    ("techo_sala.blend", p_techo),
    ("techo_tragaluz.blend", p_tragaluz),
    ("puerta.blend", p_puerta),
    ("antorcha.blend", p_antorcha),
    ("interruptor.blend", p_interruptor),
    ("rocas.blend", p_rocas),
    ("pedestal.blend", p_pedestal),
    ("trampilla.blend", p_trampilla),
]

# ------------------------------------------------------------------ verificacion y flujo
def medir(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for ob in objs:
        info = dict(loc=[round(c, 3) for c in ob.location], padre=ob.parent.name if ob.parent else None)
        if ob.type == 'MESH':
            ev = ob.evaluated_get(dg)
            me = ev.to_mesh()
            nombres = [m.name if m else None for m in me.materials]
            cnt, xs, ys, zs = {}, [], [], []
            for p in me.polygons:
                mn = nombres[p.material_index] if p.material_index < len(nombres) else "FUERA_DE_RANGO_%d" % p.material_index
                cnt[mn] = cnt.get(mn, 0) + 1
                if mn != 'M_Contorno' or ob.name in ('Trampilla_Hueco',):
                    for vi in p.vertices:
                        co = me.vertices[vi].co
                        xs.append(co.x); ys.append(co.y); zs.append(co.z)
            ev.to_mesh_clear()
            bm = bmesh.new(); bm.from_mesh(ob.data)
            nm = sum(1 for e in bm.edges if not e.is_manifold)
            bm.free()
            info.update(tam=[round(max(a) - min(a), 3) for a in (xs, ys, zs)],
                        z=[round(min(zs), 3), round(max(zs), 3)], caras=cnt, no_manifold=nm,
                        contorno=any(m.type == 'SOLIDIFY' for m in ob.modifiers))
        out[ob.name] = info
    return out

def construir(i):
    archivo, fn = PIEZAS[i]
    kit.limpiar()
    objs, marcas = fn()
    for id_, cat, desc, tags in marcas:
        kit.marcar(id_, cat, desc, tags)
    kit.encuadrar([o for o in objs if o.type == 'MESH'])
    ESTADO['pendiente'] = (archivo, [m[0].name for m in marcas], [type(m[0]).__name__ for m in marcas])
    return dict(archivo=archivo, piezas=medir(objs))

def guardar_pendiente():
    p = ESTADO.pop('pendiente', None)
    if not p:
        return None
    archivo, nombres, tipos = p
    prev = {}
    for n, t in zip(nombres, tipos):
        coleccion = {'Object': bpy.data.objects, 'Collection': bpy.data.collections, 'GeometryNodeTree': bpy.data.node_groups}.get(t, bpy.data.objects)
        id_ = coleccion.get(n)
        pv = getattr(id_, 'preview', None) if id_ else None
        prev[n] = bool(pv and pv.image_size[0] > 0)
    ruta = kit.guardar(archivo)
    return dict(guardado=ruta, miniaturas=prev)
