# -*- coding: utf-8 -*-
"""
variantes_puerta.py - Puertas de la sala del tesoro y de la sala del jefe (Blender 5.1).

Copia la coleccion "Puerta" de assets/blend/puerta.blend, le cambia texturas y herrajes y le agrega
los adornos modelados de cada variante. puerta.blend no se modifica.

    assets/blend/puerta_tesoro.blend   coleccion Puerta_Tesoro
        Puerta_Moldura   borde dorado en relieve sobre el marco + remates en las esquinas de arriba
        Puerta_Corona    corona sobre el vano (banda curva con gemas, cinco puntas con orbes)
        Puerta_Llave     llave de oro en las dos caras de la hoja (hija de Puerta_Hoja: gira con ella)
    assets/blend/puerta_jefe.blend     coleccion Puerta_Jefe
        Puerta_Calavera  calavera sobre el vano, con cuencas hondas y brasas

Los adornos de arriba van en las dos caras del muro (la puerta se ve igual desde las dos salas).
Corona, llave y calavera salen de sprites de texturas_v2.py, asi que el modelo calza pixel a pixel con
la textura: en la llave y la calavera cada pixel solido es un prisma con su altura; la corona es una sola
pieza de lados rectos doblada en media elipse. Todo lleva el contorno negro del kit (mas grueso en
corona y calavera).
Puerta_Marco y Puerta_Hoja conservan nombre, geometria y origen (bisagra): el script de puerta de Godot
sirve igual para las tres puertas.

Uso, desde la raiz del repositorio, despues de texturas_v2.py:
    blender --background --factory-startup --python tools/blender/variantes_puerta.py
En modo --background Blender no genera miniaturas (Asset Browser: clic derecho -> Generate Preview).
"""
import bpy, bmesh, math, os, sys
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import texturas_v2 as tex
from kit_isaac import uv_caja, prisma_partes, caja

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DIR_BLEND = os.path.join(RAIZ, "assets", "blend")
DIR_TEX = os.path.join(RAIZ, "assets", "texturas")
CATALOGO_PUERTAS = "6a1f3c2e-4b5d-4e8f-9a01-2b3c4d5e6f03"
PX = 1.0 / 32                    # un pixel de textura en metros
CONTORNO = 1.0 / 32              # grosor del contorno negro (1 texel, como el resto del kit)
CONTORNO_GRUESO = 1.5 / 32       # corona y calavera: linea mas pesada para que se lean de lejos
CARA = 0.25                      # el marco ocupa y = -0.25 (frente) a +0.25 (fondo), igual que el muro

# Materiales nuevos: (material de puerta.blend que se copia, textura de la copia)
MATERIALES = {
    "M_Puerta_Marco_Tesoro": ("M_Puerta_Marco", "T_Puerta_Marco_Tesoro"),
    "M_Puerta_Hoja_Tesoro": ("M_Puerta_Hoja", "T_Puerta_Hoja_Tesoro"),
    "M_Oro_Tesoro": ("M_Laton", "T_Oro_Tesoro"),
    "M_Corona": ("M_Laton", "T_Corona"),
    "M_Llave": ("M_Laton", "T_Llave"),
    "M_Puerta_Marco_Jefe": ("M_Puerta_Marco", "T_Puerta_Marco_Jefe"),
    "M_Puerta_Hoja_Jefe": ("M_Puerta_Hoja", "T_Puerta_Hoja_Jefe"),
    "M_Calavera": ("M_Puerta_Marco", "T_Calavera"),
}


def limpiar():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for _ in range(3):
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)


def cargar_puerta():
    """Anexa (no vincula) la coleccion Puerta de puerta.blend y la deja en la escena."""
    with bpy.data.libraries.load(os.path.join(DIR_BLEND, "puerta.blend"), link=False) as (_, dst):
        dst.collections = ["Puerta"]
    col = dst.collections[0]
    bpy.context.scene.collection.children.link(col)
    for lib in list(bpy.data.libraries):
        bpy.data.libraries.remove(lib)
    return col


def material(nombre):
    m = bpy.data.materials.get(nombre)
    if m is None:
        base, textura = MATERIALES[nombre]
        m = bpy.data.materials[base].copy()
        m.name = nombre
        img = bpy.data.images.load(os.path.join(DIR_TEX, textura + ".png"), check_existing=True)
        for nodo in m.node_tree.nodes:
            if nodo.type == 'TEX_IMAGE':
                nodo.image = img
        px = img.pixels[:]                     # color del modo Solid = promedio de la textura
        n = len(px) // 4
        m.diffuse_color = (sum(px[0::4]) / n, sum(px[1::4]) / n, sum(px[2::4]) / n, 1.0)
    return m


def objeto(nombre, bm, mats, col, padre=None, uv=None, grosor=CONTORNO, parejo=True):
    """Malla con sombreado plano, UV por caja para los materiales de 'uv' y contorno negro.
    parejo=False en los relieves: el grosor parejo saca puntas negras en sus esquinas finas."""
    bm.normal_update()
    for f in bm.faces:
        f.smooth = False
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    if uv:
        uv_caja(me, uv)
    ob = bpy.data.objects.new(nombre, me)
    col.objects.link(ob)
    if padre is not None:
        ob.parent = padre
    me.materials.append(bpy.data.materials["M_Contorno"])        # casco invertido, como kit_isaac.contorno
    md = ob.modifiers.new("Contorno", 'SOLIDIFY')
    md.thickness = grosor
    md.offset = 1.0
    md.use_flip_normals = True
    md.use_rim = False
    md.use_even_offset = parejo
    md.use_quality_normals = True
    md.material_offset = len(me.materials) - 1
    return ob


# ------------------------------------------------------------------ relieve de un sprite
def relieve(bm, sp, mapa, mat=0, fondo=-0.01):
    """Cada pixel solido del sprite es un prisma: frente a su altura, fondo plano y cantos en el borde.
    mapa(u, v, h) -> (x, y, z): u, v = esquina en pixeles (v hacia abajo), h = metros hacia afuera."""
    W, H = sp.w, sp.h
    uvl = bm.loops.layers.uv.get("UVMap") or bm.loops.layers.uv.new("UVMap")

    def sol(x, y):
        return 0 <= x < W and 0 <= y < H and sp.solido[y][x]

    def alto(i, j):                            # esquina = promedio de los pixeles que la tocan
        v = [sp.alto[y][x] for x, y in ((i - 1, j - 1), (i, j - 1), (i - 1, j), (i, j)) if sol(x, y)]
        return sum(v) / len(v)
    frente, atras, caras = {}, {}, []

    def vf(i, j):
        if (i, j) not in frente:
            frente[i, j] = bm.verts.new(mapa(i, j, alto(i, j)))
        return frente[i, j]

    def va(i, j):
        if (i, j) not in atras:
            atras[i, j] = bm.verts.new(mapa(i, j, fondo))
        return atras[i, j]

    for y in range(H):
        for x in range(W):
            if not sol(x, y):
                continue
            esq = [(x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)]
            caras.append((bm.faces.new([vf(i, j) for i, j in esq]), esq, x, y, False))
            caras.append((bm.faces.new([va(i, j) for i, j in esq[::-1]]), esq[::-1], x, y, False))
            for (dx, dy), (a, b) in (((0, -1), (esq[0], esq[1])), ((1, 0), (esq[1], esq[2])),
                                     ((0, 1), (esq[2], esq[3])), ((-1, 0), (esq[3], esq[0]))):
                if not sol(x + dx, y + dy):        # canto entre este pixel y uno vacio
                    caras.append((bm.faces.new([vf(*a), vf(*b), va(*b), va(*a)]), None, x, y, True))
    for f, esq, x, y, canto in caras:
        f.material_index = mat
        for k, lp in enumerate(f.loops):           # frente y fondo: esquina del pixel; canto: centro del pixel
            u, v = (x + 0.5, y + 0.5) if canto else esq[k]
            lp[uvl].uv = (u / W, 1.0 - v / H)
    bmesh.ops.recalc_face_normals(bm, faces=[c[0] for c in caras])
    return [c[0] for c in caras]


def perfil_curvo(bm, sp, mapa, arriba, abajo, cortes, alto, mat=0, fondo=0.0):
    """Silueta del sprite descrita por columnas (v de arriba y de abajo en cada u), extruida 'alto' metros
    y doblada con mapa(). Una sola malla cerrada: sin aristas internas donde el contorno pueda asomar."""
    uvl = bm.loops.layers.uv.get("UVMap") or bm.loops.layers.uv.new("UVMap")
    col = []
    for u in cortes:
        vt, vb = arriba(u), abajo(u)
        col.append((u, vt, vb, [(bm.verts.new(mapa(u, vt, h)), bm.verts.new(mapa(u, vb, h))) for h in (alto, fondo)]))
    caras = []

    def cara(vs, uvs):
        f = bm.faces.new(vs)
        f.material_index = mat
        for lp, (u, v) in zip(f.loops, uvs):
            lp[uvl].uv = (u / sp.w, 1.0 - v / sp.h)
        caras.append(f)
    for (ua, vta, vba, pa), (ub, vtb, vbb, pb) in zip(col, col[1:]):
        (fa_t, fa_b), (ba_t, ba_b) = pa
        (fb_t, fb_b), (bb_t, bb_b) = pb
        cara([fa_t, fb_t, fb_b, fa_b], [(ua, vta), (ub, vtb), (ub, vbb), (ua, vba)])        # frente
        cara([ba_b, bb_b, bb_t, ba_t], [(ua, vba), (ub, vbb), (ub, vtb), (ua, vta)])        # fondo
        cara([fa_t, ba_t, bb_t, fb_t], [(ua, vta + 0.5)] * 2 + [(ub, vtb + 0.5)] * 2)        # canto de arriba
        cara([fa_b, fb_b, bb_b, ba_b], [(ua, vba - 0.5)] * 2 + [(ub, vbb - 0.5)] * 2)        # canto de abajo
    for u, vt, vb, ((f_t, f_b), (b_t, b_b)) in (col[0], col[-1]):                           # tapas laterales
        cara([f_t, f_b, b_b, b_t], [(u, vt), (u, vb), (u, vb), (u, vt)])
    bmesh.ops.recalc_face_normals(bm, faces=caras)
    return caras


def plano(sp, x_izq, z_arriba, y_pared, signo, espejo=False):
    """Sprite plano sobre una pared vertical: sale hacia y = y_pared + signo * h."""
    def f(u, v, h):
        x = x_izq + (sp.w - u if espejo else u) * PX
        return (x, y_pared + signo * h, z_arriba - v * PX)
    return f


def curvo(sp, a, b, y_pared, signo, z_base):
    """Sprite doblado en media elipse (semiejes a en X, b hacia afuera) apoyada en la pared."""
    n = 720
    ts = [math.pi * (1 - k / n) for k in range(n + 1)]           # de la izquierda (pi) a la derecha (0)
    acum = [0.0]
    for k in range(n):
        acum.append(acum[-1] + math.hypot(a * (math.cos(ts[k + 1]) - math.cos(ts[k])),
                                          b * (math.sin(ts[k + 1]) - math.sin(ts[k]))))
    yc = y_pared - signo * 0.02                                  # la elipse arranca 2 cm dentro del muro

    def theta(s):
        lo, hi = 0, n
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if acum[mid] < s:
                lo = mid
            else:
                hi = mid
        t = (s - acum[lo]) / max(1e-9, acum[hi] - acum[lo])
        return ts[lo] + (ts[hi] - ts[lo]) * t

    def f(u, v, h):
        t = theta(u / sp.w * acum[-1])
        nx, ny = b * math.cos(t), a * math.sin(t)
        nn = math.hypot(nx, ny)
        x = a * math.cos(t) + nx / nn * h
        p = b * math.sin(t) + ny / nn * h
        return (x, yc + signo * p, z_base + (sp.h - v) * PX)
    return f


def esfera(bm, centro, radio, mat, seg=10):
    r = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2 + 1, radius=radio,
                                  matrix=Matrix.Translation(centro))
    for f in {f for v in r['verts'] for f in v.link_faces}:
        f.material_index = mat


# ------------------------------------------------------------------ adornos
def adornos_tesoro(col, marco, hoja):
    # borde dorado: placa en U de 4 cm sobre cada cara del marco + remate (pedestal y orbe) en cada esquina
    bm = bmesh.new()
    u = [[(-0.735, 0), (-0.6, 0), (-0.6, 2.3), (-0.735, 2.3)],
         [(0.6, 0), (0.735, 0), (0.735, 2.3), (0.6, 2.3)],
         [(-0.735, 2.3), (-0.6, 2.3), (0.6, 2.3), (0.735, 2.3), (0.735, 2.485), (-0.735, 2.485)]]
    prisma_partes(bm, u, -CARA - 0.04, -CARA, mat=0)
    prisma_partes(bm, u, CARA, CARA + 0.04, mat=1)
    for s in (-1, 1):
        for xc in (-0.665, 0.665):
            y0, y1 = sorted((s * (CARA - 0.01), s * (CARA + 0.12)))
            caja(bm, xc - 0.085, xc + 0.085, y0, y1, 2.45, 2.55, 2)
            esfera(bm, (xc, s * (CARA + 0.06), 2.615), 0.068, 2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    marco_uv = dict(tam=(64, 80), reglas={'X': (48, 0), 'Z': (48, 0, True)})
    objeto("Puerta_Moldura", bm, [material("M_Puerta_Marco_Tesoro")] * 2 + [material("M_Oro_Tesoro")], col,
           uv={0: dict(marco_uv, origen=(-0.75, -0.40, 0)),       # los cantos de la placa caen en el oro acanalado
               1: dict(marco_uv, origen=(-0.75, 0.14, 0)),
               2: dict(tam=(16, 16))})
    # corona sobre el vano, en las dos caras
    sp = tex.corona()
    bm = bmesh.new()

    def arriba(u):                       # borde de arriba: banda y, sobre ella, cinco puntas triangulares
        v = sp.banda
        for c, alto in tex.CORONA_PUNTAS:
            if abs(u - c) < 4.0:
                v = min(v, sp.banda - alto * (1 - abs(u - c) / 4.0))
        return v
    valles = []                          # donde se cruzan las faldas de dos puntas vecinas
    for (c1, a1), (c2, a2) in zip(tex.CORONA_PUNTAS, tex.CORONA_PUNTAS[1:]):
        u = (a2 * (1 - c2 / 4.0) - a1 * (1 + c1 / 4.0)) / (-a1 / 4.0 - a2 / 4.0)
        valles.append(u if c2 - 4.0 < u < c1 + 4.0 else None)
    quiebres = {0.0, float(sp.w)} | {c for c, _ in tex.CORONA_PUNTAS} | {u for u in valles if u is not None}
    # tiras de 1 px para seguir la curva, pero ninguna a menos de 1.5 px de un valle: ahi el contorno
    # empuja los vertices de las dos faldas hacia el valle y, si estan muy juntos, se cruzan y asoma
    cortes = sorted(quiebres | {float(k) for k in range(sp.w + 1)
                                if all(u is None or abs(k - u) >= 1.5 for u in valles)})
    for s in (-1, 1):
        f = curvo(sp, 0.45, 0.22, s * CARA, s, 2.42)
        perfil_curvo(bm, sp, f, arriba, lambda u: sp.h, cortes, 0.07)
        for nombre, (c, fila) in sp.puntos.items():
            r = 0.07 if nombre == "punta_17" else 0.06
            x, y, z = f(c, fila, 0.035)
            esfera(bm, (x, y, z + r * 0.1), r, 1)          # el orbe envuelve la punta (y su contorno)
    objeto("Puerta_Corona", bm, [material("M_Corona"), material("M_Oro_Tesoro")], col, uv={1: dict(tam=(16, 16))},
           grosor=CONTORNO_GRUESO, parejo=False)
    # llave en las dos caras de la hoja (coordenadas de la hoja: bisagra en x = 0, ancho 1.2 m)
    sp = tex.llave()
    bm = bmesh.new()
    x_izq, z_arriba = 0.6 - sp.w * PX / 2, 1.67
    relieve(bm, sp, plano(sp, x_izq, z_arriba, -0.05, -1), fondo=-0.005)
    relieve(bm, sp, plano(sp, x_izq, z_arriba, 0.05, 1, espejo=True), fondo=-0.005)
    objeto("Puerta_Llave", bm, [material("M_Llave")], col, padre=hoja, parejo=False)


def adornos_jefe(col, marco, hoja):
    sp = tex.calavera()
    bm = bmesh.new()
    x_izq, z_arriba = -sp.w * PX / 2, 2.28 + sp.h * PX
    relieve(bm, sp, plano(sp, x_izq, z_arriba, -CARA, -1))
    relieve(bm, sp, plano(sp, x_izq, z_arriba, CARA, 1, espejo=True))
    objeto("Puerta_Calavera", bm, [material("M_Calavera")], col, grosor=CONTORNO_GRUESO, parejo=False)


# ------------------------------------------------------------------ variantes
# Material de cada hueco, en orden. El ultimo hueco (M_Contorno) no se toca.
#   Puerta_Hoja: tablas, herrajes, argollas
VARIANTES = [
    dict(archivo="puerta_tesoro.blend", coleccion="Puerta_Tesoro", adornos=adornos_tesoro,
         huecos={"Puerta_Marco": ["M_Puerta_Marco_Tesoro"],
                 "Puerta_Hoja": ["M_Puerta_Hoja_Tesoro", "M_Oro_Tesoro", "M_Oro_Tesoro"]},
         descripcion="Puerta de la sala del tesoro. Misma geometria y nombres que Puerta, en oro: borde dorado en "
                     "relieve con remates en las esquinas (Puerta_Moldura), corona con orbes sobre el vano "
                     "(Puerta_Corona) y llave en la hoja (Puerta_Llave, hija de Puerta_Hoja).",
         etiquetas=("puerta", "interactivo", "tesoro")),
    dict(archivo="puerta_jefe.blend", coleccion="Puerta_Jefe", adornos=adornos_jefe,
         huecos={"Puerta_Marco": ["M_Puerta_Marco_Jefe"],
                 "Puerta_Hoja": ["M_Puerta_Hoja_Jefe", "M_Hierro", "M_Hierro"]},
         descripcion="Puerta de la sala del jefe. Misma geometria y nombres que Puerta: marco de basalto con brasas, "
                     "hoja de hierro remachado y calavera sobre el vano (Puerta_Calavera).",
         etiquetas=("puerta", "interactivo", "jefe")),
]


def crear(v):
    limpiar()
    col = cargar_puerta()
    cerrojo = bpy.data.objects.get("Puerta_Cerrojo")             # por si puerta.blend es anterior y lo trae
    if cerrojo is not None:
        bpy.data.objects.remove(cerrojo, do_unlink=True)
    for nombre_ob, mats in v["huecos"].items():
        ob = bpy.data.objects[nombre_ob]
        for i, nombre_mat in enumerate(mats):
            ob.material_slots[i].material = material(nombre_mat)
    v["adornos"](col, bpy.data.objects["Puerta_Marco"], bpy.data.objects["Puerta_Hoja"])
    for _ in range(3):           # quita materiales e imagenes que ya no se usan
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    col.name = v["coleccion"]
    if col.asset_data is None:
        col.asset_mark()
    ad = col.asset_data
    ad.catalog_id = CATALOGO_PUERTAS
    ad.description = v["descripcion"]
    ad.author = "TheSaac"
    for t in list(ad.tags):
        ad.tags.remove(t)
    for t in v["etiquetas"]:
        ad.tags.new(t, skip_if_exists=True)
    try:
        col.asset_generate_preview()
    except Exception:
        pass
    for img in bpy.data.images:  # rutas relativas al .blend, como en el resto del kit
        if img.source == 'FILE' and img.filepath and not img.filepath.startswith("//"):
            img.filepath = bpy.path.relpath(img.filepath, start=DIR_BLEND)
    ruta = os.path.join(DIR_BLEND, v["archivo"])
    bpy.ops.wm.save_as_mainfile(filepath=ruta, relative_remap=False)
    return ruta


def generar():
    """Crea puerta_tesoro.blend y puerta_jefe.blend. Devuelve sus rutas."""
    fp = bpy.context.preferences.filepaths
    antes = fp.save_version
    fp.save_version = 0          # sin .blend1
    try:
        return [crear(v) for v in VARIANTES]
    finally:
        fp.save_version = antes


if __name__ == "__main__":
    for r in generar():
        print("Guardado", r)
