# -*- coding: utf-8 -*-
"""
texturas_v2.py - Texturas de muros, pilar, piso y puertas (normal, tesoro y jefe) de TheSaac,
y los sprites con relieve de la corona, la llave y la calavera.

Pixel art a 32 px por metro, dibujado por codigo y con diseno propio. Paletas:
  * Sotano: #694134 (piedra) y #3e261f (sombra).
  * Tesoro: #F8C83E #D99A18 #A96F0C #5A3508 #321D07 #1D160D (solo esos seis colores).
  * Jefe: #191912 #30221D #481F1F #54392F #60393A #641513 #795041 (solo esos siete colores).

    T_Muro_Piedra          64 x 96   muro de 2 x 3 m de piedra irregular; se repite en horizontal
    T_Pilar_Piedra         32 x 96   una cara de 1 x 3 m del pilar
    T_Piso_Sotano          64 x 64   losas biseladas como las piedras del muro; se repite en X y en Y
    T_Puerta_Marco[_X]     64 x 80   cols 0-47 = frente (jambas de 5 px, dintel de 6 px); cols 48-63 = cantos del vano
    T_Puerta_Hoja[_X]      48 x 80   cols 0-38 x filas 6-79 = cara de la hoja; cols 39-47 = cantos
    T_Oro_Tesoro           16 x 16   oro para el portal, los herrajes y los orbes de la puerta del tesoro
    T_Friso_Tesoro         16 x 16   acolchado oscuro detras de la corona
    T_Piedra_Jefe          32 x 32   sillares de las pilastras del jefe
    T_Metal_Jefe           16 x 16   plancha remachada: basas, capiteles, dintel, puas y herrajes del jefe
    T_Friso_Jefe           16 x 16   rojo acanalado detras de la calavera (tambien es su mapa de brillo)
    T_Calavera_Brillo      21 x 20   mapa de brillo de la calavera: negro salvo las brasas de las cuencas
    T_Corona, T_Llave, T_Calavera    sprites: variantes_puerta.py levanta su relieve con SPRITES[nombre]

Uso, desde la raiz del repositorio (Python 3 normal o el de Blender; no necesita librerias):
    python tools/blender/texturas_v2.py
"""
import os, math, random, struct, zlib

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DIR_TEX = os.path.join(RAIZ, "assets", "texturas")

# ------------------------------------------------------------------ paletas (de oscuro a claro)
K = '#120c09'                       # linea negra del kit (kit_isaac.LINEA)
PIEDRA = [K, '#22140f', '#2f1b15', '#3e261f', '#53322a', '#694134', '#7a4c3c', '#8e5a46', '#a56c54', '#bd8266']
MADERA = ['#150c08', '#28170f', '#3a2216', '#4d2e1d', '#5e3823', '#6e432a', '#825234', '#9a6540']
HIERRO = ['#0f0e11', '#1c1b20', '#2a282f', '#3a3740', '#4c4853', '#615c69', '#7f7987', '#a49eab']
TES = ['#1D160D', '#321D07', '#5A3508', '#A96F0C', '#D99A18', '#F8C83E']   # paleta del tesoro (del equipo)
# Paleta del jefe (del equipo): #191912 #30221D #481F1F #54392F #60393A #641513 #795041, ordenada en dos rampas
PIEDRA_J = ['#191912', '#30221D', '#54392F', '#60393A', '#795041']          # de casi negro a marron claro
ROJO_J = ['#191912', '#481F1F', '#641513']                                  # vino y rojo muy oscuro
RAMPAS = [PIEDRA, MADERA, HIERRO, TES, PIEDRA_J, ROJO_J]


def paso(c, n):
    """Mueve un color n pasos dentro de su rampa (negativo = mas oscuro)."""
    for r in RAMPAS:
        if c in r:
            return r[max(0, min(len(r) - 1, r.index(c) + n))]
    return c


def rgb(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


class Lienzo:
    """Imagen en memoria con (0, 0) arriba a la izquierda, como en un editor de pixel art."""

    def __init__(self, w, h, color, envolver_x=False):
        self.w, self.h, self.envolver_x = w, h, envolver_x
        self.p = [[color] * w for _ in range(h)]

    def set(self, x, y, c):
        if self.envolver_x:
            x %= self.w
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    def get(self, x, y):
        if self.envolver_x:
            x %= self.w
        return self.p[y][x] if (0 <= x < self.w and 0 <= y < self.h) else None

    def fila(self, y, c, x0=0, x1=None):
        for x in range(x0, (self.w - 1 if x1 is None else x1) + 1):
            self.set(x, y, c)

    def columna(self, x, c, y0=0, y1=None):
        for y in range(y0, (self.h - 1 if y1 is None else y1) + 1):
            self.set(x, y, c)

    def guardar(self, ruta):
        crudo = b''.join(b'\x00' + bytes(v for c in fila for v in rgb(c)) for fila in self.p)

        def trozo(tipo, datos):
            return (struct.pack('>I', len(datos)) + tipo + datos
                    + struct.pack('>I', zlib.crc32(tipo + datos) & 0xffffffff))

        with open(ruta, 'wb') as fh:
            fh.write(b'\x89PNG\r\n\x1a\n'
                     + trozo(b'IHDR', struct.pack('>IIBBBBB', self.w, self.h, 8, 2, 0, 0, 0))
                     + trozo(b'IDAT', zlib.compress(crudo, 9)) + trozo(b'IEND', b''))


# ------------------------------------------------------------------ piezas de dibujo
def bloque(l, x0, y0, w, h, rampa, base, rnd, motas=(0.07, 0.035), astilla=0.3, grieta=0.18, junta=K):
    """Placa rectangular con junta arriba y a la izquierda, bisel (luz arriba-izquierda), desconchones y grietas."""
    l.fila(y0, junta, x0, x0 + w - 1)
    for y in range(y0, y0 + h):
        l.set(x0, y, junta)
    c = rampa[base]
    for y in range(y0 + 1, y0 + h):
        for x in range(x0 + 1, x0 + w):
            r = rnd.random()
            l.set(x, y, paso(c, -1) if r < motas[0] else paso(c, 1) if r < motas[0] + motas[1] else c)
    for x in range(x0 + 1, x0 + w):
        l.set(x, y0 + 1, paso(c, 1))
        l.set(x, y0 + h - 1, paso(c, -1))
    for y in range(y0 + 1, y0 + h):
        l.set(x0 + 1, y, paso(c, 1))
        l.set(x0 + w - 1, y, paso(c, -1))
    l.set(x0 + 1, y0 + 1, paso(c, 2))
    l.set(x0 + w - 1, y0 + h - 1, paso(c, -2))
    if w >= 6 and h >= 6 and rnd.random() < astilla:            # desconchon en una esquina
        ex, ey, dx, dy = rnd.choice(((x0 + w - 1, y0 + 1, -1, 1), (x0 + 1, y0 + h - 1, 1, -1),
                                     (x0 + w - 1, y0 + h - 1, -1, -1)))
        l.set(ex, ey, junta)
        l.set(ex + dx, ey, paso(c, -2))
        l.set(ex, ey + dy, paso(c, -2))
    if w >= 14 and h >= 9 and rnd.random() < grieta:            # grieta corta en diagonal
        s = rnd.choice((-1, 1))
        x = x0 + (rnd.randrange(3, w // 2) if s > 0 else rnd.randrange(w // 2, w - 3))
        desde_arriba = rnd.random() < 0.5
        y, dy = (y0 + 2, 1) if desde_arriba else (y0 + h - 2, -1)
        for _ in range(rnd.randrange(3, 6)):
            if not (x0 + 2 <= x <= x0 + w - 3):
                break
            l.set(x, y, paso(c, -3))
            l.set(x + 1, y, paso(c, 1))
            if rnd.random() < 0.65:
                x += s
            y += dy


def oscurecer(l, y0, y1, prob, rnd, x0=0, x1=None, n=1, respetar=(K,)):
    x1 = l.w - 1 if x1 is None else x1
    for y in range(y0, y1 + 1):
        p = prob(y)
        for x in range(x0, x1 + 1):
            c = l.get(x, y)
            if c not in respetar and rnd.random() < p:
                l.set(x, y, paso(c, -n))


def mancha(l, cx, cy, r, rnd):
    """Mancha de humedad: oscurece un ovalo irregular."""
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r - 2, cx + r + 3):
            d = ((x - cx) ** 2 / 1.6 + (y - cy) ** 2) ** 0.5
            c = l.get(x, y)
            if c is not None and c != K and d < r - rnd.random() * 1.5:
                l.set(x, y, paso(c, -1))


def clavo(l, x, y, rampa=HIERRO):
    l.set(x, y, rampa[6]); l.set(x + 1, y + 1, rampa[1])


def tabla(l, x0, y0, w, h, rampa, base, rnd, nudos=1, rendija=None, claras=0.25):
    """Tabla vertical: rendija a la izquierda, luz y sombra en los cantos, veta (claras = parte de veta clara) y nudos."""
    c = rampa[base]
    for y in range(y0, y0 + h):
        l.set(x0, y, rampa[0] if rendija is None else rendija)
        for x in range(x0 + 1, x0 + w):
            l.set(x, y, c)
        l.set(x0 + 1, y, paso(c, 1))
        l.set(x0 + w - 1, y, paso(c, -1))
    for x in range(x0 + 2, x0 + w - 1):
        y = y0 + rnd.randrange(0, 6)
        while y < y0 + h:
            largo = rnd.randrange(3, 9)
            tono = paso(c, -1) if rnd.random() < 1 - claras else paso(c, 1)
            for k in range(largo):
                if y + k < y0 + h and rnd.random() < 0.85:
                    l.set(x, y + k, tono)
            y += largo + rnd.randrange(4, 12)
    for _ in range(nudos):
        if w < 6:
            break
        nx, ny = x0 + rnd.randrange(2, w - 3), y0 + rnd.randrange(6, h - 6)
        l.set(nx, ny, rampa[1]); l.set(nx + 1, ny, rampa[1])
        l.set(nx - 1, ny, paso(c, -1)); l.set(nx + 2, ny, paso(c, -1))
        l.set(nx, ny - 1, paso(c, -1)); l.set(nx + 1, ny - 1, paso(c, 1))
        l.set(nx, ny + 1, paso(c, 1)); l.set(nx + 1, ny + 1, paso(c, -1))


def travesano(l, a, b, grosor, rampa, base, rnd):
    """Tablon en diagonal (refuerzo en Z) con borde oscuro, luz en el canto de arriba y sombra abajo."""
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    largo2 = dx * dx + dy * dy
    nx, ny = -dy / largo2 ** 0.5, dx / largo2 ** 0.5
    if ny > 0:
        nx, ny = -nx, -ny                       # normal hacia arriba
    c, m = rampa[base], grosor / 2
    for y in range(min(ay, by) - grosor - 2, max(ay, by) + grosor + 3):
        for x in range(min(ax, bx) - grosor - 2, max(ax, bx) + grosor + 3):
            t = ((x - ax) * dx + (y - ay) * dy) / largo2
            if not 0 <= t <= 1:
                continue
            s = -((ax + t * dx - x) * nx + (ay + t * dy - y) * ny)
            if abs(s) <= m:
                tono = paso(c, 1) if s > m - 1 else paso(c, -1) if s < -m + 1 else c
                l.set(x, y, paso(tono, -1) if rnd.random() < 0.08 else tono)
            elif abs(s) <= m + 1:
                l.set(x, y, rampa[0])


# ------------------------------------------------------------------ piedra irregular (sotano)
def ruido(w, h, celda, rnd):
    """Ruido de valor suave con periodo w en x (para torcer las juntas)."""
    gw, gh = max(1, w // celda), h // celda + 2
    g = [[rnd.uniform(-1, 1) for _ in range(gw)] for _ in range(gh)]

    def f(x, y):
        fx, fy = x / celda, y / celda
        i, j = int(math.floor(fx)), int(math.floor(fy))
        tx, ty = fx - i, fy - j
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a, b = g[j % gh][i % gw], g[j % gh][(i + 1) % gw]
        c, d = g[(j + 1) % gh][i % gw], g[(j + 1) % gh][(i + 1) % gw]
        return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty
    return f


def piedras(l, rnd, radio, tonos, ey=1.3, pesos=4.5, x0=0, x1=None, y0=0, y1=None, envolver=True,
            rampa=PIEDRA, hueco=1.25, esquina=2.4, bisel=3.2, luz=(-0.55, -0.75, 0.6)):
    """Piedras irregulares (Voronoi con pesos, distancia mas larga en Y) con juntas oscuras y bisel.
    radio(y) = separacion minima entre centros; tonos = indices posibles de 'rampa' para cada piedra."""
    x1 = l.w - 1 if x1 is None else x1
    y1 = l.h - 1 if y1 is None else y1
    w, h = x1 - x0 + 1, y1 - y0 + 1
    pts = []
    for _ in range(6000):                                       # dardos: centros separados
        x, y = rnd.uniform(0, w), rnd.uniform(-3, h + 3)
        ok = True
        for (px, py) in pts:
            dx = abs(x - px)
            if envolver:
                dx = min(dx, w - dx)
            r = (radio(y) + radio(py)) * 0.5
            if dx * dx + ((y - py) * ey) ** 2 < r * r:
                ok = False
                break
        if ok:
            pts.append((x, y))
    peso = [rnd.uniform(0, pesos) for _ in pts]
    tono = [rnd.choice(tonos) for _ in pts]
    nx, ny = ruido(w, h + 8, 8, rnd), ruido(w, h + 8, 8, rnd)
    M = [[None] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            qx, qy = x + 0.5 + 1.5 * nx(x, y + 4), y + 0.5 + 1.2 * ny(x, y + 4)
            mejores = [(1e9, -1)] * 3
            for i, (px, py) in enumerate(pts):
                dx = abs(qx - px)
                if envolver:
                    dx = min(dx, w - dx)
                d = math.sqrt(dx * dx + ((qy - py) * ey) ** 2) - peso[i]
                if d < mejores[2][0]:
                    mejores = sorted(mejores[:2] + [(d, i)])
            M[y][x] = (mejores[0][1], mejores[0][0], mejores[1][0], mejores[2][0])
    alto = [[0.0] * w for _ in range(h)]                        # almohadilla: 0 en la junta, 1 adentro
    for y in range(h):
        for x in range(w):
            i, d1, d2, d3 = M[y][x]
            e = d2 - d1
            if e < hueco or d3 - d1 < esquina:
                alto[y][x] = -1.0
            else:
                t = min(1.0, (e - hueco) / bisel)
                alto[y][x] = 1 - (1 - t) ** 2
    n0 = math.sqrt(sum(c * c for c in luz))
    L = tuple(c / n0 for c in luz)

    def a(x, y):
        x = x % w if envolver else min(max(x, 0), w - 1)
        y = min(max(y, 0), h - 1)
        return max(0.0, alto[y][x])
    for y in range(h):
        for x in range(w):
            i, d1, d2, d3 = M[y][x]
            if alto[y][x] < 0:
                l.set(x0 + x, y0 + y, K if (d2 - d1 < hueco * 0.55 or d3 - d1 < esquina * 0.6) else rampa[1])
                continue
            gx, gy = (a(x + 1, y) - a(x - 1, y)) * 0.8, (a(x, y + 1) - a(x, y - 1)) * 0.8
            n = math.sqrt(gx * gx + gy * gy + 1.0)
            lam = (-gx * L[0] - gy * L[1] + L[2]) / n
            off = max(-2, min(2, int(round((lam - L[2]) / 0.16))))
            c = rampa[max(1, min(len(rampa) - 1, tono[i] + off))]
            r = rnd.random()
            if off == 0 and r < 0.06:
                c = paso(c, -1)
            elif off == 0 and r < 0.085:
                c = paso(c, 1)
            l.set(x0 + x, y0 + y, c)


def muro():
    """Muro de sotano: piedras irregulares, mas grandes abajo. Fila 0 = linea contra el techo."""
    rnd = random.Random(5)
    l = Lienzo(64, 96, PIEDRA[3], envolver_x=True)
    piedras(l, rnd, lambda y: 12 + 8 * (max(0.0, y) / 96) ** 1.4, (3, 4, 4, 5, 5, 5, 6), ey=1.35)
    oscurecer(l, 1, 3, lambda y: (0.95, 0.65, 0.3)[y - 1], rnd)            # sombra bajo el techo
    oscurecer(l, 72, 94, lambda y: ((y - 72) / 22) ** 1.3 * 0.7, rnd)    # tierra junto al piso
    for _ in range(3):
        mancha(l, rnd.randrange(64), rnd.randrange(20, 70), rnd.randrange(3, 6), rnd)
    l.fila(0, K)
    l.fila(95, K)
    return l


def pilar():
    """Pilar de la misma piedra, algo mas clara. Columna 0 = arista negra."""
    rnd = random.Random(19)
    l = Lienzo(32, 96, PIEDRA[3], envolver_x=True)
    piedras(l, rnd, lambda y: 11 + 5 * (max(0.0, y) / 96) ** 1.4, (4, 5, 5, 6, 6), ey=1.25, pesos=4.0)
    oscurecer(l, 1, 3, lambda y: (0.95, 0.65, 0.3)[y - 1], rnd)
    oscurecer(l, 72, 94, lambda y: ((y - 72) / 22) ** 1.3 * 0.6, rnd)
    l.columna(0, K)
    l.fila(0, K)
    l.fila(95, K)
    return l


def ruido2(w, h, celda, rnd):
    """Ruido de valor suave que se repite en X y en Y (texturas de piso y mosaicos)."""
    gw, gh = w // celda, h // celda
    g = [[rnd.uniform(-1, 1) for _ in range(gw)] for _ in range(gh)]

    def f(x, y):
        fx, fy = x / celda, y / celda
        i, j = int(math.floor(fx)), int(math.floor(fy))
        tx, ty = fx - i, fy - j
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a, b = g[j % gh][i % gw], g[j % gh][(i + 1) % gw]
        c, d = g[(j + 1) % gh][i % gw], g[(j + 1) % gh][(i + 1) % gw]
        return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty
    return f


def losas(l, rnd, rmin, tonos, rampa=PIEDRA, pesos=5.0, tierra=0.15, hueco=1.8, bisel=5.0, relieve=0.5,
          juntas=None, piedritas=18):
    """Losas irregulares que se repiten en X y en Y, con tierra en las juntas y algunas celdas de tierra.
    juntas = (oscura, media, clara, sombra) de la tierra; por defecto salen de 'rampa'.
    Devuelve la altura de cada pixel (-1 = tierra) para poder agregar detalles encima."""
    W, H = l.w, l.h
    pts = []
    for _ in range(6000):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        if all(min(abs(x - px), W - abs(x - px)) ** 2 + min(abs(y - py), H - abs(y - py)) ** 2 >= rmin ** 2
               for px, py in pts):
            pts.append((x, y))
    peso = [rnd.uniform(0, pesos) for _ in pts]
    es_tierra = [rnd.random() < tierra for _ in pts]
    tono = [rnd.choice(tonos) for _ in pts]
    nx, ny, nh = ruido2(W, H, 8, rnd), ruido2(W, H, 8, rnd), ruido2(W, H, 8, rnd)
    nt = ruido2(W, H, 4, rnd)
    M = [[None] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            qx, qy = x + 0.5 + 1.5 * nx(x, y), y + 0.5 + 1.5 * ny(x, y)
            mejores = [(1e9, -1)] * 3
            for i, (px, py) in enumerate(pts):
                dx, dy = min(abs(qx - px), W - abs(qx - px)), min(abs(qy - py), H - abs(qy - py))
                d = math.sqrt(dx * dx + dy * dy) - peso[i]
                if d < mejores[2][0]:
                    mejores = sorted(mejores[:2] + [(d, i)])
            M[y][x] = (mejores[0][1], mejores[1][0] - mejores[0][0], mejores[2][0] - mejores[0][0])
    alto = [[-1.0] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            i, e, e3 = M[y][x]
            g = hueco + 0.6 * nh(x, y)
            if not es_tierra[i] and e > g and e3 > g + 1.2:
                alto[y][x] = min(1.0, (e - g) / bisel)
    L = (-0.55, -0.75, 0.6)
    n0 = math.sqrt(sum(c * c for c in L))
    L = tuple(c / n0 for c in L)

    def a(x, y):
        return max(0.0, alto[y % H][x % W])
    for y in range(H):
        for x in range(W):
            i = M[y][x][0]
            if alto[y][x] < 0:                                  # tierra: junta o celda sin losa
                v = nt(x, y)
                J = juntas or (rampa[1], rampa[2], rampa[3], rampa[0])
                c = J[0] if v < -0.45 else J[2] if v > 0.5 and es_tierra[i] else J[1]
                r = rnd.random()
                if r < 0.06:
                    c = paso(c, 1)
                elif r < 0.09:
                    c = paso(c, -1)
                if alto[(y - 1) % H][x] >= 0 or alto[y][(x - 1) % W] >= 0:
                    c = J[3]                                    # sombra pegada a la losa
                l.p[y][x] = c
                continue
            gx, gy = (a(x + 1, y) - a(x - 1, y)) * relieve, (a(x, y + 1) - a(x, y - 1)) * relieve
            n = math.sqrt(gx * gx + gy * gy + 1)
            lam = (-gx * L[0] - gy * L[1] + L[2]) / n
            off = max(-2, min(2, int(round((lam - L[2]) / 0.16))))
            c = rampa[max(1, min(len(rampa) - 1, tono[i] + off))]
            r = rnd.random()
            if off == 0 and r < 0.07:
                c = paso(c, -1)
            elif off == 0 and r < 0.09:
                c = paso(c, 1)
            l.p[y][x] = c
    for _ in range(piedritas):                                  # piedritas en la tierra
        x, y = rnd.randrange(W), rnd.randrange(H)
        if all(alto[(y + dy) % H][(x + dx) % W] < 0 for dx, dy in ((0, 0), (0, 1), (1, 0), (1, 1))):
            l.p[y][x] = rampa[4]; l.p[y][(x + 1) % W] = rampa[3]
            l.p[(y + 1) % H][x] = rampa[3]; l.p[(y + 1) % H][(x + 1) % W] = rampa[0]
    for i, (px, py) in enumerate(pts):                          # grietas en algunas losas
        if es_tierra[i] or rnd.random() > 0.3:
            continue
        x, y = int(px) + rnd.randrange(-3, 4), int(py) + rnd.randrange(-3, 4)
        s = rnd.choice((-1, 1))
        for _ in range(rnd.randrange(3, 7)):
            if alto[y % H][x % W] < 0.5:
                break
            l.p[y % H][x % W] = rampa[max(1, tono[i] - 2)]
            if rnd.random() < 0.6:
                x += s
            y += 1
    return alto


def piso():
    """Piso del sotano: losas irregulares con el mismo bisel y contraste que las piedras del muro,
    un tono mas oscuras y mas grandes, con juntas de tierra. 64 x 64, se repite en X y en Y."""
    rnd = random.Random(11)
    l = Lienzo(64, 64, PIEDRA[2], envolver_x=True)
    losas(l, rnd, 18, (3, 4, 4, 5, 5), pesos=4.0, tierra=0.06, hueco=1.5, bisel=3.5, relieve=0.9)
    return l


def veta_roja(l, x, y, largo, rnd, x_min, x_max, respetar=()):
    """Veta roja que baja en diagonal: nucleo rojo muy oscuro con borde vino."""
    sg = rnd.choice((-1, 1))
    for _ in range(largo):
        if not x_min <= x <= x_max:
            break
        for dx in (-1, 1):
            if l.get(x + dx, y) not in (ROJO_J[2],) + tuple(respetar):
                l.set(x + dx, y, ROJO_J[1])
        if l.get(x, y) not in respetar:
            l.set(x, y, ROJO_J[2])
        if rnd.random() < 0.55:
            x += sg
        y += 1


def chorreon_rojo(l, x, y, largo, rnd):
    """Reguero rojo oscuro que baja desde (x, y) (oxido de la paleta del jefe)."""
    for k in range(largo):
        if rnd.random() < 0.85:
            l.set(x + (1 if k > 4 and rnd.random() < 0.3 else 0), y + k,
                  ROJO_J[2] if k < 2 else ROJO_J[1])


def remache_j(l, x, y):
    l.set(x, y, PIEDRA_J[4]); l.set(x + 1, y, PIEDRA_J[3]); l.set(x, y + 1, PIEDRA_J[3]); l.set(x + 1, y + 1, PIEDRA_J[0])


def piedra_jefe():
    """Mosaico de 32 x 32 (1 x 1 m) para las pilastras del jefe: hiladas de sillares oscuros (0.5 x 0.25 m),
    trabados, con vetas rojas. Se repite en X y en Y."""
    rnd = random.Random(34)
    N = PIEDRA_J[0]
    l = Lienzo(32, 32, PIEDRA_J[1], envolver_x=True)
    for j, y0 in enumerate(range(0, 32, 8)):
        for x0 in range(8 * (j % 2), 8 * (j % 2) + 32, 16):
            bloque(l, x0, y0, 16, 8, PIEDRA_J, rnd.choice((1, 1, 1, 2)), rnd, motas=(0.08, 0.04), astilla=0.6, grieta=0,
                   junta=N)
    for (x, y, largo) in ((5, 2, 5), (21, 10, 5), (12, 26, 4)):
        veta_roja(l, x, y, largo, rnd, 0, 31, respetar=(N,))
    return l


def metal_jefe():
    """Mosaico de 16 x 16 (0.5 x 0.5 m) para basas, capiteles, dintel, puas y herrajes del jefe:
    plancha oscura con dos remaches y oxido rojo."""
    rnd = random.Random(35)
    l = Lienzo(16, 16, PIEDRA_J[1])
    for y in range(16):
        for x in range(16):
            r = rnd.random()
            if r < 0.06:
                l.set(x, y, PIEDRA_J[0])
            elif r < 0.10:
                l.set(x, y, PIEDRA_J[2])
    l.fila(0, PIEDRA_J[2]); l.columna(0, PIEDRA_J[2])            # canto de la plancha
    l.fila(15, PIEDRA_J[0]); l.columna(15, PIEDRA_J[0])
    for (x, y) in ((4, 4), (11, 10)):                             # remaches con oxido que baja
        remache_j(l, x, y)
        for k in range(1, rnd.randrange(3, 5)):
            l.set(x + (1 if k > 2 else 0), y + 1 + k, ROJO_J[2] if k < 3 else ROJO_J[1])
    return l


def friso_jefe():
    """Friso de 16 x 16 (0.5 x 0.5 m) detras de la calavera: rojo acanalado (canal oscuro, cara roja, borde vino).
    Brilla un poco (variantes_puerta.py lo usa tambien como mapa de emision)."""
    rnd = random.Random(36)
    l = Lienzo(16, 16, ROJO_J[2])
    for x in range(16):
        c = (PIEDRA_J[0], ROJO_J[1], ROJO_J[2], ROJO_J[2])[x % 4]
        for y in range(16):
            l.set(x, y, c)
    for y in range(16):                                           # algun golpe oscuro en las caras
        for x in range(16):
            if x % 4 in (2, 3) and rnd.random() < 0.06:
                l.set(x, y, ROJO_J[1])
    return l


# ------------------------------------------------------------------ marcos (64 x 80)
CANTOS = (13, 11, 12, 13, 10, 11, 10)            # planchas de los cantos del vano en la puerta del jefe


def lineas_marco(l, color=K):
    l.fila(0, color, 0, 47)
    l.fila(6, color, 0, 47)
    for x in (0, 4, 43, 47, 48, 63):
        l.columna(x, color)
    l.fila(79, color, 0, 4)
    l.fila(79, color, 43, 47)


def marco_normal():
    """Marco de piedra labrada lisa (dintel de una pieza y jambas largas); cantos de piedra irregular."""
    rnd = random.Random(31)
    l = Lienzo(64, 80, PIEDRA[3])
    piedras(l, rnd, lambda y: 9.0, (3, 3, 4, 4, 5), ey=1.1, pesos=3.0, x0=48, x1=63, envolver=False)
    for x0 in (0, 43):                                           # jambas: luz, cara, sombra
        for y in range(7, 79):
            l.set(x0 + 1, y, PIEDRA[8]); l.set(x0 + 2, y, PIEDRA[7]); l.set(x0 + 3, y, PIEDRA[6])
    for x in range(1, 47):                                       # dintel
        l.set(x, 1, PIEDRA[8]); l.set(x, 2, PIEDRA[7]); l.set(x, 3, PIEDRA[7]); l.set(x, 4, PIEDRA[7])
        l.set(x, 5, PIEDRA[6])
    for x in range(1, 47):                                       # motas de la piedra labrada
        for y in range(1, 6):
            if rnd.random() < 0.08:
                l.set(x, y, paso(l.get(x, y), -1))
    for x0 in (0, 43):
        for y in range(7, 79):
            for x in range(x0 + 1, x0 + 4):
                if rnd.random() < 0.06:
                    l.set(x, y, paso(l.get(x, y), -1))
    for x0, juntas in ((0, (31, 56)), (43, (27, 52))):           # dos juntas por jamba, a distinta altura
        for y in juntas:
            l.fila(y, K, x0, x0 + 4)
            l.fila(y + 1, PIEDRA[8], x0 + 1, x0 + 3)
    for x in (5, 42):                                            # el dintel apoya sobre las jambas
        l.columna(x, K, 1, 5)
        l.set(x + 1, 2, PIEDRA[8])
    for (x, y) in ((17, 2), (18, 3), (19, 3), (30, 4), (31, 4)):  # grietas finas
        l.set(x, y, PIEDRA[5])
    lineas_marco(l)
    return l


def marco_tesoro():
    """Marco dorado: bisel de oro en el frente, molduras con perlas y cantos acanalados."""
    l = Lienzo(64, 80, TES[3])
    for x0 in (0, 43):                                           # jambas
        for y in range(7, 79):
            l.set(x0 + 1, y, TES[5]); l.set(x0 + 2, y, TES[4]); l.set(x0 + 3, y, TES[3])
        for y in range(10, 78, 6):                               # perlas
            l.set(x0 + 2, y, TES[5]); l.set(x0 + 2, y + 1, TES[3])
    for x in range(1, 47):                                       # dintel
        l.set(x, 1, TES[5]); l.set(x, 2, TES[4]); l.set(x, 3, TES[4]); l.set(x, 4, TES[4]); l.set(x, 5, TES[3])
    for x in range(4, 44, 6):                                    # rombos repujados en el dintel
        l.set(x, 2, TES[5]); l.set(x - 1, 3, TES[5]); l.set(x, 3, TES[4]); l.set(x + 1, 3, TES[3]); l.set(x, 4, TES[3])
    acanalado = (TES[4], TES[5], TES[4], TES[3], TES[2])         # cantos: 3 canales verticales
    for x in range(49, 63):
        c = acanalado[(x - 49) % 5]
        for y in range(80):
            l.set(x, y, c)
    for y in range(0, 80, 20):                                   # anillos que cortan los canales
        l.fila(y, TES[2], 49, 62)
        l.fila(y + 1, TES[5], 49, 62)
    lineas_marco(l, TES[0])
    return l


def marco_jefe():
    """Paleta del jefe: dintel de plancha remachada, jambas y cantos de sillares con vetas rojas."""
    rnd = random.Random(33)
    N = PIEDRA_J[0]
    l = Lienzo(64, 80, PIEDRA_J[2])
    bloque(l, 0, 0, 48, 6, PIEDRA_J, 1, rnd, motas=(0.10, 0.05), astilla=0, grieta=0, junta=N)
    for x in range(3, 46, 6):
        remache_j(l, x, 2)
    for x0, alturas in ((0, (10, 12, 9, 11, 10, 12, 9)), (43, (9, 12, 10, 11, 9, 12, 10))):
        y = 7
        for h in alturas:
            bloque(l, x0, y, 5, h, PIEDRA_J, rnd.choice((2, 3)), rnd, motas=(0.05, 0.02), astilla=0, grieta=0, junta=N)
            y += h
    y = 0
    for h in CANTOS:
        bloque(l, 48, y, 16, h, PIEDRA_J, rnd.choice((1, 2, 2)), rnd, motas=(0.08, 0.03), astilla=0.3, grieta=0.25, junta=N)
        y += h
    lineas_marco(l, N)
    for x in (1, 2, 3, 44, 45, 46):                              # oxido que baja del dintel
        chorreon_rojo(l, x, 7, rnd.randrange(2, 7), rnd)
    for y in range(9, 79, 10):                                   # pernos en las jambas
        l.set(2, y, PIEDRA_J[4]); l.set(45, y, PIEDRA_J[4])
    for (x, y, largo) in ((2, 30, 6), (45, 52, 7), (2, 63, 5), (45, 18, 5)):     # vetas rojas en las jambas
        veta_roja(l, x, y, largo, rnd, 1, 3, respetar=(N,)) if x < 10 else veta_roja(l, x, y, largo, rnd, 44, 46, respetar=(N,))
    for (x, y, largo) in ((53, 8, 7), (59, 31, 8), (55, 52, 6), (60, 66, 6)):    # y en los cantos
        veta_roja(l, x, y, largo, rnd, 50, 61, respetar=(N,))
    return l


# ------------------------------------------------------------------ hojas (48 x 80)
TABLAS = (0, 8, 15, 23, 30, 38)                  # rendijas entre las 5 tablas


def lineas_hoja(l, color):
    l.fila(6, color, 0, 38)
    l.fila(79, color, 0, 38)
    for x in (0, 38, 39):
        l.columna(x, color, 6, 79)


def hoja_normal():
    """Cinco tablas con refuerzo en Z y clavos."""
    rnd = random.Random(41)
    l = Lienzo(48, 80, MADERA[4])
    for k in range(5):
        tabla(l, TABLAS[k], 6, TABLAS[k + 1] - TABLAS[k], 74, MADERA, rnd.choice((4, 5, 5)), rnd)
    tabla(l, 0, 0, 39, 6, MADERA, 4, rnd, nudos=0)               # filas 0-5: fuera de la cara
    for x in range(39, 48):                                       # cantos
        for y in range(80):
            l.set(x, y, MADERA[2] if (x + y // 3) % 4 else MADERA[1])
    travesano(l, (3, 62), (35, 25), 5, MADERA, 6, rnd)            # refuerzo en Z entre los herrajes
    for t in (0.06, 0.5, 0.94):
        clavo(l, round(3 + t * 32), round(62 - t * 37))
    for x in (4, 11, 19, 26, 34):
        clavo(l, x, 10)
        clavo(l, x, 74)
    lineas_hoja(l, MADERA[0])
    return l


def hoja_tesoro():
    """Tablas en los marrones de la paleta del tesoro, con tachuelas de oro arriba y abajo."""
    rnd = random.Random(42)
    rampa = TES[:4]                                               # sombra, muy oscuro, oscuro, ocre
    l = Lienzo(48, 80, TES[2])
    for k in range(5):
        tabla(l, TABLAS[k], 6, TABLAS[k + 1] - TABLAS[k], 74, rampa, 2, rnd, rendija=TES[0], claras=0.06)
    for x in range(39):
        for y in range(6):
            l.set(x, y, TES[1])
    for x in range(39, 48):
        for y in range(80):
            l.set(x, y, TES[2] if (x + y // 3) % 4 else TES[1])
    for k in range(5):                                            # tachuelas
        cx = (TABLAS[k] + TABLAS[k + 1]) // 2
        for y in (10, 74):
            l.set(cx, y, TES[5]); l.set(cx + 1, y, TES[4]); l.set(cx, y + 1, TES[4]); l.set(cx + 1, y + 1, TES[3])
    lineas_hoja(l, TES[0])
    return l


def hoja_jefe():
    """Paleta del jefe: seis planchas remachadas con oxido rojo y una mirilla con barrotes y resplandor rojo."""
    rnd = random.Random(43)
    N = PIEDRA_J[0]
    l = Lienzo(48, 80, PIEDRA_J[1])
    cortes_x, cortes_y = (0, 19, 38), (6, 30, 54, 79)
    for i in range(2):
        for j in range(3):
            x0, x1, y0, y1 = cortes_x[i], cortes_x[i + 1], cortes_y[j], cortes_y[j + 1]
            base = rnd.choice((1, 1, 2))
            bloque(l, x0, y0, x1 - x0 + 1, y1 - y0 + 1, PIEDRA_J, base, rnd, motas=(0, 0), astilla=0, grieta=0, junta=N)
            for x in range(x0 + 2, x1 - 1):                      # cepillado vertical (solo en las planchas claras)
                if base == 2 and rnd.random() < 0.3:
                    ya = rnd.randrange(y0 + 2, y1 - 2)
                    for y in range(ya, min(y1 - 1, ya + rnd.randrange(3, 10))):
                        l.set(x, y, paso(l.get(x, y), -1))
            puntos = ([(x, y0 + 2) for x in range(x0 + 2, x1 - 2, 5)] + [(x, y1 - 3) for x in range(x0 + 2, x1 - 2, 5)]
                      + [(x0 + 2, y) for y in range(y0 + 7, y1 - 4, 6)] + [(x1 - 3, y) for y in range(y0 + 7, y1 - 4, 6)])
            for (x, y) in puntos:
                remache_j(l, x, y)
                if rnd.random() < 0.35:
                    chorreon_rojo(l, x, y + 2, rnd.randrange(2, 6), rnd)
    for y in range(23, 29):                                      # mirilla: oscura, con resplandor rojo abajo
        for x in range(12, 27):
            l.set(x, y, ROJO_J[2] if y == 28 else ROJO_J[1] if y == 27 else N)
    l.fila(22, N, 11, 27)
    l.fila(29, PIEDRA_J[3], 11, 27)
    l.columna(11, N, 22, 29)
    l.columna(27, PIEDRA_J[3], 22, 29)
    for x in (14, 18, 22, 25):                                   # barrotes
        l.columna(x, PIEDRA_J[2], 23, 28)
        l.set(x, 23, PIEDRA_J[4])
    for x in range(39):
        for y in range(6):
            l.set(x, y, PIEDRA_J[1])
    for x in range(39, 48):
        for y in range(80):
            l.set(x, y, PIEDRA_J[1] if (y // 4) % 2 else N)
    lineas_hoja(l, N)
    return l


def friso_tesoro():
    """Friso de 16 x 16 (0.5 x 0.5 m) detras de la corona: acolchado oscuro en rombos con tachuelas de oro."""
    l = Lienzo(16, 16, TES[1])
    for y in range(16):
        for x in range(16):
            if (x + y) % 8 == 0:
                l.set(x, y, TES[0])                               # pliegue en sombra
            elif (x - y) % 8 == 1:
                l.set(x, y, TES[2])                               # pliegue con luz
    for (x, y) in ((0, 0), (8, 0), (4, 4), (12, 4), (0, 8), (8, 8), (4, 12), (12, 12)):
        l.set(x, y, TES[4])                                       # tachuelas en los cruces
    return l


def oro_tesoro():
    """Oro pulido para el portal, los herrajes y los orbes: 16 x 16, se repite. Casi liso: el brillo
    lo ponen los chaflanes del modelo; aqui solo hay algun destello y alguna marca."""
    rnd = random.Random(44)
    l = Lienzo(16, 16, TES[4])
    for y in range(16):
        for x in range(16):
            r = rnd.random()
            if r < 0.03:
                l.set(x, y, TES[3])
            elif r < 0.045:
                l.set(x, y, TES[5])
    return l


# ------------------------------------------------------------------ sprites con relieve
class Sprite:
    """Dibujo en pixeles + que pixeles son solidos + altura de cada pixel (m, hacia afuera).
    variantes_puerta.py construye la malla: frente con estas alturas, fondo plano y cantos."""

    def __init__(self, w, h, fondo):
        self.w, self.h = w, h
        self.lienzo = Lienzo(w, h, fondo)
        self.solido = [[False] * w for _ in range(h)]
        self.alto = [[0.0] * w for _ in range(h)]
        self.puntos = {}                                          # posiciones utiles (pixeles)


def dist_borde(sol, w, h):
    """Distancia (pixeles) de cada pixel solido al vacio mas cercano (chaflan 1 / 1.414, dos pasadas)."""
    d = [[1e9 if sol[y][x] else 0.0 for x in range(w)] for y in range(h)]

    def g(x, y):
        return d[y][x] if 0 <= x < w and 0 <= y < h else 0.0
    for y in range(h):
        for x in range(w):
            if sol[y][x]:
                d[y][x] = min(d[y][x], g(x - 1, y) + 1, g(x, y - 1) + 1, g(x - 1, y - 1) + 1.414, g(x + 1, y - 1) + 1.414)
    for y in range(h - 1, -1, -1):
        for x in range(w - 1, -1, -1):
            if sol[y][x]:
                d[y][x] = min(d[y][x], g(x + 1, y) + 1, g(x, y + 1) + 1, g(x + 1, y + 1) + 1.414, g(x - 1, y + 1) + 1.414)
    return d


def sombrear(sp, rampa, base, fuerza=0.45, escalon=0.2, luz=(-0.5, -0.7, 0.55)):
    """Pinta los pixeles solidos segun la normal del relieve (luz arriba-izquierda)."""
    n0 = math.sqrt(sum(c * c for c in luz))
    L = tuple(c / n0 for c in luz)

    def a(x, y):
        return sp.alto[y][x] if 0 <= x < sp.w and 0 <= y < sp.h and sp.solido[y][x] else 0.0
    for y in range(sp.h):
        for x in range(sp.w):
            if sp.solido[y][x]:
                gx = (a(x + 1, y) - a(x - 1, y)) * 16 * fuerza
                gy = (a(x, y + 1) - a(x, y - 1)) * 16 * fuerza
                n = math.sqrt(gx * gx + gy * gy + 1.0)
                lam = (-gx * L[0] - gy * L[1] + L[2]) / n
                off = int(round((lam - L[2]) / escalon))
                sp.lienzo.set(x, y, rampa[max(1, min(len(rampa) - 1, base + off))])


def sangrar(sp, filas):
    """Copia el color de los pixeles solidos a sus vecinos vacios (en 'filas'): asi el modelo puede tener
    lados rectos que cortan pixeles del borde sin que asome el fondo."""
    l = sp.lienzo
    nuevos = {}
    for y in filas:
        for x in range(sp.w):
            if not sp.solido[y][x]:
                for dx, dy in ((-1, 0), (1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < sp.w and 0 <= yy < sp.h and sp.solido[yy][xx]:
                        nuevos[x, y] = l.get(xx, yy)
                        break
    for (x, y), c in nuevos.items():
        l.set(x, y, c)


def calavera():
    """Calavera de 21 x 20 px (0.66 x 0.62 m) en la paleta del jefe: craneo abombado, cuencas hondas con
    una brasa roja (T_Calavera_Brillo la hace brillar), nariz y dientes."""
    W, H, cx = 21, 20, 10.5
    N = PIEDRA_J[0]
    sp = Sprite(W, H, N)
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5, y + 0.5
            craneo = ((px - cx) / 10.3) ** 2 + ((py - 9.0) / 9.0) ** 2 <= 1.0
            pomulos = 3.2 <= px <= 17.8 and 9.0 <= py <= 14.4
            cara = 4.6 <= px <= 16.4 and 13.0 <= py <= 15.8
            mandibula = 5.4 <= px <= 15.6 and 15.0 <= py <= 19.8 and not (py > 18.8 and (px < 6.4 or px > 14.6))
            sp.solido[y][x] = craneo or pomulos or cara or mandibula
    db = dist_borde(sp.solido, W, H)
    for y in range(H):
        for x in range(W):
            if sp.solido[y][x]:
                t = min(1.0, db[y][x] / 6.5)
                sp.alto[y][x] = 0.05 + 0.21 * math.sqrt(1 - (1 - t) ** 2)
    rasgo = {}
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5, y + 0.5
            for ox in (6.5, 14.5):
                if (abs(px - ox) / 2.9) ** 2.6 + (abs(py - 9.9) / 3.0) ** 2.6 <= 1.0:
                    rasgo[(x, y)] = 'cuenca'
            if 12.4 <= py <= 15.0 and abs(px - cx) <= (15.3 - py) * 0.6 + 0.2:
                rasgo[(x, y)] = 'nariz'
            if 6.0 <= px <= 15.0 and 15.0 < py <= 17.0:
                rasgo[(x, y)] = 'diente_a' if (x - 10) % 2 == 0 else 'entre'
            if 6.0 <= px <= 15.0 and 17.0 < py <= 18.0:
                rasgo[(x, y)] = 'boca'
            if 7.0 <= px <= 14.0 and 18.0 < py <= 19.0:
                rasgo[(x, y)] = 'diente_b' if (x - 10) % 2 == 0 else 'entre'
    for (x, y), r in rasgo.items():                               # cuencas, nariz y boca hundidas
        if sp.solido[y][x]:
            sp.alto[y][x] -= {'cuenca': 0.10, 'nariz': 0.07, 'entre': 0.025, 'boca': 0.04}.get(r, 0.0)
    sombrear(sp, PIEDRA_J, 4)                                     # hueso viejo: marron claro con sombras rojizas
    l = sp.lienzo
    for y in range(H):                                            # canto de abajo y de la derecha en sombra
        for x in range(W):
            if sp.solido[y][x] and (x + 1 >= W or not sp.solido[y][x + 1] or y + 1 >= H or not sp.solido[y + 1][x]):
                l.set(x, y, paso(l.get(x, y), -1))
    for (x, y), r in rasgo.items():
        if sp.solido[y][x]:
            l.set(x, y, {'cuenca': N, 'nariz': N, 'boca': N, 'entre': PIEDRA_J[1],
                         'diente_a': PIEDRA_J[4], 'diente_b': PIEDRA_J[3]}[r])
    for (x, y), r in list(rasgo.items()):                         # sombra bajo cuencas y nariz
        if r in ('cuenca', 'nariz'):
            for dx, dy in ((1, 0), (0, 1), (1, 1)):
                q = (x + dx, y + dy)
                if q not in rasgo and 0 <= q[0] < W and 0 <= q[1] < H and sp.solido[q[1]][q[0]]:
                    l.set(q[0], q[1], PIEDRA_J[2])
    sp.brasas = []
    for ox in (6, 14):                                            # brasa roja al fondo de cada cuenca
        for (x, y, c) in ((ox, 10, ROJO_J[2]), (ox, 11, ROJO_J[2]), (ox - 1, 10, ROJO_J[1]), (ox + 1, 10, ROJO_J[1]),
                          (ox - 1, 11, ROJO_J[1]), (ox + 1, 11, ROJO_J[1])):
            l.set(x, y, c)
            sp.brasas.append((x, y))
    for (x, y) in ((14, 1), (14, 2), (15, 3), (15, 4)):           # grieta
        l.set(x, y, PIEDRA_J[2])
    return sp


def calavera_brillo():
    """Mapa de emision de la calavera (mismo tamano): negro salvo las brasas de las cuencas."""
    sp = calavera()
    l = Lienzo(sp.w, sp.h, '#000000')
    for (x, y) in sp.brasas:
        l.set(x, y, sp.lienzo.get(x, y))
    return l


CORONA_PUNTAS = ((4.5, 7), (12.5, 8), (20.5, 10), (28.5, 8), (36.5, 7))   # (centro en px, alto sobre la banda)
CORONA_ANCHO = 4.4                                                         # media base de cada punta (px)


def corona():
    """Corona desenrollada de 41 x 16 px: banda de 6 px con gemas y cinco puntas (la del centro mas alta).
    variantes_puerta.py la curva en media elipse delante de la cornisa y pone un orbe en cada punta."""
    W, H, banda = 41, 16, 10
    sp = Sprite(W, H, TES[0])
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5, y + 0.5
            if y >= banda:
                sp.solido[y][x], sp.alto[y][x] = True, 0.07
                continue
            for c, alto in CORONA_PUNTAS:
                if py >= banda - alto and abs(px - c) <= CORONA_ANCHO * (py - (banda - alto)) / alto + 0.4:
                    sp.solido[y][x], sp.alto[y][x] = True, 0.07
    l = sp.lienzo
    for x in range(W):                                            # banda: canto de luz arriba, sombra abajo
        for y, k in ((10, 5), (11, 4), (12, 4), (13, 4), (14, 3), (15, 2)):
            l.set(x, y, TES[k])
        if all(abs(x + 0.5 - c) > 2.0 for c, _ in CORONA_PUNTAS) and x % 2 == 1:
            l.set(x, 12, TES[5])                                  # perlas entre gemas
            l.set(x, 13, TES[3])
    for c, alto in CORONA_PUNTAS:                                 # gemas talladas bajo cada punta
        gx = int(c)
        for dx, dy, k in ((-1, 11, 5), (0, 11, 1), (1, 11, 2), (-1, 12, 2), (0, 12, 1), (1, 12, 2),
                          (-1, 13, 2), (0, 13, 1), (1, 13, 0)):
            l.set(gx + dx, dy, TES[k])
    for y in range(banda):                                        # puntas: mitad iluminada, mitad en sombra
        for x in range(W):
            if sp.solido[y][x]:
                c = min(CORONA_PUNTAS, key=lambda p: abs(x + 0.5 - p[0]))[0]
                dx = x + 0.5 - c
                l.set(x, y, TES[5] if dx < -0.6 else TES[3] if dx > 0.6 else TES[4])
    sangrar(sp, range(banda))
    for c, alto in CORONA_PUNTAS:
        sp.puntos["punta_%d" % int(c)] = (c, banda - alto)        # donde va cada orbe
    sp.banda = banda
    return sp


LLAVE = ("..#####..",
         ".#######.",
         "###...###",
         "##.....##",
         "##.....##",
         "###...###",
         ".#######.",
         "...###...",
         "...###...",
         "...###...",
         "...#####.",
         "...#####.",
         "...###...",
         "...#####.",
         "...#####.")


def llave():
    """Llave de 9 x 15 px (0.28 x 0.47 m) en oro, para la hoja de la puerta del tesoro."""
    W, H = len(LLAVE[0]), len(LLAVE)
    sp = Sprite(W, H, TES[0])
    for y, fila in enumerate(LLAVE):
        for x, ch in enumerate(fila):
            if ch == '#':
                sp.solido[y][x], sp.alto[y][x] = True, 0.03
    for y in range(H):
        for x in range(W):
            if sp.solido[y][x]:
                s = lambda xx, yy: 0 <= xx < W and 0 <= yy < H and sp.solido[yy][xx]
                c = TES[4]
                if not s(x, y - 1) or not s(x - 1, y):
                    c = TES[5]
                if not s(x, y + 1) or not s(x + 1, y):
                    c = TES[3]
                sp.lienzo.set(x, y, c)
    return sp


# ------------------------------------------------------------------ salida
SPRITES = {"T_Calavera": calavera, "T_Corona": corona, "T_Llave": llave}
TEXTURAS = {
    "T_Muro_Piedra": muro,
    "T_Pilar_Piedra": pilar,
    "T_Piso_Sotano": piso,
    "T_Puerta_Marco": marco_normal,
    "T_Puerta_Hoja": hoja_normal,
    "T_Puerta_Marco_Tesoro": marco_tesoro,
    "T_Puerta_Hoja_Tesoro": hoja_tesoro,
    "T_Oro_Tesoro": oro_tesoro,
    "T_Friso_Tesoro": friso_tesoro,
    "T_Puerta_Marco_Jefe": marco_jefe,
    "T_Puerta_Hoja_Jefe": hoja_jefe,
    "T_Piedra_Jefe": piedra_jefe,
    "T_Metal_Jefe": metal_jefe,
    "T_Friso_Jefe": friso_jefe,
    "T_Calavera_Brillo": calavera_brillo,
}


def generar(carpeta=DIR_TEX):
    """Escribe las texturas y los sprites en 'carpeta' y devuelve sus rutas."""
    os.makedirs(carpeta, exist_ok=True)
    rutas = []
    for nombre, fn in list(TEXTURAS.items()) + list(SPRITES.items()):
        img = fn()
        ruta = os.path.join(carpeta, nombre + ".png")
        (img.lienzo if isinstance(img, Sprite) else img).guardar(ruta)
        rutas.append(ruta)
    return rutas


if __name__ == "__main__":
    for r in generar():
        print("Escrita", r)
