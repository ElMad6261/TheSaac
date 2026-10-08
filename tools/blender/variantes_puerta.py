# -*- coding: utf-8 -*-
"""
variantes_puerta.py - Puertas de la sala del tesoro y de la sala del jefe (Blender 5.1).

Copia la coleccion "Puerta" de assets/blend/puerta.blend, le cambia texturas y herrajes y le agrega
los adornos modelados de cada variante. puerta.blend no se modifica.

Las dos comparten la misma arquitectura (Puerta_Portal), hecha de bloques gruesos con el borde de
adelante redondeado: basas de dos escalones, pilastras que se abren hacia arriba, capiteles, un dintel
macizo y una cornisa que vuela sobre el. Cada variante le pone su emblema al centro del dintel y sus
remates en las esquinas de arriba.

    assets/blend/puerta_tesoro.blend   coleccion Puerta_Tesoro (solo la paleta del tesoro)
        Puerta_Portal    portal de oro: pilastras con una moldura y tachones, un medallon en cada bloque
                         del dintel, un orbe sobre cada esquina y un friso acolchado oscuro tras la corona
        Puerta_Corona    corona como clave del portal (banda curva con gemas, cinco puntas con orbes)
        Puerta_Llave     llave de oro en las dos caras de la hoja (hija de Puerta_Hoja: gira con ella)
    assets/blend/puerta_jefe.blend     coleccion Puerta_Jefe (solo la paleta del jefe)
        Puerta_Portal    pilastras de sillares con vetas rojas y zunchos; basas, capiteles, dintel y
                         cornisa de metal oscuro; friso rojo acanalado que brilla detras de la calavera
        Puerta_Puas      puas de metal: tres en abanico en cada esquina y una a cada lado de la calavera
        Puerta_Calavera  calavera maciza como clave del portal, con brasas rojas que brillan en las cuencas

Portal y adornos van en las dos caras del muro (la puerta se ve igual desde las dos salas).
Corona, llave y calavera salen de sprites de texturas_v2.py, asi que el modelo calza pixel a pixel con
la textura: en la llave y la calavera cada pixel solido es un prisma con su altura; la corona es una sola
pieza de lados rectos doblada en media elipse. Todo lleva el contorno negro del kit (mas grueso en
corona y calavera).
Puerta_Marco y Puerta_Hoja conservan nombre, geometria y origen (bisagra): el script de puerta de Godot
sirve igual para las tres puertas. Nada de los adornos baja de z = 2.34 entre las pilastras (la hoja,
de 2.30 m, pasa por debajo al abrirse) ni pasa de x = +-0.70 hacia el vano, y nada sube de 2.97 (techo a 3 m).

Uso, desde la raiz del repositorio, despues de texturas_v2.py:
    blender --background --factory-startup --python tools/blender/variantes_puerta.py
En modo --background Blender no genera miniaturas (Asset Browser: clic derecho -> Generate Preview).
"""
import bpy, bmesh, math, os, sys
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import texturas_v2 as tex
from kit_isaac import uv_caja

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DIR_BLEND = os.path.join(RAIZ, "assets", "blend")
DIR_TEX = os.path.join(RAIZ, "assets", "texturas")
CATALOGO_PUERTAS = "6a1f3c2e-4b5d-4e8f-9a01-2b3c4d5e6f03"
PX = 1.0 / 32                    # un pixel de textura en metros
CONTORNO = 1.0 / 32              # grosor del contorno negro (1 texel, como el resto del kit)
CONTORNO_GRUESO = 1.5 / 32       # corona y calavera: linea mas pesada para que se lean de lejos
CARA = 0.25                      # el marco ocupa y = -0.25 (frente) a +0.25 (fondo), igual que el muro

# Materiales nuevos: (material de puerta.blend que se copia, textura de la copia[, textura de brillo, fuerza])
MATERIALES = {
    "M_Puerta_Marco_Tesoro": ("M_Puerta_Marco", "T_Puerta_Marco_Tesoro"),
    "M_Puerta_Hoja_Tesoro": ("M_Puerta_Hoja", "T_Puerta_Hoja_Tesoro"),
    "M_Oro_Tesoro": ("M_Laton", "T_Oro_Tesoro"),
    "M_Corona": ("M_Laton", "T_Corona"),
    "M_Llave": ("M_Laton", "T_Llave"),
    "M_Friso_Tesoro": ("M_Puerta_Marco", "T_Friso_Tesoro"),
    "M_Puerta_Marco_Jefe": ("M_Puerta_Marco", "T_Puerta_Marco_Jefe"),
    "M_Puerta_Hoja_Jefe": ("M_Puerta_Hoja", "T_Puerta_Hoja_Jefe"),
    "M_Piedra_Jefe": ("M_Puerta_Marco", "T_Piedra_Jefe"),
    "M_Metal_Jefe": ("M_Puerta_Marco", "T_Metal_Jefe"),           # mate: los colores de la paleta, sin brillo gris
    "M_Friso_Jefe": ("M_Puerta_Marco", "T_Friso_Jefe", "T_Friso_Jefe", 1.5),
    "M_Calavera": ("M_Puerta_Marco", "T_Calavera", "T_Calavera_Brillo", 6.0),
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
        base, textura, *brillo = MATERIALES[nombre]
        m = bpy.data.materials[base].copy()
        m.name = nombre
        img = bpy.data.images.load(os.path.join(DIR_TEX, textura + ".png"), check_existing=True)
        nt = m.node_tree
        for nodo in nt.nodes:
            if nodo.type == 'TEX_IMAGE':
                nodo.image = img
        if brillo:                             # emision con su propia textura (negro = no brilla)
            mapa, fuerza = brillo
            bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
            uvn = next(n for n in nt.nodes if n.type == 'UVMAP')
            tx = nt.nodes.new('ShaderNodeTexImage')
            tx.location = (-400, -300)
            tx.image = bpy.data.images.load(os.path.join(DIR_TEX, mapa + ".png"), check_existing=True)
            tx.interpolation = 'Closest'
            tx.extension = 'REPEAT'
            nt.links.new(uvn.outputs['UV'], tx.inputs['Vector'])
            nt.links.new(tx.outputs['Color'], bs.inputs['Emission Color'])
            bs.inputs['Emission Strength'].default_value = fuerza
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


def plano(sp, x_izq, z_arriba, y_pared, signo, espejo=False, escala=1.0, lado=PX, base=0.0):
    """Sprite plano sobre una pared vertical: sale hacia y = y_pared + signo * (base + h * escala).
    lado = tamano de un pixel en metros; con base > 0 el relieve es macizo (el fondo queda en la pared)."""
    def f(u, v, h):
        x = x_izq + (sp.w - u if espejo else u) * lado
        d = h if h <= 0 else base + h * escala
        return (x, y_pared + signo * d, z_arriba - v * lado)
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


# ------------------------------------------------------------------ portal en relieve
def inset(pol, b):
    """Poligono convexo (x, z) encogido b metros hacia adentro."""
    n = len(pol)
    area = sum(pol[i][0] * pol[(i + 1) % n][1] - pol[(i + 1) % n][0] * pol[i][1] for i in range(n))
    sg = 1 if area > 0 else -1
    lineas = []
    for i in range(n):
        (x0, z0), (x1, z1) = pol[i], pol[(i + 1) % n]
        dx, dz = x1 - x0, z1 - z0
        ln = math.hypot(dx, dz)
        nx, nz = -dz / ln * sg, dx / ln * sg                        # normal hacia adentro
        lineas.append(((x0 + nx * b, z0 + nz * b), (dx, dz)))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lineas[i - 1], lineas[i]
        den = d1[0] * d2[1] - d1[1] * d2[0]
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
        out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    return out


def prisma_redondo(bm, pol, s, d1, r, mat, n=3, d0=-0.01):
    """Bloque que sale de la cara del muro (s = -1 frente, +1 fondo) desde d0 hasta d1 metros, con el borde
    de adelante redondeado (radio r en n facetas planas): la luz lo pinta en franjas, como el sombreado de
    un sprite, y el contorno negro lo rodea entero. pol = poligono convexo (x, z)."""
    y = lambda d: s * (CARA + d)
    capas = [[bm.verts.new((x, y(d0), z)) for x, z in pol]]
    for k in range(n + 1):
        t = (math.pi / 2) * k / n
        b = r * (1 - math.cos(t))
        capas.append([bm.verts.new((x, y(d1 - r + r * math.sin(t)), z)) for x, z in (pol if k == 0 else inset(pol, b))])
    caras = [bm.faces.new(capas[0]), bm.faces.new(capas[-1])]
    m = len(pol)
    for c0, c1 in zip(capas, capas[1:]):
        for i in range(m):
            j = (i + 1) % m
            caras.append(bm.faces.new([c0[i], c0[j], c1[j], c1[i]]))
    for f in caras:
        f.material_index = mat
    bmesh.ops.recalc_face_normals(bm, faces=caras)
    return caras


def rect(x0, x1, z0, z1):
    return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]


def pua_eje(bm, x, z, s, d, ang, largo, ancho, mat, grueso=None):
    """Pua en el plano del muro: base en rombo en (x, z) a d metros del muro, perpendicular a su eje
    (ancho en el plano del muro, grueso hacia afuera; si grueso < ancho es una hoja plana con lomo).
    El eje forma 'ang' radianes con la vertical (positivo hacia +X)."""
    y = lambda dd: s * (CARA + dd)
    ax, az = math.sin(ang), math.cos(ang)
    m = ancho / 2
    g = m if grueso is None else grueso / 2
    base = [bm.verts.new(p) for p in ((x - az * m, y(d), z + ax * m), (x, y(d - g), z), (x + az * m, y(d), z - ax * m),
                                       (x, y(d + g), z))]
    punta = bm.verts.new((x + ax * largo, y(d), z + az * largo))
    caras = [bm.faces.new(base)] + [bm.faces.new([base[i], base[(i + 1) % 4], punta]) for i in range(4)]
    for f in caras:
        f.material_index = mat
    bmesh.ops.recalc_face_normals(bm, faces=caras)


# Portal comun de las puertas especiales (metros; x-z sobre la cara del muro, d = cuanto sale del muro).
# El borde de adentro queda en x = +-0.70: la hoja abierta (x -0.68 a -0.52 con sus herrajes) no lo toca.
# El dintel empieza en z = 2.34: la hoja (2.30 m y su contorno) pasa por debajo.
X_VANO = 0.70
Z_DINTEL = 2.34
PILASTRA = [(-X_VANO, 0.24), (-0.96, 0.24), (-1.04, 2.22), (-X_VANO, 2.22)]
MOLDURA = [(-0.765, 0.36), (-0.895, 0.36), (-0.965, 2.10), (-0.765, 2.10)]
BASA = [(rect(-1.04, -X_VANO, 0.0, 0.14), 0.22, 0.05), (rect(-1.00, -X_VANO, 0.12, 0.27), 0.19, 0.05)]
CAPITEL = [(rect(-1.07, -X_VANO, 2.19, 2.28), 0.19, 0.03), (rect(-1.13, -X_VANO, 2.26, Z_DINTEL + 0.02), 0.22, 0.04)]
DINTEL = (rect(-1.22, -0.56, Z_DINTEL, 2.62), 0.23, 0.08)        # dos bloques; el emblema va en el hueco
CORNISA = (rect(-1.30, -0.52, 2.58, 2.68), 0.27, 0.04)
FRISO = (rect(-0.64, 0.64, Z_DINTEL, 2.60), 0.12, 0.02)          # panel oscuro detras del emblema
TOPE = 2.68
X_ESQUINA = 1.13


def espejo_x(pol):
    return [(-x, z) for x, z in reversed(pol)]


def portal(bm, s, mat_pilastra, mat_metal, mat_friso, moldura=True):
    """Basas, pilastras (con moldura), capiteles, los dos bloques del dintel con su cornisa y el friso,
    en la cara s del muro."""
    for pol, d, r in BASA + CAPITEL + [DINTEL, CORNISA]:
        prisma_redondo(bm, pol, s, d, r, mat_metal)
        prisma_redondo(bm, espejo_x(pol), s, d, r, mat_metal)
    for pol in (PILASTRA, espejo_x(PILASTRA)):
        prisma_redondo(bm, pol, s, 0.15, 0.06, mat_pilastra)
    if moldura:
        for pol in (MOLDURA, espejo_x(MOLDURA)):
            prisma_redondo(bm, pol, s, 0.195, 0.04, mat_pilastra)
    pol, d, r = FRISO
    prisma_redondo(bm, pol, s, d, r, mat_friso)


def puntas_corona(sp):
    """Borde de arriba de la corona (v por cada u) y los cortes de las tiras verticales."""
    ancho = tex.CORONA_ANCHO

    def arriba(u):
        v = sp.banda
        for c, alto in tex.CORONA_PUNTAS:
            if abs(u - c) < ancho:
                v = min(v, sp.banda - alto * (1 - abs(u - c) / ancho))
        return v
    valles = []                          # donde se cruzan las faldas de dos puntas vecinas
    for (c1, a1), (c2, a2) in zip(tex.CORONA_PUNTAS, tex.CORONA_PUNTAS[1:]):
        u = (a2 * (1 - c2 / ancho) - a1 * (1 + c1 / ancho)) / (-a1 / ancho - a2 / ancho)
        valles.append(u if c2 - ancho < u < c1 + ancho else None)
    quiebres = {0.0, float(sp.w)} | {c for c, _ in tex.CORONA_PUNTAS} | {u for u in valles if u is not None}
    # tiras de 1 px para seguir la curva, pero ninguna a menos de 1.5 px de un valle: ahi el contorno
    # empuja los vertices de las dos faldas hacia el valle y, si estan muy juntos, se cruzan y asoma
    cortes = sorted(quiebres | {float(k) for k in range(sp.w + 1)
                                if all(u is None or abs(k - u) >= 1.5 for u in valles)})
    return arriba, cortes


# ------------------------------------------------------------------ adornos
def centro_pilastra(z, lado):
    """x del eje de la moldura a la altura z (lado -1 izquierda, +1 derecha)."""
    (xi, _), (xa, za), (xb, zb), _ = MOLDURA
    afuera = xa + (xb - xa) * (z - za) / (zb - za)
    return lado * -(xi + afuera) / 2


def adornos_tesoro(col, marco, hoja):
    # portal de oro: tachones en las molduras, una roseta en cada bloque del dintel y un orbe en cada esquina
    bm = bmesh.new()
    for s in (-1, 1):
        portal(bm, s, 0, 0, 1)
        for lado in (-1, 1):
            for z in (0.66, 1.23, 1.80):
                esfera(bm, (centro_pilastra(z, lado), s * (CARA + 0.195), z), 0.045, 0, seg=8)
            x = lado * 0.92                                                                # medallon: placa y boton
            prisma_redondo(bm, rect(x - 0.11, x + 0.11, 2.37, 2.59), s, 0.25, 0.02, 0, d0=0.15)
            esfera(bm, (x, s * (CARA + 0.25), 2.48), 0.075, 0, seg=12)
            xe = lado * X_ESQUINA                                                          # pedestal y orbe
            prisma_redondo(bm, rect(xe - 0.10, xe + 0.10, TOPE - 0.02, TOPE + 0.05), s, 0.22, 0.02, 0, d0=0.02)
            esfera(bm, (xe, s * (CARA + 0.12), TOPE + 0.05 + 0.092), 0.10, 0, seg=12)
    objeto("Puerta_Portal", bm, [material("M_Oro_Tesoro"), material("M_Friso_Tesoro")], col,
           uv={0: dict(tam=(16, 16)), 1: dict(tam=(16, 16), origen=(0.0, 0.0, Z_DINTEL))})
    # corona como clave del portal: delante del friso, entre los dos bloques del dintel
    sp = tex.corona()
    arriba, cortes = puntas_corona(sp)
    bm = bmesh.new()
    for s in (-1, 1):
        f = curvo(sp, 0.52, 0.36, s * CARA, s, Z_DINTEL)
        perfil_curvo(bm, sp, f, arriba, lambda u: sp.h, cortes, 0.07)
        for nombre, (c, fila) in sp.puntos.items():
            r = 0.072 if nombre == "punta_20" else 0.06
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
    # portal de sillares y metal oscuro, friso rojo detras de la calavera, zunchos y puas
    bm = bmesh.new()
    for s in (-1, 1):
        portal(bm, s, 0, 1, 2, moldura=False)
        for lado in (-1, 1):
            for z0 in (0.80, 1.58):                                                         # zunchos
                (xi, _), (xa, za), (xb, zb), _ = PILASTRA
                afuera = lambda z: xa + (xb - xa) * (z - za) / (zb - za)
                pol = [(xi, z0), (afuera(z0) - 0.025, z0), (afuera(z0 + 0.10) - 0.025, z0 + 0.10), (xi, z0 + 0.10)]
                prisma_redondo(bm, pol if lado < 0 else espejo_x(pol), s, 0.185, 0.03, 1)
    objeto("Puerta_Portal", bm, [material("M_Piedra_Jefe"), material("M_Metal_Jefe"), material("M_Friso_Jefe")], col,
           uv={0: dict(tam=(32, 32)), 1: dict(tam=(16, 16)), 2: dict(tam=(16, 16))})
    # puas: tres en abanico en cada esquina de la cornisa y una en la punta de adentro de cada bloque
    # (objeto aparte, con el contorno sin grosor parejo: si no, la punta negra se alarga y toca el techo)
    bm = bmesh.new()
    for s in (-1, 1):
        for lado in (-1, 1):
            xe = lado * X_ESQUINA
            pua_eje(bm, xe, TOPE - 0.02, s, 0.135, 0.0, 0.27, 0.21, 0)
            pua_eje(bm, xe + lado * 0.13, TOPE - 0.02, s, 0.135, lado * 0.62, 0.20, 0.16, 0)
            pua_eje(bm, xe - lado * 0.13, TOPE - 0.02, s, 0.135, -lado * 0.42, 0.17, 0.15, 0)
            pua_eje(bm, lado * 0.64, TOPE - 0.02, s, 0.135, -lado * 0.12, 0.19, 0.16, 0)
    objeto("Puerta_Puas", bm, [material("M_Metal_Jefe")], col, uv={0: dict(tam=(16, 16))}, parejo=False)
    # calavera maciza como clave del portal: sale del friso, entre los dos bloques del dintel
    sp = tex.calavera()
    lado_px = 0.92 * PX
    bm = bmesh.new()
    x_izq, z_arriba = -sp.w * lado_px / 2, Z_DINTEL + sp.h * lado_px
    relieve(bm, sp, plano(sp, x_izq, z_arriba, -CARA, -1, lado=lado_px, base=0.14))
    relieve(bm, sp, plano(sp, x_izq, z_arriba, CARA, 1, espejo=True, lado=lado_px, base=0.14))
    objeto("Puerta_Calavera", bm, [material("M_Calavera")], col, grosor=CONTORNO_GRUESO, parejo=False)


# ------------------------------------------------------------------ variantes
# Material de cada hueco, en orden. El ultimo hueco (M_Contorno) no se toca.
#   Puerta_Hoja: tablas, herrajes, argollas
VARIANTES = [
    dict(archivo="puerta_tesoro.blend", coleccion="Puerta_Tesoro", adornos=adornos_tesoro,
         huecos={"Puerta_Marco": ["M_Puerta_Marco_Tesoro"],
                 "Puerta_Hoja": ["M_Puerta_Hoja_Tesoro", "M_Oro_Tesoro", "M_Oro_Tesoro"]},
         descripcion="Puerta de la sala del tesoro. Misma hoja y nombres que Puerta, en oro: portal macizo con "
                     "pilastras, dintel, cornisa y un orbe en cada esquina (Puerta_Portal), corona como clave del "
                     "portal (Puerta_Corona) y llave en la hoja (Puerta_Llave, hija de Puerta_Hoja).",
         etiquetas=("puerta", "interactivo", "tesoro")),
    dict(archivo="puerta_jefe.blend", coleccion="Puerta_Jefe", adornos=adornos_jefe,
         huecos={"Puerta_Marco": ["M_Puerta_Marco_Jefe"],
                 "Puerta_Hoja": ["M_Puerta_Hoja_Jefe", "M_Metal_Jefe", "M_Metal_Jefe"]},
         descripcion="Puerta de la sala del jefe. Misma hoja y nombres que Puerta, en marrones y rojos oscuros: "
                     "portal macizo de sillares y metal con un friso rojo que brilla (Puerta_Portal), puas en las "
                     "esquinas (Puerta_Puas), hoja de planchas remachadas y calavera como clave del portal, con "
                     "brasas que brillan en las cuencas (Puerta_Calavera).",
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
