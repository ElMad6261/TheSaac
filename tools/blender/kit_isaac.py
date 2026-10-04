# -*- coding: utf-8 -*-
"""
kit_isaac.py - Generador del kit modular de TheSaac (Blender 5.1).
Estilo pixel art inspirado en The Binding of Isaac:
  * Texturas originales generadas por codigo, 32 px por metro, interpolacion Closest.
  * Contorno negro duro de 1 texel (1/32 m) con casco invertido (Solidify).
"""
import bpy, bmesh, os, math, random
import numpy as np
from mathutils import Euler, Matrix

PX = 32
CONTORNO = 1.0 / PX
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))   # raiz del repo TheSaac
DIR_TEX = os.path.join(RAIZ, "assets", "texturas")
DIR_BLEND = os.path.join(RAIZ, "assets", "blend")
LINEA = '#120c09'
ORIG = {}
MATS = {}

CATALOGOS = {
    "Muros":    "6a1f3c2e-4b5d-4e8f-9a01-2b3c4d5e6f01",
    "Pisos":    "6a1f3c2e-4b5d-4e8f-9a01-2b3c4d5e6f02",
    "Puertas":  "6a1f3c2e-4b5d-4e8f-9a01-2b3c4d5e6f03",
    "Detalles": "6a1f3c2e-4b5d-4e8f-9a01-2b3c4d5e6f04",
}

# ------------------------------------------------------------------ color / lienzo
def hx(c):
    if isinstance(c, np.ndarray):
        return c
    c = c.lstrip('#')
    return np.array([int(c[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)

def mezcla(a, b, t):
    return hx(a) * (1.0 - t) + hx(b) * t

class Lienzo:
    """Imagen pequena en memoria. Fila 0 = abajo, igual que el UV de Blender."""
    def __init__(self, w, h, base):
        self.w, self.h = w, h
        self.a = np.empty((h, w, 3), np.float32)
        self.a[:] = hx(base)
    def px(self, x, y, c):
        self.a[y % self.h, x % self.w] = hx(c)
    def get(self, x, y):
        return self.a[y % self.h, x % self.w].copy()
    def guardar(self, nombre):
        os.makedirs(DIR_TEX, exist_ok=True)
        ruta = os.path.join(DIR_TEX, nombre + ".png")
        img = bpy.data.images.new("_tmp_" + nombre, self.w, self.h, alpha=False)
        rgba = np.ones((self.h, self.w, 4), np.float32)
        rgba[..., :3] = self.a
        img.pixels.foreach_set(rgba.ravel())
        img.filepath_raw = ruta
        img.file_format = 'PNG'
        try:
            img.save(filepath=ruta)
        except TypeError:
            img.save()
        bpy.data.images.remove(img)
        return ruta

# ------------------------------------------------------------------ patrones
def bloque(l, x, y, w, h, base, pal, rnd):
    """Bloque de piedra: junta oscura abajo/izquierda, luz arriba/izquierda, sombra abajo/derecha."""
    lin = pal.get('linea', LINEA)
    base = hx(base)
    claro = mezcla(base, pal['luz'], 0.5)
    oscuro = mezcla(base, lin, 0.35)
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            l.px(xx, yy, base)
    for xx in range(x + 1, x + w):
        l.px(xx, y + h - 1, claro)
        l.px(xx, y + 1, oscuro)
    for yy in range(y + 1, y + h):
        l.px(x + 1, yy, claro)
        l.px(x + w - 1, yy, oscuro)
    for xx in range(x, x + w):
        l.px(xx, y, lin)
    for yy in range(y, y + h):
        l.px(x, yy, lin)
    mot = pal.get('mot', 0.07)
    for yy in range(y + 2, y + h - 1):
        for xx in range(x + 2, x + w - 1):
            r = rnd.random()
            if r < mot:
                l.px(xx, yy, oscuro)
            elif r < mot * 1.6:
                l.px(xx, yy, claro)
    if w >= 10 and h >= 8 and rnd.random() < pal.get('grietas', 0.3):
        cx = x + rnd.randrange(3, w - 3)
        cy = y + rnd.randrange(3, h - 2)
        for _ in range(rnd.randrange(3, 7)):
            if not (x + 2 <= cx < x + w - 1 and y + 2 <= cy < y + h - 1):
                break
            l.px(cx, cy, lin)
            l.px(cx + 1, cy, claro)
            cx += rnd.choice((-1, 0, 1))
            cy += rnd.choice((-1, -1, 0, 1))

def hileras(l, cursos, anchos, tonos, pal, rnd, desfase=True):
    """Hiladas de bloques que se repiten sin costura en horizontal."""
    y = 0
    for i, h in enumerate(cursos):
        an = anchos[i % len(anchos)] if isinstance(anchos[0], (tuple, list)) else anchos
        x = rnd.randrange(l.w) if desfase else 0
        resto = l.w
        while resto > 0:
            w = rnd.choice(an)
            if w > resto or resto - w < min(an):
                w = resto
            bloque(l, x, y, w, h, rnd.choice(tonos), pal, rnd)
            x += w
            resto -= w
        y += h

def tablones(l, x0, y0, w, h, ancho, vertical, tonos, pal, rnd, juntas=0):
    """Tablones de madera con veta, nudos y juntas negras."""
    lin = pal.get('linea', LINEA)
    total = w if vertical else h
    largo = h if vertical else w
    def P(a, b, c):
        if vertical:
            l.px(x0 + a, y0 + b, c)
        else:
            l.px(x0 + b, y0 + a, c)
    a0 = 0
    while a0 < total:
        aw = min(ancho, total - a0)
        base = hx(rnd.choice(tonos))
        claro = mezcla(base, pal['luz'], 0.45)
        oscuro = mezcla(base, lin, 0.35)
        veta = mezcla(base, lin, 0.55)
        luz_a, sombra_a = (1, aw - 1) if vertical else (aw - 1, 1)
        for a in range(aw):
            for b in range(largo):
                if a == 0:
                    c = lin
                elif a == luz_a:
                    c = claro
                elif a == sombra_a:
                    c = oscuro
                else:
                    c = base
                P(a0 + a, b, c)
        if aw > 3:
            for _ in range(max(1, aw // 4)):
                a = a0 + rnd.randrange(2, aw - 1)
                for b in range(largo):
                    if rnd.random() < 0.5:
                        P(a, b, veta)
            if rnd.random() < 0.6 and aw >= 5 and largo > 6:
                a = a0 + rnd.randrange(2, aw - 2)
                b = rnd.randrange(2, largo - 3)
                P(a, b, lin); P(a + 1, b, veta); P(a, b + 1, veta); P(a + 1, b + 1, claro)
        if juntas and largo > 10:
            for b in rnd.sample(range(3, largo - 3), juntas):
                for a in range(aw):
                    P(a0 + a, b, lin)
        a0 += ancho

def metal(nombre, base, claro, oscuro, brillo, semilla, tam=16, remaches=True):
    rnd = random.Random(semilla)
    l = Lienzo(tam, tam, base)
    for y in range(tam):
        for x in range(tam):
            r = rnd.random()
            if r < 0.12:
                l.px(x, y, oscuro)
            elif r < 0.20:
                l.px(x, y, claro)
    if remaches:
        for (x, y) in ((3, 12), (11, 4)):
            l.px(x, y, brillo); l.px(x + 1, y, claro); l.px(x, y - 1, claro); l.px(x + 1, y - 1, oscuro)
    return l.guardar(nombre)

def tex_marco():
    """64 x 80 px. Columnas 0-47: cara del marco (1.5 x 2.5 m). Columnas 48-63: caras interiores (0.5 m)."""
    rnd = random.Random(31)
    pal = dict(luz='#cdb9a0', mot=0.05, grietas=0.2)
    tonos = ['#8f7b67', '#86725f', '#998571']
    l = Lienzo(64, 80, '#8f7b67')
    for x0 in (0, 43):
        y = 0
        while y < 73:
            h = min(rnd.choice((10, 12, 14)), 73 - y)
            bloque(l, x0, y, 5, h, rnd.choice(tonos), pal, rnd)
            y += h
    x = 0
    for i, w in enumerate((8, 6, 6, 8, 6, 6, 8)):
        bloque(l, x, 73, w, 7, '#a5917c' if i == 3 else rnd.choice(tonos), pal, rnd)
        x += w
    y = 0
    while y < 80:
        h = min(rnd.choice((10, 12, 14)), 80 - y)
        bloque(l, 48, y, 16, h, rnd.choice(tonos), pal, rnd)
        y += h
    for y in range(80):
        for x in (0, 47, 48, 63):
            l.px(x, y, LINEA)
    for y in range(75):
        l.px(4, y, LINEA); l.px(43, y, LINEA)
    for x in range(48):
        l.px(x, 79, LINEA)
    for x in range(4, 44):
        l.px(x, 73, LINEA); l.px(x, 74, LINEA)
    return l.guardar('T_Puerta_Marco')

def tex_hoja():
    """48 x 80 px. Columnas 0-38: cara de la hoja (1.2 x 2.3 m). Columnas 40-47: cantos (10 cm)."""
    rnd = random.Random(32)
    l = Lienzo(48, 80, '#7a4a2a')
    tablones(l, 0, 0, 40, 74, 8, True, ['#7a4a2a', '#724527', '#81502e'], dict(luz='#a8703f'), rnd)
    tablones(l, 40, 0, 8, 80, 8, True, ['#5a3620'], dict(luz='#7a4a2a'), rnd)
    for y in range(80):
        for x in (0, 37, 38, 40, 43):
            l.px(x, y, LINEA)
    for x in range(40):
        l.px(x, 0, LINEA); l.px(x, 72, LINEA); l.px(x, 73, LINEA)
    return l.guardar('T_Puerta_Hoja')

def generar_texturas():
    T = {}
    rnd = random.Random(11)
    l = Lienzo(64, 96, '#6b5444')
    hileras(l, [16] * 6, (16, 24, 32), ['#6b5444', '#644e3f', '#735b4a', '#5e4a3c'],
            dict(luz='#b39678', mot=0.07, grietas=0.35), rnd)
    for y in range(1, 4):
        for x in range(64):
            if rnd.random() < (4 - y) / 4.5:
                l.px(x, y, mezcla(l.get(x, y), LINEA, 0.45))
    T['T_Muro_Piedra'] = l.guardar('T_Muro_Piedra')

    rnd = random.Random(12)
    l = Lienzo(32, 96, '#5b493d')
    hileras(l, [16] * 6, [(32,), (16,)], ['#5b493d', '#554437', '#614e41'],
            dict(luz='#a3876f', mot=0.06, grietas=0.3), rnd, desfase=False)
    T['T_Pilar_Piedra'] = l.guardar('T_Pilar_Piedra')

    rnd = random.Random(13)
    l = Lienzo(64, 64, '#7a5f45')
    hileras(l, [16] * 4, (16, 32), ['#7a5f45', '#72583f', '#82674c', '#6c533c'],
            dict(luz='#a88a6a', mot=0.08, grietas=0.4), rnd)
    lin_s = hx(LINEA).sum() + 0.15
    for _ in range(40):
        x, y = rnd.randrange(64), rnd.randrange(64)
        if l.get(x, y).sum() > lin_s:
            l.px(x, y, '#9a7e60' if rnd.random() < 0.5 else '#5a4532')
    T['T_Piso_Sotano'] = l.guardar('T_Piso_Sotano')

    rnd = random.Random(14)
    l = Lienzo(64, 64, '#3b2f28')
    tablones(l, 0, 0, 64, 64, 8, False, ['#3b2f28', '#362b24', '#41342c'], dict(luz='#5c4b3f'), rnd, juntas=1)
    T['T_Techo_Tablas'] = l.guardar('T_Techo_Tablas')

    rnd = random.Random(15)
    l = Lienzo(32, 32, '#7a4a2a')
    tablones(l, 0, 0, 32, 32, 8, True, ['#7a4a2a', '#724527', '#81502e'], dict(luz='#a8703f'), rnd)
    T['T_Madera'] = l.guardar('T_Madera')

    rnd = random.Random(16)
    l = Lienzo(32, 32, '#4e3220')
    tablones(l, 0, 0, 32, 32, 8, True, ['#4e3220', '#482e1d', '#553724'], dict(luz='#78523a'), rnd)
    T['T_Madera_Oscura'] = l.guardar('T_Madera_Oscura')

    T['T_Hierro'] = metal('T_Hierro', '#4a4a51', '#5f5f69', '#36363c', '#9a9aa8', 17)
    T['T_Laton'] = metal('T_Laton', '#b8862c', '#d6a645', '#7e5a1c', '#f2d27a', 18)
    T['T_Brea'] = metal('T_Brea', '#2b1d14', '#3c2a1d', '#1a110b', '#4a3626', 19, tam=8, remaches=False)
    T['T_Rojo'] = metal('T_Rojo', '#a8281e', '#c93a2e', '#6e1610', '#ec7a68', 20, tam=8, remaches=False)

    rnd = random.Random(21)
    grad = ['#fff3c4', '#ffd94a', '#ffae2a', '#ff8a1c', '#f05a16', '#c83214']
    l = Lienzo(8, 16, grad[-1])
    for y in range(16):
        for x in range(8):
            i = min(y, len(grad) - 1)
            j = min(i + 1, len(grad) - 1)
            l.px(x, y, grad[j] if rnd.random() < 0.25 else grad[i])
    T['T_Fuego'] = l.guardar('T_Fuego')

    rnd = random.Random(22)
    l = Lienzo(32, 32, '#77706a')
    celdas = [[rnd.random() for _ in range(8)] for _ in range(8)]
    tonos = ['#5d5650', '#6c655f', '#7b746d', '#8e867e']
    for y in range(32):
        for x in range(32):
            v = celdas[y // 4][x // 4] * 0.65 + rnd.random() * 0.35
            l.px(x, y, tonos[min(3, int(v * 4))])
    for _ in range(5):
        x, y = rnd.randrange(32), rnd.randrange(32)
        for _ in range(rnd.randrange(4, 9)):
            l.px(x, y, LINEA); l.px(x, y + 1, '#9c948b')
            x += rnd.choice((-1, 0, 1)); y += rnd.choice((-1, 0, 1))
    T['T_Roca'] = l.guardar('T_Roca')

    rnd = random.Random(23)
    l = Lienzo(32, 32, '#a39888')
    hileras(l, [8] * 4, (16,), ['#a39888', '#998e7f', '#ab9f8f'], dict(luz='#d2c6b2', mot=0.05, grietas=0.15), rnd)
    T['T_Piedra_Clara'] = l.guardar('T_Piedra_Clara')

    T['T_Puerta_Marco'] = tex_marco()
    T['T_Puerta_Hoja'] = tex_hoja()
    return T

# ------------------------------------------------------------------ materiales
def mat(nombre, tex=None, color=(0.5, 0.5, 0.5), rough=1.0, metal=0.0, emision=0.0, culling=False, especular=0.5):
    m = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (300, 0)
    bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); bs.location = (0, 0)
    nt.links.new(bs.outputs['BSDF'], out.inputs['Surface'])
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    bs.inputs['Specular IOR Level'].default_value = especular
    if tex:
        ruta = os.path.join(DIR_TEX, tex + ".png")
        img = bpy.data.images.load(ruta, check_existing=True)
        img.filepath = bpy.path.relpath(ruta)   # relativa al .blend; save_as la reubica
        uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.location = (-650, 0); uvn.uv_map = "UVMap"
        tx = nt.nodes.new('ShaderNodeTexImage'); tx.location = (-400, 0)
        tx.image = img
        tx.interpolation = 'Closest'
        tx.extension = 'REPEAT'
        nt.links.new(uvn.outputs['UV'], tx.inputs['Vector'])
        nt.links.new(tx.outputs['Color'], bs.inputs['Base Color'])
        if emision:
            nt.links.new(tx.outputs['Color'], bs.inputs['Emission Color'])
            bs.inputs['Emission Strength'].default_value = emision
        pix = np.empty(img.size[0] * img.size[1] * 4, np.float32)
        img.pixels.foreach_get(pix)
        p = pix.reshape(-1, 4)[:, :3].mean(axis=0)
        m.diffuse_color = (float(p[0]), float(p[1]), float(p[2]), 1.0)
    else:
        bs.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
        m.diffuse_color = (color[0], color[1], color[2], 1.0)
    m.use_backface_culling = culling
    m.use_backface_culling_shadow = culling
    return m

def mat_t(nombre, tex=None, **kw):
    if nombre not in MATS or MATS[nombre].name not in bpy.data.materials:
        MATS[nombre] = mat(nombre, tex, **kw)
    return MATS[nombre]

def mat_contorno():
    return mat_t("M_Contorno", None, color=(0.0, 0.0, 0.0), rough=1.0, culling=True, especular=0.0)

def contorno(ob, grosor=CONTORNO):
    """Casco invertido: copia 1 texel hacia afuera, normales invertidas, material negro con backface culling."""
    mc = mat_contorno()
    if not any(m == mc for m in ob.data.materials):
        ob.data.materials.append(mc)
    md = ob.modifiers.new("Contorno", 'SOLIDIFY')
    md.thickness = grosor
    md.offset = 1.0
    md.use_flip_normals = True
    md.use_rim = False
    md.use_even_offset = True
    md.use_quality_normals = True
    md.material_offset = len(ob.data.materials) - 1
    return md

# ------------------------------------------------------------------ geometria
def caja(bm, x0, x1, y0, y1, z0, z1, mat=0):
    v = [bm.verts.new(p) for p in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                    (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for idx in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        f = bm.faces.new([v[i] for i in idx])
        f.material_index = mat

def prisma_xz(bm, pts, y0, y1, mat=0):
    """Extruye un perfil (x, z) a lo largo de Y. Las tapas concavas se parten en caras convexas."""
    fr = [bm.verts.new((x, y0, z)) for x, z in pts]
    bk = [bm.verts.new((x, y1, z)) for x, z in pts]
    tapas = [bm.faces.new(fr), bm.faces.new(list(reversed(bk)))]
    caras = list(tapas)
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        caras.append(bm.faces.new([fr[i], fr[j], bk[j], bk[i]]))
    for f in caras:
        f.material_index = mat
    bm.normal_update()
    bmesh.ops.connect_verts_concave(bm, faces=tapas)

def prisma_partes(bm, partes, y0, y1, mat=0):
    """Extruye en Y un perfil (x, z) armado con piezas convexas que comparten vertices.
    Las caras de frente y fondo quedan como quads limpios; los cantos salen de las aristas de borde."""
    V = {}
    def vert(p, y):
        k = (round(p[0], 5), round(p[1], 5), y)
        if k not in V:
            V[k] = bm.verts.new((p[0], y, p[1]))
        return V[k]
    caras, usos = [], {}
    for parte in partes:
        caras.append(bm.faces.new([vert(p, y0) for p in parte]))
        caras.append(bm.faces.new([vert(p, y1) for p in reversed(parte)]))
        for i in range(len(parte)):
            a, b = parte[i], parte[(i + 1) % len(parte)]
            k = frozenset(((round(a[0], 5), round(a[1], 5)), (round(b[0], 5), round(b[1], 5))))
            usos.setdefault(k, []).append((a, b))
    for lista in usos.values():
        if len(lista) == 1:
            a, b = lista[0]
            caras.append(bm.faces.new([vert(a, y0), vert(b, y0), vert(b, y1), vert(a, y1)]))
    for f in caras:
        f.material_index = mat

def torre(bm, niveles, mat=0):
    """Solido de planta cuadrada por niveles (medio_x, medio_y, z), de abajo hacia arriba."""
    an = [[bm.verts.new(p) for p in ((-a, -b, z), (a, -b, z), (a, b, z), (-a, b, z))] for a, b, z in niveles]
    caras = [bm.faces.new(list(reversed(an[0]))), bm.faces.new(an[-1])]
    for r0, r1 in zip(an, an[1:]):
        for i in range(4):
            j = (i + 1) % 4
            caras.append(bm.faces.new([r0[i], r0[j], r1[j], r1[i]]))
    for f in caras:
        f.material_index = mat

def losa_hueco(bm, xs, ys, z0, z1, hueco=(1, 1), mat=0):
    """Losa con una celda vacia (tragaluz, marco de trampilla)."""
    V = {(i, j): bm.verts.new((x, y, z1)) for i, x in enumerate(xs) for j, y in enumerate(ys)}
    caras = []
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            if (i, j) != hueco:
                caras.append(bm.faces.new([V[i, j], V[i + 1, j], V[i + 1, j + 1], V[i, j + 1]]))
    r = bmesh.ops.extrude_face_region(bm, geom=caras, use_keep_orig=True)
    nv = [g for g in r['geom'] if isinstance(g, bmesh.types.BMVert)]
    nf = [g for g in r['geom'] if isinstance(g, bmesh.types.BMFace)]
    bmesh.ops.translate(bm, vec=(0, 0, z0 - z1), verts=nv)
    for f in caras + nf:
        f.material_index = mat

def aro(bm, centro, radio, g, seg=8, plano='XZ', mat=0):
    cx, cy, cz = centro
    an = []
    for i in range(seg):
        t = 2 * math.pi * i / seg
        ct, st = math.cos(t), math.sin(t)
        r_ = []
        for dr, dn in ((-g, -g), (g, -g), (g, g), (-g, g)):
            r = radio + dr
            p = (cx + r * ct, cy + dn, cz + r * st) if plano == 'XZ' else (cx + r * ct, cy + r * st, cz + dn)
            r_.append(bm.verts.new(p))
        an.append(r_)
    for i in range(seg):
        a, b = an[i], an[(i + 1) % seg]
        for k in range(4):
            k2 = (k + 1) % 4
            f = bm.faces.new([a[k], b[k], b[k2], a[k2]])
            f.material_index = mat

def llama(bm, mat=0):
    niveles = [(0.03, 0.03, 0.0), (0.05, 0.05, 0.04), (0.03, 0.03, 0.085)]
    an = [[bm.verts.new(p) for p in ((-a, -b, z), (a, -b, z), (a, b, z), (-a, b, z))] for a, b, z in niveles]
    punta = bm.verts.new((0.008, -0.004, 0.12))
    caras = [bm.faces.new(list(reversed(an[0])))]
    for r0, r1 in zip(an, an[1:]):
        for i in range(4):
            j = (i + 1) % 4
            caras.append(bm.faces.new([r0[i], r0[j], r1[j], r1[i]]))
    for i in range(4):
        caras.append(bm.faces.new([an[-1][i], an[-1][(i + 1) % 4], punta]))
    for f in caras:
        f.material_index = mat

def uv_caja(me, specs):
    """Proyeccion por caja a densidad fija (32 px/m). specs: {indice_material o None: dict(tam, origen, reglas)}."""
    uvl = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    me.uv_layers.active = uvl
    data = uvl.data
    for p in me.polygons:
        s = specs.get(p.material_index, specs.get(None))
        if s is None:
            continue
        w, h = s['tam']
        ox, oy, oz = s.get('origen', (0.0, 0.0, 0.0))
        reglas = s.get('reglas', {})
        n = p.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        eje = 'Z' if (az >= ax and az >= ay) else ('X' if ax >= ay else 'Y')
        r = reglas.get(eje, (0, 0))
        du, dv = r[0], r[1]
        swap = len(r) > 2 and r[2]
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if eje == 'Y':
                u, v = co.x - ox, co.z - oz
            elif eje == 'X':
                u, v = co.y - oy, co.z - oz
            else:
                u, v = (co.y - oy, co.x - ox) if swap else (co.x - ox, co.y - oy)
            data[li].uv = ((u * PX + du) / w, (v * PX + dv) / h)

def objeto(nombre, bm, mats, col, loc=(0, 0, 0), uv=None, con_contorno=True, padre=None, recalc=True):
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        f.smooth = False
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(nombre, me)
    col.objects.link(ob)
    if padre is not None:
        ob.parent = padre
    ob.location = loc
    if uv:
        uv_caja(me, uv)
    if con_contorno:
        contorno(ob)
    return ob

# ------------------------------------------------------------------ escena / archivos / assets
def coleccion(nombre):
    c = bpy.data.collections.new(nombre)
    bpy.context.scene.collection.children.link(c)
    return c

def limpiar():
    MATS.clear()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for _ in range(3):
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

def escribir_catalogos():
    ruta = os.path.join(DIR_BLEND, "blender_assets.cats.txt")
    if os.path.exists(ruta):
        return ruta
    lineas = ["# Catalogos del Asset Browser de TheSaac.", "# Formato: UUID:ruta/del/catalogo:nombre_simple", "", "VERSION 1", ""]
    for nombre, cid in CATALOGOS.items():
        lineas.append("%s:TheSaac/%s:TheSaac-%s" % (cid, nombre, nombre))
    with open(ruta, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write("\n".join(lineas) + "\n")
    return ruta

def marcar(id_, catalogo, descripcion, etiquetas=()):
    id_.asset_mark()
    ad = id_.asset_data
    ad.catalog_id = CATALOGOS[catalogo]
    ad.description = descripcion
    ad.author = "TheSaac"
    for t in etiquetas:
        ad.tags.new(t, skip_if_exists=True)
    try:
        id_.asset_generate_preview()
    except Exception:
        pass

def preparar():
    fp = bpy.context.preferences.filepaths
    if 'save_version' not in ORIG:
        ORIG['save_version'] = fp.save_version
    fp.save_version = 0          # sin .blend1 mientras se generan los archivos
    return escribir_catalogos()

def restaurar():
    if 'save_version' in ORIG:
        bpy.context.preferences.filepaths.save_version = ORIG['save_version']

def guardar(nombre_archivo):
    ruta = os.path.join(DIR_BLEND, nombre_archivo)
    bpy.ops.wm.save_as_mainfile(filepath=ruta, relative_remap=True)
    return ruta

def encuadrar(objs, rot=(68, 0, -35)):
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    for ob in objs:
        ob.select_set(True)
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                sp = area.spaces.active
                sp.shading.type = 'MATERIAL'
                r3d = sp.region_3d
                r3d.view_perspective = 'PERSP'
                r3d.view_rotation = Euler([math.radians(a) for a in rot]).to_quaternion()
                region = next(r for r in area.regions if r.type == 'WINDOW')
                with bpy.context.temp_override(window=win, area=area, region=region):
                    bpy.ops.view3d.view_selected()
                for ob in objs:
                    ob.select_set(False)
                return True
    return False

def informe(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    res = {}
    for ob in objs:
        ev = ob.evaluated_get(dg)
        m2 = ev.to_mesh()
        cnt = {}
        for p in m2.polygons:
            cnt[p.material_index] = cnt.get(p.material_index, 0) + 1
        mats_eval = [m.name if m else None for m in m2.materials]
        src = ob.data if len(ob.data.vertices) else m2
        xs = [v.co.x for v in src.vertices]; ys = [v.co.y for v in src.vertices]; zs = [v.co.z for v in src.vertices]
        bm = bmesh.new(); bm.from_mesh(src)
        nm = sum(1 for e in bm.edges if not e.is_manifold)
        bm.free()
        ev.to_mesh_clear()
        res[ob.name] = dict(
            loc=[round(c, 3) for c in ob.location],
            padre=ob.parent.name if ob.parent else None,
            tam=[round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3), round(max(zs) - min(zs), 3)] if xs else None,
            rango_z=[round(min(zs), 3), round(max(zs), 3)] if zs else None,
            caras=len(src.polygons), no_manifold=nm,
            caras_eval_por_mat={mats_eval[k] if k < len(mats_eval) else k: v for k, v in cnt.items()},
            asset=bool(ob.asset_data))
    return res
