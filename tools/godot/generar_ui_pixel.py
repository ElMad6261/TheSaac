# -*- coding: utf-8 -*-
"""
generar_ui_pixel.py - Arte pixelado del aviso de interaccion ("E ABRIR" sobre el objeto).

Escribe en assets/ui/:
  fuente_pixel.png      fuente de 5 x 7 px (celdas de 6 x 8), ASCII 32-95: espacio, signos, 0-9 y A-Z.
                        Godot la importa como fuente de imagen (fuente_pixel.png.import, importador font_data_image).
  globo.png             globo de 12 x 12 px para 9-slice (bordes de 4 px): linea negra, borde calido y relleno oscuro.
  globo_cola.png        colita de 7 x 4 px que apunta hacia el objeto.
  tecla_e.png           tecla "E" de 13 x 13 px.
  tecla_e_pulsada.png   la misma tecla hundida 1 px (la animacion alterna las dos).

Paleta tomada del kit (tools/blender/kit_isaac.py): linea #120c09, brea #2b1d14 / #3c2a1d, piedra clara.
No necesita Godot, Blender ni librerias: escribe los PNG a mano. Uso, desde la raiz del repo:
    python tools/godot/generar_ui_pixel.py
Despues, en Godot: el sistema de archivos se reimporta solo (o clic derecho -> Reimport).
"""
import os, struct, zlib

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SALIDA = os.path.join(RAIZ, "assets", "ui")

LINEA = "#120c09"
RELLENO = "#3c2a1d"
RELLENO_OSCURO = "#2b1d14"
BORDE = "#d9a86a"
BORDE_LUZ = "#f2d27a"
TECLA = "#e8d8b8"
TECLA_LUZ = "#fff3dc"
TECLA_LADO = "#9a7e60"
TECLA_LETRA = "#2b1d14"


def rgba(hexa, a=255):
    h = hexa.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


VACIO = (0, 0, 0, 0)


def guardar_png(nombre, pix):
    """pix: lista de filas, cada fila una lista de (r, g, b, a)."""
    alto, ancho = len(pix), len(pix[0])
    crudo = b"".join(b"\x00" + bytes(c for p in fila for c in p) for fila in pix)
    def bloque(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos) & 0xffffffff)
    png = b"\x89PNG\r\n\x1a\n" + bloque(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 6, 0, 0, 0))
    png += bloque(b"IDAT", zlib.compress(crudo, 9)) + bloque(b"IEND", b"")
    ruta = os.path.join(SALIDA, nombre)
    with open(ruta, "wb") as f:
        f.write(png)
    return ruta


def lienzo(ancho, alto):
    return [[VACIO] * ancho for _ in range(alto)]


# ------------------------------------------------------------------ fuente 5 x 7
GLIFOS = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    ".": [".....", ".....", ".....", ".....", ".....", ".....", "..#.."],
    ",": [".....", ".....", ".....", ".....", ".....", "..#..", ".#..."],
    ":": [".....", "..#..", ".....", ".....", ".....", "..#..", "....."],
    "-": [".....", ".....", ".....", ".###.", ".....", ".....", "....."],
    "'": ["..#..", "..#..", ".....", ".....", ".....", ".....", "....."],
    "/": ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
    "(": ["...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."],
    ")": [".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    "=": [".....", ".....", "#####", ".....", "#####", ".....", "....."],
    "_": [".....", ".....", ".....", ".....", ".....", ".....", "#####"],
}
CELDA_X, CELDA_Y, COLUMNAS, PRIMERO, ULTIMO = 6, 8, 16, 32, 95


def fuente():
    filas = (ULTIMO - PRIMERO + 1) // COLUMNAS
    img = lienzo(COLUMNAS * CELDA_X, filas * CELDA_Y)
    blanco = (255, 255, 255, 255)   # blanco: el Label le pone el color
    for codigo in range(PRIMERO, ULTIMO + 1):
        g = GLIFOS.get(chr(codigo))
        if not g:
            continue
        i = codigo - PRIMERO
        x0, y0 = (i % COLUMNAS) * CELDA_X, (i // COLUMNAS) * CELDA_Y
        for y, fila in enumerate(g):
            for x, c in enumerate(fila):
                if c == "#":
                    img[y0 + y][x0 + x] = blanco
    return guardar_png("fuente_pixel.png", img), COLUMNAS, filas


# ------------------------------------------------------------------ globo (9-slice) y colita
def globo():
    n = 12
    img = lienzo(n, n)
    for y in range(n):
        for x in range(n):
            borde_ext = x in (0, n - 1) or y in (0, n - 1)
            esquina = (x in (0, n - 1)) and (y in (0, n - 1))
            if esquina:
                continue                                   # esquinas recortadas: el globo se ve redondeado
            if borde_ext:
                img[y][x] = rgba(LINEA)
            elif x in (1, n - 2) or y in (1, n - 2):
                img[y][x] = rgba(BORDE_LUZ if (y == 1 or x == 1) else BORDE)   # bisel: luz arriba e izquierda
            else:
                img[y][x] = rgba(RELLENO_OSCURO if y == n - 3 else RELLENO)
    # las esquinas de adentro del borde calido tambien van negras, para que la esquina quede de 2 px
    for x, y in ((1, 1), (n - 2, 1), (1, n - 2), (n - 2, n - 2)):
        img[y][x] = rgba(LINEA)
    return guardar_png("globo.png", img)


def cola():
    # La primera fila se monta sobre la linea de abajo del globo y la "abre".
    filas = ["#bbbbb#", ".#fff#.", "..#f#..", "...#..."]
    colores = {"#": rgba(LINEA), "b": rgba(BORDE), "f": rgba(RELLENO), ".": VACIO}
    return guardar_png("globo_cola.png", [[colores[c] for c in f] for f in filas])


# ------------------------------------------------------------------ tecla E
def tecla(pulsada):
    ancho, alto = 13, 13
    img = lienzo(ancho, alto)
    arriba = 1 if pulsada else 0               # la tecla pulsada baja 1 px y su lado se ve mas corto
    cara0, cara1 = arriba + 1, arriba + 9      # filas de la cara de arriba
    for y in range(arriba, alto):
        for x in range(ancho):
            esquina = (x in (0, ancho - 1)) and (y in (arriba, alto - 1))
            if esquina:
                continue
            if x in (0, ancho - 1) or y in (arriba, alto - 1):
                img[y][x] = rgba(LINEA)
            elif y <= cara1:
                img[y][x] = rgba(TECLA_LUZ if y == cara0 else TECLA)
            else:
                img[y][x] = rgba(TECLA_LADO)
    for y, fila in enumerate(GLIFOS["E"]):
        for x, c in enumerate(fila):
            if c == "#":
                img[cara0 + 1 + y][4 + x] = rgba(TECLA_LETRA)
    return guardar_png("tecla_e_pulsada.png" if pulsada else "tecla_e.png", img)


if __name__ == "__main__":
    os.makedirs(SALIDA, exist_ok=True)
    ruta, columnas, filas = fuente()
    print("Fuente:", ruta, "(%d columnas x %d filas, ASCII %d-%d)" % (columnas, filas, PRIMERO, ULTIMO))
    print("Globo:", globo())
    print("Cola:", cola())
    print("Tecla:", tecla(False))
    print("Tecla pulsada:", tecla(True))
