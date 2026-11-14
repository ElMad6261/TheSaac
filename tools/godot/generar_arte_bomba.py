# -*- coding: utf-8 -*-
"""
generar_arte_bomba.py - Arte pixelado de la bomba que no sale de Blender: HUD y mancha de la explosion.

Escribe:
  assets/ui/corazon_lleno.png, corazon_medio.png, corazon_vacio.png   corazones de 9 x 8 px del HUD
  assets/ui/icono_bomba.png                                           icono de 13 x 16 px junto al contador de bombas
  assets/ui/fuente_hud.png                                            numeros gruesos de 6 x 9 px con contorno (celdas de 8 x 12)
                                                                      Godot la importa como fuente de imagen (fuente_hud.png.import)
  assets/texturas/T_Mancha_Explosion.png                              quemadura de 64 x 64 px (2 m a 32 px/m) con transparencia

Arte original, con la paleta del kit (tools/blender/kit_isaac.py). El modelo 3D de la bomba y sus texturas
(T_Bomba, T_Bomba_Calavera, T_Mecha) los genera tools/blender/kit_piezas.py (p_bomba).
No necesita Godot, Blender ni librerias. Uso, desde la raiz del repo:
    python tools/godot/generar_arte_bomba.py
"""
import math, os, random, struct, zlib

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DIR_UI = os.path.join(RAIZ, "assets", "ui")
DIR_TEX = os.path.join(RAIZ, "assets", "texturas")

LINEA = "#120c09"
BREA = "#2b1d14"
ROJO, ROJO_LUZ, ROJO_SOMBRA = "#c93a2e", "#ec7a68", "#8e1f18"
VACIO_CORAZON = "#3c2a1d"
# Bomba: la misma paleta del modelo 3D (tools/blender/kit_piezas.py): cuerpo casi negro y calavera de hueso.
BOMBA, BOMBA_LUZ, BOMBA_SOMBRA = "#34343d", "#6a6a78", "#25252c"
HUESO, HUECO = "#d9d2c0", "#1d1d23"
BOQUILLA = "#7c7c88"
MECHA, MECHA_RAYA = "#cfae75", "#5e4023"
LLAMA, LLAMA_BORDE = "#ffd94a", "#f05a16"
NUMERO, NUMERO_SOMBRA = "#fff3dc", "#cbb894"
VACIO = (0, 0, 0, 0)


def rgba(hexa, a=255):
    h = hexa.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def guardar_png(carpeta, nombre, pix):
    """pix: lista de filas (la primera es la de arriba), cada fila una lista de (r, g, b, a)."""
    alto, ancho = len(pix), len(pix[0])
    crudo = b"".join(b"\x00" + bytes(c for p in fila for c in p) for fila in pix)
    def bloque(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos) & 0xffffffff)
    png = b"\x89PNG\r\n\x1a\n" + bloque(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 6, 0, 0, 0))
    png += bloque(b"IDAT", zlib.compress(crudo, 9)) + bloque(b"IEND", b"")
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, "wb") as f:
        f.write(png)
    return ruta


def pintar(mapa, colores):
    """Convierte un dibujo de texto en pixeles: cada letra es un color de 'colores'; '.' es transparente."""
    return [[rgba(colores[c]) if c in colores else VACIO for c in fila] for fila in mapa]


# ------------------------------------------------------------------ corazones 9 x 8
# '#' linea, 'R' rojo, 'L' brillo, 'S' sombra, 'V' corazon vacio.
CORAZON = [
    ".##...##.",
    "#LR#.#RR#",
    "#RRR#RRR#",
    "#RRRRRRR#",
    ".#RRRRS#.",
    "..#RRS#..",
    "...#S#...",
    "....#....",
]

def corazon(tipo):
    colores = {"#": LINEA, "R": ROJO, "L": ROJO_LUZ, "S": ROJO_SOMBRA, "V": VACIO_CORAZON}
    mapa = []
    for fila in CORAZON:
        nueva = ""
        for x, c in enumerate(fila):
            lleno = tipo == "lleno" or (tipo == "medio" and x <= 4)   # el medio corazon es la mitad izquierda
            nueva += c if (c in "#." or lleno) else "V"
        mapa.append(nueva)
    return guardar_png(DIR_UI, "corazon_%s.png" % tipo, pintar(mapa, colores))


# ------------------------------------------------------------------ icono de la bomba 13 x 16
# 'G' cuerpo, 'L' brillo, 'S' sombra, 'H' hueso de la calavera, 'o' cuencas/nariz/dientes, 'B' boquilla,
# 'M' cuerda de la mecha, 'm' raya de la cuerda, 'F' centro de la llama, 'f' borde de la llama, '#' contorno.
ICONO_BOMBA = [
    "..f..........",
    ".fFf.........",
    "..Mm.........",
    "...mM........",
    "....Mm.......",
    "....BBBB.....",
    "..##BBBB##...",
    ".#LLGGGGGG#..",
    "#LGGHHHHHGS#.",
    "#GGHHHHHHHS#.",
    "#GGHooHooHS#.",
    "#GGHHHoHHHS#.",
    "#GSSHoHoHSS#.",
    ".#SSSSSSSS#..",
    "..########...",
    ".............",
]

def icono_bomba():
    colores = {"#": LINEA, "G": BOMBA, "L": BOMBA_LUZ, "S": BOMBA_SOMBRA, "H": HUESO, "o": HUECO, "B": BOQUILLA,
               "M": MECHA, "m": MECHA_RAYA, "F": LLAMA, "f": LLAMA_BORDE}
    assert all(len(fila) == 13 for fila in ICONO_BOMBA)
    return guardar_png(DIR_UI, "icono_bomba.png", pintar(ICONO_BOMBA, colores))


# ------------------------------------------------------------------ fuente del HUD: numeros 6 x 9
# Numeros gruesos (trazo de 2 px) para el contador: se leen bien chicos y sobre cualquier fondo, porque
# cada uno lleva su contorno negro de 1 px y una sombra de 1 px abajo, pintados en la imagen.
NUMEROS = {
    "0": [".####.", "######", "##..##", "##..##", "##..##", "##..##", "##..##", "######", ".####."],
    "1": ["..##..", ".###..", "####..", "..##..", "..##..", "..##..", "..##..", "######", "######"],
    "2": [".####.", "######", "##..##", "....##", "...##.", "..##..", ".##...", "######", "######"],
    "3": [".####.", "######", "##..##", "....##", "..###.", "....##", "##..##", "######", ".####."],
    "4": ["...##.", "..###.", ".####.", "##.##.", "##.##.", "######", "######", "...##.", "...##."],
    "5": ["######", "######", "##....", "#####.", "######", "....##", "##..##", "######", ".####."],
    "6": [".####.", "######", "##....", "#####.", "######", "##..##", "##..##", "######", ".####."],
    "7": ["######", "######", "....##", "...##.", "...##.", "..##..", "..##..", ".##...", ".##..."],
    "8": [".####.", "######", "##..##", "######", ".####.", "##..##", "##..##", "######", ".####."],
    "9": [".####.", "######", "##..##", "##..##", "######", ".#####", "....##", "######", ".####."],
}
HUD_CELDA_X, HUD_CELDA_Y = 8, 12      # 6 x 9 del numero + 1 px de contorno a cada lado + 1 px de sombra abajo

def fuente_hud():
    """Tira de 10 celdas (del 0 al 9). Los colores van pintados: en Godot el Label se deja en blanco."""
    img = [[VACIO] * (HUD_CELDA_X * 10) for _ in range(HUD_CELDA_Y)]
    for i in range(10):
        glifo = NUMEROS[str(i)]
        x0 = i * HUD_CELDA_X + 1                  # el numero empieza 1 px adentro de la celda (deja sitio al contorno)
        relleno = {(x, y) for y, fila in enumerate(glifo) for x, c in enumerate(fila) if c == "#"}
        # Contorno: todo pixel vacio que toca al numero (tambien en diagonal). La sombra: una fila mas abajo.
        for (x, y) in relleno:
            for dy in (-1, 0, 1, 2):
                for dx in (-1, 0, 1):
                    if (x + dx, y + dy) not in relleno:
                        img[y + dy + 1][x0 + x + dx] = rgba(LINEA)
        for (x, y) in relleno:
            img[y + 1][x0 + x] = rgba(NUMERO if y < 6 else NUMERO_SOMBRA)   # el tercio de abajo, mas oscuro
    return guardar_png(DIR_UI, "fuente_hud.png", img)


# ------------------------------------------------------------------ mancha de la explosion 64 x 64
def mancha():
    """Quemadura redonda de bordes rotos: centro casi negro, aro de hollin tramado y salpicaduras sueltas."""
    tam = 64
    rnd = random.Random(41)
    # Un valor al azar por cada angulo (24 gajos) hace el borde irregular, como un estallido.
    gajos = [rnd.uniform(0.78, 1.0) for _ in range(24)]
    img = [[VACIO] * tam for _ in range(tam)]
    centro = (tam - 1) / 2.0
    for y in range(tam):
        for x in range(tam):
            dx, dy = x - centro, y - centro
            ang = (math.atan2(dy, dx) + math.pi) / (2 * math.pi) * 24
            i = int(ang) % 24
            t = ang - int(ang)
            borde = gajos[i] * (1 - t) + gajos[(i + 1) % 24] * t          # radio del borde en ese angulo (0 a 1)
            d = math.hypot(dx, dy) / (tam / 2.0) / borde                    # 0 = centro, 1 = borde de la mancha
            # Tonos casi negros y bastante opacos: el piso del sotano ya es oscuro y una mancha suave no se notaba.
            if d < 0.5:
                img[y][x] = rgba(LINEA, 245)
            elif d < 0.72:
                img[y][x] = rgba(LINEA, 240) if rnd.random() < 0.55 else rgba(BREA, 225)
            elif d < 0.88:
                if (x + y) % 2 == 0 or rnd.random() < 0.3:                  # tramado de tablero: se deshace hacia afuera
                    img[y][x] = rgba(LINEA, 210)
            elif d < 1.0:
                if rnd.random() < 0.25:
                    img[y][x] = rgba(LINEA, 170)
    return guardar_png(DIR_TEX, "T_Mancha_Explosion.png", img)


if __name__ == "__main__":
    for tipo in ("lleno", "medio", "vacio"):
        print("Corazon:", corazon(tipo))
    print("Icono:", icono_bomba())
    print("Fuente del HUD:", fuente_hud())
    print("Mancha:", mancha())
