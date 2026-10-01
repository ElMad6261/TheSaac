"""
Genera los dibujos del taller de preproducción (TheSaac):
  - planta_basement_1.png / planta_basement_2.png  (planta a escala, 1 cuadro = 1 m)
  - ficha_puerta.png                                (alzado, perfil y planta de giro)
  - flujo_interaccion.png                           (diagrama de flujo de la puerta)
e imprime la matriz de assets modulares con las cantidades de cada nivel.

Uso:  python generar_planos.py
Requiere: matplotlib
"""
from pathlib import Path
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, Arc, FancyBboxPatch, Patch
from matplotlib.lines import Line2D

OUT = Path(__file__).parent
DPI = 200

# ───────────────────────── Métricas del kit modular ─────────────────────────
MURO_ANCHO = 2.0       # módulo de muro: 2 m × 3 m × 0.5 m
MURO_ESP = 0.5
PILAR = 1.0            # pilar 1 × 3 × 1 m en cada unión de muros
VANO = 1.5             # marco de puerta 1.5 × 2.5 × 0.5 m
JAMBA = 0.15
HOJA = 1.2             # hoja 1.2 × 2.3 × 0.1 m
N_LARGO, N_CORTO = 5, 3                  # módulos por tramo (impar → puerta centrada)
PASO_X = N_LARGO * MURO_ANCHO + PILAR    # 11 m de eje a eje
PASO_Y = N_CORTO * MURO_ANCHO + PILAR    # 7 m de eje a eje
COLS, FILAS = 3, 3
ANCHO_NIVEL = COLS * PASO_X + PILAR      # 34 m
ALTO_NIVEL = FILAS * PASO_Y + PILAR      # 22 m

# Colores
C_PISO = "#f4efe6"
C_TIERRA = "#e2ddd5"
C_MURO = "#4b4b4b"
C_PILAR = "#1f1f1f"
C_MARCO = "#8b5a2b"
C_HOJA = "#c08a4d"
C_RUTA = "#d62728"
C_OPC = "#6b6b6b"
C_ANTORCHA = "#f39c12"
C_INTERRUPTOR = "#8e44ad"
C_ROCA = "#9a9a9a"
C_SPAWN = "#27ae60"
C_PIVOTE = "#e00000"


# ───────────────────────────── Geometría de la rejilla ─────────────────────────────
def x_eje(i):  # x del eje vertical i (0..COLS)
    return PILAR / 2 + i * PASO_X


def y_eje(j):  # y del eje horizontal j (0..FILAS); j=0 abajo
    return PILAR / 2 + j * PASO_Y


def celda(c, f):
    """Rectángulo de eje a eje de la sala en columna c, fila f (f=0 arriba)."""
    x0, x1 = x_eje(c), x_eje(c + 1)
    y1 = y_eje(FILAS - f)
    y0 = y_eje(FILAS - f - 1)
    return x0, y0, x1, y1


def centro(c, f):
    x0, y0, x1, y1 = celda(c, f)
    return (x0 + x1) / 2, (y0 + y1) / 2


# ───────────────────────────── Definición de los niveles ─────────────────────────────
# Salas: (columna, fila) -> (nombre, tipo). Fila 0 = arriba en el plano.
# Conexiones: (sala A, sala B, sala hacia donde abre la hoja, bloqueada)
BASEMENT_1 = {
    "titulo": "Basement 1 — Planta a escala",
    "subtitulo": "Mapa fijo para la entrega · 7 salas · rejilla 1 cuadro = 1 m",
    "salas": {
        (0, 0): ("Sala del tesoro", "tesoro"),
        (1, 0): ("Sala de rocas", "normal"),
        (0, 1): ("Sala de inicio", "inicio"),
        (1, 1): ("Sala central", "normal"),
        (2, 1): ("Sala del tragaluz", "normal"),
        (1, 2): ("Sala del interruptor", "interruptor"),
        (2, 2): ("Sala del jefe", "jefe"),
    },
    "conexiones": [
        ((0, 1), (1, 1), (1, 1), False),
        ((1, 1), (1, 0), (1, 0), False),
        ((1, 0), (0, 0), (0, 0), False),
        ((1, 1), (2, 1), (2, 1), False),
        ((1, 1), (1, 2), (1, 2), False),
        ((2, 1), (2, 2), (2, 2), True),   # puerta del jefe: se desbloquea con el interruptor
    ],
    "tragaluz": [(2, 1)],
    "spawn": (3.5, 11.0),
    "meta": (2, 2),
    "ruta": [(3.5, 11.0), (11.5, 11.0), (16.4, 11.0), (16.4, 2.4), (17.6, 2.4),
             (17.6, 10.4), (22.5, 10.4), (27.4, 10.4), (27.4, 4.3)],
    "ruta_opcional": [(17.0, 11.9), (17.0, 18.0), (11.5, 18.0), (6.9, 18.0)],
    "rocas": [(13.3, 12.3), (20.7, 12.4), (13.4, 8.7), (20.6, 8.6),
              (13.3, 19.1), (20.7, 19.2), (20.3, 16.4), (14.2, 16.2),
              (24.2, 12.4), (32.0, 12.3), (31.2, 8.9), (24.4, 8.5),
              (13.6, 4.2), (20.4, 4.0)],
    "nota_bloqueo": "Bloqueada hasta\nactivar el\ninterruptor",
}

BASEMENT_2 = {
    "titulo": "Basement 2 — Planta a escala",
    "subtitulo": "Post-entrega · 8 salas · mismos módulos que Basement 1 · 1 cuadro = 1 m",
    "salas": {
        (0, 0): ("Sala del jefe", "jefe"),
        (1, 0): ("Sala norte", "normal"),
        (2, 0): ("Sala noreste", "normal"),
        (0, 1): ("Sala oeste", "normal"),
        (1, 1): ("Sala de llegada", "inicio"),
        (2, 1): ("Sala del tesoro", "tesoro"),
        (0, 2): ("Sala suroeste", "normal"),
        (1, 2): ("Sala sur", "normal"),
    },
    "conexiones": [
        ((1, 1), (1, 0), (1, 0), False),
        ((1, 0), (2, 0), (2, 0), False),
        ((1, 1), (2, 1), (2, 1), False),
        ((1, 1), (1, 2), (1, 2), False),
        ((1, 2), (0, 2), (0, 2), False),
        ((0, 2), (0, 1), (0, 1), False),
        ((0, 1), (0, 0), (0, 0), False),
    ],
    "tragaluz": [(2, 0)],
    "spawn": (17.0, 11.0),
    "meta": (0, 0),
    "ruta": [(17.0, 10.3), (17.0, 4.0), (11.5, 4.0), (6.6, 4.0), (6.6, 7.5),
             (6.6, 14.5), (6.6, 17.1)],
    "ruta_opcional": [(17.9, 11.6), (22.5, 11.6), (25.6, 11.6)],
    "ruta_opcional_2": [(17.35, 11.75), (17.35, 18.0), (22.5, 18.0), (26.8, 18.0)],
    "rocas": [(13.5, 20.0), (20.5, 20.2), (14.0, 16.3),
              (24.6, 19.6), (31.0, 16.3), (32.1, 19.5), (24.8, 16.1),
              (3.0, 13.0), (9.5, 13.1), (3.2, 9.0), (9.6, 8.8),
              (2.4, 5.2), (10.0, 5.6), (3.3, 2.0), (9.5, 2.1),
              (13.6, 6.0), (20.4, 6.1), (13.4, 2.1), (20.6, 2.0), (20.6, 16.4)],
    "nota_bloqueo": None,
}

# Rocas por tipo de sala (para la matriz)
ROCAS_POR_TIPO = {"normal": 4, "interruptor": 2, "inicio": 0, "tesoro": 0, "jefe": 0}


# ───────────────────────────── Tramos de muro ─────────────────────────────
def tramos(nivel):
    """Devuelve la lista de tramos de muro que existen: (orientación, i, j, puerta|None)."""
    salas = nivel["salas"]
    conex = {}
    for a, b, hacia, bloq in nivel["conexiones"]:
        conex[frozenset((a, b))] = (hacia, bloq)
    out = []
    # Horizontales: eje y j (0..FILAS), columna c. Separa fila (FILAS-j-1) arriba y (FILAS-j) abajo.
    for j in range(FILAS + 1):
        for c in range(COLS):
            arriba = (c, FILAS - j - 1) if j < FILAS else None
            abajo = (c, FILAS - j) if j > 0 else None
            if (arriba in salas) or (abajo in salas):
                puerta = conex.get(frozenset((arriba, abajo))) if arriba and abajo else None
                out.append(("H", c, j, puerta, arriba, abajo))
    # Verticales: eje x i (0..COLS), fila f.
    for i in range(COLS + 1):
        for f in range(FILAS):
            izq = (i - 1, f) if i > 0 else None
            der = (i, f) if i < COLS else None
            if (izq in salas) or (der in salas):
                puerta = conex.get(frozenset((izq, der))) if izq and der else None
                out.append(("V", i, f, puerta, izq, der))
    return out


def pilares(nivel):
    pts = set()
    for o, a, b, *_ in tramos(nivel):
        if o == "H":
            y = y_eje(b)
            pts.add((x_eje(a), y)); pts.add((x_eje(a + 1), y))
        else:
            x = x_eje(a)
            y0 = y_eje(FILAS - b - 1); y1 = y_eje(FILAS - b)
            pts.add((x, y0)); pts.add((x, y1))
    return sorted(pts)


def contar(nivel):
    t = tramos(nivel)
    muros = vanos = 0
    for o, a, b, puerta, *_ in t:
        n = N_LARGO if o == "H" else N_CORTO
        if puerta:
            vanos += 1
            muros += n - 1
        else:
            muros += n
    salas = nivel["salas"]
    n_salas = len(salas)
    n_tragaluz = len(nivel["tragaluz"])
    return {
        "Muro estándar": muros,
        "Muro con vano": vanos,
        "Pilar modular": len(pilares(nivel)),
        "Marco de puerta": len(nivel["conexiones"]),
        "Puerta (hoja)": len(nivel["conexiones"]),
        "Piso de sala": n_salas,
        "Techo de sala": n_salas - n_tragaluz,
        "Techo con tragaluz": n_tragaluz,
        "Antorcha": 2 * n_salas,
        "Interruptor (palanca)": sum(1 for _, tp in salas.values() if tp == "interruptor"),
        "Roca": sum(ROCAS_POR_TIPO[tp] for _, tp in salas.values()),
        "Pedestal": sum(1 for _, tp in salas.values() if tp == "tesoro"),
        "Trampilla de salida": 1,
    }


# ───────────────────────────── Dibujo de la planta ─────────────────────────────
def roca(ax, x, y, r=0.5, semilla=0):
    pts = []
    for k in range(7):
        ang = 2 * math.pi * k / 7
        rr = r * (0.75 + 0.25 * math.sin(semilla * 1.7 + k * 2.3))
        pts.append((x + rr * math.cos(ang), y + rr * math.sin(ang)))
    ax.add_patch(Polygon(pts, closed=True, fc=C_ROCA, ec="#5e5e5e", lw=0.8, zorder=6))


def flecha_ruta(ax, pts, color, lw, estilo):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, ls=estilo, zorder=8, solid_capstyle="round")
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        if math.hypot(x1 - x0, y1 - y0) < 2.5:
            continue
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = (x1 - x0), (y1 - y0)
        L = math.hypot(dx, dy)
        ax.annotate("", xy=(mx + dx / L * 0.35, my + dy / L * 0.35),
                    xytext=(mx - dx / L * 0.35, my - dy / L * 0.35),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=14),
                    zorder=9)
    # punta final
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    ax.annotate("", xy=(x1, y1), xytext=(x0 + (x1 - x0) * 0.9, y0 + (y1 - y0) * 0.9),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=16), zorder=9)


def dibujar_puerta_planta(ax, o, a, b, hacia, bloqueada, desde):
    """Marco (jambas), hoja abierta 90° hacia la sala 'hacia' y arco de giro."""
    if o == "H":
        y = y_eje(b)
        xc = (x_eje(a) + x_eje(a + 1)) / 2
        # jambas
        for xj in (xc - VANO / 2, xc + VANO / 2 - JAMBA):
            ax.add_patch(Rectangle((xj, y - MURO_ESP / 2), JAMBA, MURO_ESP, fc=C_MARCO, ec="none", zorder=5))
        bis = (xc - HOJA / 2, y)
        s = 1 if centro(*hacia)[1] > y else -1
        if bloqueada:
            ax.add_patch(Rectangle((xc - HOJA / 2, y - 0.07), HOJA, 0.14, fc="#c0392b", ec="#7b1e14", lw=0.8, zorder=6))
        else:
            ax.add_patch(Rectangle((bis[0], y if s > 0 else y - HOJA), 0.1, HOJA, fc=C_HOJA, ec="#6b4423", lw=0.8, zorder=6))
            t1, t2 = (0, 90) if s > 0 else (270, 360)
            ax.add_patch(Arc(bis, 2 * HOJA, 2 * HOJA, theta1=t1, theta2=t2, color="#6b4423", lw=0.8, ls=(0, (2, 2)), zorder=6))
    else:
        x = x_eje(a)
        y0 = y_eje(FILAS - b - 1); y1 = y_eje(FILAS - b)
        yc = (y0 + y1) / 2
        for yj in (yc - VANO / 2, yc + VANO / 2 - JAMBA):
            ax.add_patch(Rectangle((x - MURO_ESP / 2, yj), MURO_ESP, JAMBA, fc=C_MARCO, ec="none", zorder=5))
        bis = (x, yc - HOJA / 2)
        s = 1 if centro(*hacia)[0] > x else -1
        if bloqueada:
            ax.add_patch(Rectangle((x - 0.07, yc - HOJA / 2), 0.14, HOJA, fc="#c0392b", ec="#7b1e14", lw=0.8, zorder=6))
        else:
            ax.add_patch(Rectangle((x if s > 0 else x - HOJA, bis[1]), HOJA, 0.1, fc=C_HOJA, ec="#6b4423", lw=0.8, zorder=6))
            t1, t2 = (0, 90) if s > 0 else (90, 180)
            ax.add_patch(Arc(bis, 2 * HOJA, 2 * HOJA, theta1=t1, theta2=t2, color="#6b4423", lw=0.8, ls=(0, (2, 2)), zorder=6))


def dibujar_planta(nivel, archivo):
    fig, ax = plt.subplots(figsize=(17, 10.2))
    ax.set_aspect("equal")
    salas = nivel["salas"]

    # Tierra (celdas sin sala) y pisos
    for c in range(COLS):
        for f in range(FILAS):
            x0, y0, x1, y1 = celda(c, f)
            if (c, f) in salas:
                ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=C_PISO, ec="none", zorder=0))
            else:
                ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=C_TIERRA, ec="none",
                                       hatch="///", zorder=0))
                ax.text((x0 + x1) / 2, (y0 + y1) / 2, "Tierra\n(sin sala)", ha="center", va="center",
                        fontsize=10, color="#8a857d", style="italic", zorder=1,
                        bbox=dict(fc=C_TIERRA, ec="none", pad=1.5))

    # Rejilla de 1 m
    for x in range(0, int(ANCHO_NIVEL) + 1):
        ax.plot([x, x], [0, ALTO_NIVEL], color="#000000", alpha=0.18 if x % 5 else 0.32, lw=0.4 if x % 5 else 0.7, zorder=2)
    for y in range(0, int(ALTO_NIVEL) + 1):
        ax.plot([0, ANCHO_NIVEL], [y, y], color="#000000", alpha=0.18 if y % 5 else 0.32, lw=0.4 if y % 5 else 0.7, zorder=2)

    # Muros
    for o, a, b, puerta, l1, l2 in tramos(nivel):
        if o == "H":
            y = y_eje(b)
            xa, xb = x_eje(a) + PILAR / 2, x_eje(a + 1) - PILAR / 2
            if puerta:
                xc = (xa + xb) / 2
                ax.add_patch(Rectangle((xa, y - MURO_ESP / 2), (xc - VANO / 2) - xa, MURO_ESP, fc=C_MURO, ec="none", zorder=4))
                ax.add_patch(Rectangle((xc + VANO / 2, y - MURO_ESP / 2), xb - (xc + VANO / 2), MURO_ESP, fc=C_MURO, ec="none", zorder=4))
                dibujar_puerta_planta(ax, o, a, b, puerta[0], puerta[1], None)
            else:
                ax.add_patch(Rectangle((xa, y - MURO_ESP / 2), xb - xa, MURO_ESP, fc=C_MURO, ec="none", zorder=4))
        else:
            x = x_eje(a)
            ya, yb = y_eje(FILAS - b - 1) + PILAR / 2, y_eje(FILAS - b) - PILAR / 2
            if puerta:
                yc = (ya + yb) / 2
                ax.add_patch(Rectangle((x - MURO_ESP / 2, ya), MURO_ESP, (yc - VANO / 2) - ya, fc=C_MURO, ec="none", zorder=4))
                ax.add_patch(Rectangle((x - MURO_ESP / 2, yc + VANO / 2), MURO_ESP, yb - (yc + VANO / 2), fc=C_MURO, ec="none", zorder=4))
                dibujar_puerta_planta(ax, o, a, b, puerta[0], puerta[1], None)
            else:
                ax.add_patch(Rectangle((x - MURO_ESP / 2, ya), MURO_ESP, yb - ya, fc=C_MURO, ec="none", zorder=4))

    # Pilares
    for (px, py) in pilares(nivel):
        ax.add_patch(Rectangle((px - PILAR / 2, py - PILAR / 2), PILAR, PILAR, fc=C_PILAR, ec="none", zorder=5))

    # Contenido de cada sala
    for (c, f), (nombre, tipo) in salas.items():
        x0, y0, x1, y1 = celda(c, f)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        ax.text(cx, y1 - 1.35, nombre, ha="center", va="center", fontsize=11.5, fontweight="bold",
                color="#2b2b2b", zorder=10, bbox=dict(fc=C_PISO, ec="none", pad=1.2, alpha=0.9))
        # Antorchas en el muro norte
        for xt in (x0 + 2.5, x1 - 2.5):
            ax.add_patch(Circle((xt, y1 - 0.62), 0.28, fc=C_ANTORCHA, ec="#a85d00", lw=1, zorder=7))
        if tipo == "interruptor":
            ax.add_patch(Rectangle((cx - 0.25, y0 + 0.3), 0.5, 0.45, fc=C_INTERRUPTOR, ec="#4a235a", lw=1, zorder=7))
            ax.text(cx + 0.55, y0 + 1.25, "Interruptor", fontsize=9.5, color=C_INTERRUPTOR, fontweight="bold", zorder=10)
        if tipo == "tesoro":
            ax.add_patch(Rectangle((cx - 0.4 - 1.5, cy - 0.4 + 0.4), 0.8, 0.8, fc="#d9b26f", ec="#7a5a1d", lw=1, zorder=7))
            ax.text(cx - 1.5, cy - 0.55, "Pedestal", fontsize=9, ha="center", color="#7a5a1d", zorder=10)
        if (c, f) in nivel["tragaluz"]:
            ax.add_patch(Rectangle((cx - 1, cy - 1), 2, 2, fc="#d6eaf8", ec="#2e86c1", lw=1.2, ls="--", alpha=0.85, zorder=3))
            ax.text(cx + 1.15, cy - 1.35, "Tragaluz 2 × 2 m", fontsize=9, color="#2e86c1", zorder=10)

    # Rocas
    for k, (rx, ry) in enumerate(nivel["rocas"]):
        roca(ax, rx, ry, 0.55, k)

    # Meta (trampilla)
    mx, my = centro(*nivel["meta"])
    my -= 0.6
    ax.add_patch(Rectangle((mx - 0.75, my - 0.75), 1.5, 1.5, fc="#2b2b2b", ec="#000", lw=1, zorder=9))
    ax.plot([mx - 0.75, mx + 0.75], [my - 0.75, my + 0.75], color="#ffffff", lw=0.8, zorder=10)
    ax.plot([mx - 0.75, mx + 0.75], [my + 0.75, my - 0.75], color="#ffffff", lw=0.8, zorder=10)
    ax.text(mx + 1.0, my - 0.1, "META\n(trampilla)", fontsize=10, fontweight="bold", va="center", color="#000", zorder=10)

    # Rutas
    flecha_ruta(ax, nivel["ruta"], C_RUTA, 2.4, (0, (4, 2.5)))
    flecha_ruta(ax, nivel["ruta_opcional"], C_OPC, 1.8, (0, (2, 2)))
    if nivel.get("ruta_opcional_2"):
        flecha_ruta(ax, nivel["ruta_opcional_2"], C_OPC, 1.8, (0, (2, 2)))

    # Spawn
    sx, sy = nivel["spawn"]
    ax.add_patch(Circle((sx, sy), 0.65, fc=C_SPAWN, ec="#145a32", lw=1.2, zorder=11))
    ax.text(sx, sy, "S", ha="center", va="center", fontsize=12, fontweight="bold", color="white", zorder=12)
    ax.text(sx, sy - 1.25, "SPAWN", ha="center", fontsize=10, fontweight="bold", color="#145a32", zorder=12)

    # Nota de la puerta bloqueada
    if nivel["nota_bloqueo"]:
        for a, b, hacia, bloq in nivel["conexiones"]:
            if bloq:
                ax.annotate(nivel["nota_bloqueo"], xy=(28.5, 7.4), xytext=(23.1, 1.9), fontsize=9,
                            color="#c0392b", fontweight="bold", zorder=12,
                            arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1))

    # Cotas generales
    ax.annotate("", xy=(0, ALTO_NIVEL + 1.0), xytext=(ANCHO_NIVEL, ALTO_NIVEL + 1.0),
                arrowprops=dict(arrowstyle="<->", color="#333", lw=1))
    ax.text(ANCHO_NIVEL / 2, ALTO_NIVEL + 1.35, f"{ANCHO_NIVEL:g} m", ha="center", fontsize=11, fontweight="bold")
    ax.annotate("", xy=(-1.0, 0), xytext=(-1.0, ALTO_NIVEL),
                arrowprops=dict(arrowstyle="<->", color="#333", lw=1))
    ax.text(-1.45, ALTO_NIVEL / 2, f"{ALTO_NIVEL:g} m", va="center", rotation=90, fontsize=11, fontweight="bold")
    # Cota de una sala (eje a eje)
    x0, y0, x1, y1 = celda(*list(salas.keys())[0])
    ax.annotate("", xy=(x_eje(0), -1.0), xytext=(x_eje(1), -1.0), arrowprops=dict(arrowstyle="<->", color="#555", lw=0.9))
    ax.text((x_eje(0) + x_eje(1)) / 2, -1.6, f"{PASO_X:g} m (eje a eje)", ha="center", fontsize=9.5, color="#555")
    ax.annotate("", xy=(ANCHO_NIVEL + 1.0, y_eje(0)), xytext=(ANCHO_NIVEL + 1.0, y_eje(1)),
                arrowprops=dict(arrowstyle="<->", color="#555", lw=0.9))
    ax.text(ANCHO_NIVEL + 1.3, (y_eje(0) + y_eje(1)) / 2, f"{PASO_Y:g} m", va="center", fontsize=9.5, color="#555")

    # Escala gráfica
    for k in range(0, 10, 1):
        ax.add_patch(Rectangle((k, -3.2), 1, 0.35, fc="#222" if k % 2 == 0 else "white", ec="#222", lw=0.8))
    for v in (0, 5, 10):
        ax.text(v, -3.75, f"{v}", ha="center", fontsize=9)
    ax.text(10.6, -3.1, "m  ·  1 cuadro = 1 m", fontsize=9.5)

    # Leyenda
    handles = [
        Line2D([], [], marker="o", ls="", ms=12, mfc=C_SPAWN, mec="#145a32", label="Spawn (inicio del jugador)"),
        Patch(fc="#2b2b2b", ec="#000", label="Meta: trampilla 1.5 × 1.5 m"),
        Line2D([], [], color=C_RUTA, lw=2.4, ls=(0, (4, 2.5)), label="Ruta principal"),
        Line2D([], [], color=C_OPC, lw=1.8, ls=(0, (2, 2)), label="Ruta opcional"),
        Patch(fc=C_MURO, label="Muro 2 × 3 × 0.5 m"),
        Patch(fc=C_PILAR, label="Pilar 1 × 3 × 1 m (uniones)"),
        Patch(fc=C_MARCO, label="Marco de puerta 1.5 × 2.5 m"),
        Patch(fc=C_HOJA, ec="#6b4423", label="Puerta abierta + arco de 90°"),
        Patch(fc="#c0392b", label="Puerta bloqueada"),
        Line2D([], [], marker="o", ls="", ms=10, mfc=C_ANTORCHA, mec="#a85d00", label="Antorcha (interactiva)"),
        Patch(fc=C_INTERRUPTOR, label="Interruptor (interactivo)"),
        Patch(fc=C_ROCA, ec="#5e5e5e", label="Roca (Geometry Nodes)"),
        Patch(fc="#d9b26f", ec="#7a5a1d", label="Pedestal"),
        Patch(fc="#d6eaf8", ec="#2e86c1", ls="--", label="Tragaluz (luz direccional)"),
    ]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.035, 1.0), fontsize=10,
              frameon=True, title="Leyenda", title_fontsize=11, borderpad=0.9, labelspacing=0.85)

    ax.set_xlim(-2.2, ANCHO_NIVEL + 2.2)
    ax.set_ylim(-4.3, ALTO_NIVEL + 2.2)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(f"{nivel['titulo']}\n", fontsize=17, fontweight="bold", loc="left")
    ax.text(0, ALTO_NIVEL + 2.55, nivel["subtitulo"], fontsize=11, color="#555")
    fig.tight_layout()
    fig.savefig(OUT / archivo, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ───────────────────────────── Ficha técnica de la puerta ─────────────────────────────
def cota(ax, p0, p1, texto, off=(0, 0), rot=0, fs=10, color="#222"):
    ax.annotate("", xy=p0, xytext=p1, arrowprops=dict(arrowstyle="<->", color=color, lw=0.9, shrinkA=0, shrinkB=0))
    mx, my = (p0[0] + p1[0]) / 2 + off[0], (p0[1] + p1[1]) / 2 + off[1]
    ax.text(mx, my, texto, ha="center", va="center", fontsize=fs, rotation=rot, color=color,
            bbox=dict(fc="white", ec="none", pad=0.6))


def pivote(ax, x, y, r=0.06):
    ax.add_patch(Circle((x, y), r, fc="none", ec=C_PIVOTE, lw=2, zorder=20))
    ax.plot([x - r * 1.8, x + r * 1.8], [y, y], color=C_PIVOTE, lw=1.6, zorder=20)
    ax.plot([x, x], [y - r * 1.8, y + r * 1.8], color=C_PIVOTE, lw=1.6, zorder=20)


def dibujar_ficha(archivo):
    fig, axs = plt.subplots(1, 3, figsize=(17, 8.6), gridspec_kw={"width_ratios": [1.25, 0.8, 1.25]})

    # ── Alzado frontal
    ax = axs[0]
    ax.set_aspect("equal")
    ax.add_patch(Rectangle((-0.45, -0.12), 2.35, 0.12, fc="#bbb", ec="none", hatch="////"))
    for r in [(0, 0, JAMBA, 2.5), (1.5 - JAMBA, 0, JAMBA, 2.5), (JAMBA, 2.3, 1.2, 0.2)]:
        ax.add_patch(Rectangle(r[:2], r[2], r[3], fc=C_MARCO, ec="#5a3a1a", lw=1))
    ax.add_patch(Rectangle((JAMBA, 0), HOJA, 2.3, fc=C_HOJA, ec="#6b4423", lw=1.3))
    for (yy, hh) in [(0.15, 0.95), (1.2, 0.95)]:
        ax.add_patch(Rectangle((JAMBA + 0.15, yy), 0.9, hh, fc="none", ec="#8a6234", lw=0.9))
    for yb in (0.3, 1.9):
        ax.add_patch(Rectangle((JAMBA, yb), 0.05, 0.15, fc="#333", ec="none", zorder=5))
    ax.add_patch(Circle((1.2, 1.05), 0.04, fc="#333"))
    ax.add_patch(Rectangle((1.16, 1.18), 0.08, 0.12, fc="#555"))
    ax.text(1.27, 1.24, "cerrojo", fontsize=8.5, color="#333")
    ax.text(0.06, 0.38, "bisagras", fontsize=8.5, color="#333", rotation=90, va="bottom")
    ax.plot([JAMBA, JAMBA], [-0.35, 2.85], color=C_PIVOTE, lw=1.4, ls=(0, (6, 3)), zorder=19)
    ax.text(JAMBA + 0.05, 2.9, "Eje de giro\nY (Godot) / Z (Blender)", color=C_PIVOTE, fontsize=9.5, fontweight="bold", va="bottom")
    pivote(ax, JAMBA, 0)
    ax.annotate("PIVOTE (origen)\nborde de la bisagra,\nbase de la hoja", xy=(JAMBA, 0), xytext=(-0.95, 0.55),
                fontsize=9.5, color=C_PIVOTE, fontweight="bold", arrowprops=dict(arrowstyle="->", color=C_PIVOTE))
    cota(ax, (JAMBA, -0.38), (JAMBA + HOJA, -0.38), "Hoja 1.20 m (120 cm)")
    cota(ax, (0, -0.68), (1.5, -0.68), "Marco 1.50 m (150 cm)")
    cota(ax, (1.72, 0), (1.72, 2.3), "2.30 m (230 cm)", rot=90)
    cota(ax, (2.02, 0), (2.02, 2.5), "2.50 m (250 cm)", rot=90)
    ax.annotate("Jamba 0.15 m (15 cm)", xy=(1.5 - JAMBA / 2, 1.6), xytext=(1.62, 1.75), fontsize=9,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.annotate("Dintel 0.20 m (20 cm)", xy=(0.75, 2.4), xytext=(0.3, 2.62), fontsize=9,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.set_xlim(-1.05, 2.35); ax.set_ylim(-0.95, 3.4)
    ax.set_title("1 · Alzado frontal (plano)", fontsize=13, fontweight="bold", loc="left")
    ax.axis("off")

    # ── Perfil lateral
    ax = axs[1]
    ax.set_aspect("equal")
    ax.add_patch(Rectangle((-0.3, -0.12), 1.1, 0.12, fc="#bbb", ec="none", hatch="////"))
    ax.add_patch(Rectangle((0, 0), 0.5, 2.5, fc="none", ec="#5a3a1a", lw=1.2, ls="--"))
    ax.add_patch(Rectangle((0, 2.3), 0.5, 0.2, fc=C_MARCO, ec="#5a3a1a", lw=1))
    ax.add_patch(Rectangle((0.2, 0), 0.1, 2.3, fc=C_HOJA, ec="#6b4423", lw=1.3))
    ax.plot([0.25, 0.25], [-0.35, 2.85], color=C_PIVOTE, lw=1.4, ls=(0, (6, 3)))
    pivote(ax, 0.25, 0)
    ax.annotate("Pivote al centro\ndel espesor (5 cm)", xy=(0.25, 0), xytext=(0.42, 0.55), fontsize=9.5,
                color=C_PIVOTE, fontweight="bold", arrowprops=dict(arrowstyle="->", color=C_PIVOTE))
    cota(ax, (0.2, 2.62), (0.3, 2.62), "", fs=8)
    ax.text(0.25, 2.98, "Hoja 0.10 m\n(10 cm)", ha="center", fontsize=9.5)
    cota(ax, (0, -0.38), (0.5, -0.38), "Marco 0.50 m (50 cm)", fs=9.5)
    cota(ax, (-0.17, 0), (-0.17, 2.3), "2.30 m", rot=90, fs=9.5)
    ax.text(0.55, 1.4, "marco\n(línea\ndiscontinua)", fontsize=8.5, color="#5a3a1a")
    ax.set_xlim(-0.35, 0.95); ax.set_ylim(-0.95, 3.4)
    ax.set_title("2 · Perfil (vista lateral)", fontsize=13, fontweight="bold", loc="left")
    ax.axis("off")

    # ── Planta de giro
    ax = axs[2]
    ax.set_aspect("equal")
    ax.add_patch(Rectangle((-0.25, -1.5), 2.0, 3.0, fc="#fdf2e9", ec="#e67e22", lw=1.2, ls=(0, (4, 3)), zorder=0))
    ax.text(1.78, -1.42, "Área de detección\n(Area3D) 2 × 3 m", fontsize=9, color="#c0661a", va="bottom")
    ax.add_patch(Rectangle((-1.0, -0.25), 1.0, 0.5, fc=C_MURO, ec="none"))
    ax.add_patch(Rectangle((1.5, -0.25), 1.0, 0.5, fc=C_MURO, ec="none"))
    ax.add_patch(Rectangle((0, -0.25), JAMBA, 0.5, fc=C_MARCO, ec="none"))
    ax.add_patch(Rectangle((1.5 - JAMBA, -0.25), JAMBA, 0.5, fc=C_MARCO, ec="none"))
    ax.add_patch(Rectangle((JAMBA, -0.05), HOJA, 0.1, fc="none", ec="#6b4423", lw=1, ls="--"))
    ax.text(0.75, -0.42, "cerrada (0°)", ha="center", fontsize=9, color="#6b4423")
    ax.add_patch(Rectangle((JAMBA - 0.05, 0), 0.1, HOJA, fc=C_HOJA, ec="#6b4423", lw=1.3))
    ax.text(-0.02, 1.32, "abierta (+90°)", ha="center", fontsize=9, color="#6b4423")
    ax.add_patch(Arc((JAMBA, 0), 2 * HOJA, 2 * HOJA, theta1=2, theta2=88, color=C_PIVOTE, lw=1.4))
    ax.annotate("", xy=(JAMBA + HOJA * math.cos(math.radians(84)), HOJA * math.sin(math.radians(84))),
                xytext=(JAMBA + HOJA * math.cos(math.radians(70)), HOJA * math.sin(math.radians(70))),
                arrowprops=dict(arrowstyle="-|>", color=C_PIVOTE, lw=1.4, mutation_scale=16))
    ax.text(1.28, 1.02, "+90°", fontsize=15, fontweight="bold", color=C_PIVOTE)
    ax.text(1.28, 0.9, "antihorario visto\ndesde arriba", fontsize=8.5, color=C_PIVOTE, va="top")
    pivote(ax, JAMBA, 0)
    # ejes
    ox, oy = -1.3, -1.15
    ax.annotate("", xy=(ox + 0.5, oy), xytext=(ox, oy), arrowprops=dict(arrowstyle="-|>", color="#c0392b", lw=1.3))
    ax.annotate("", xy=(ox, oy + 0.5), xytext=(ox, oy), arrowprops=dict(arrowstyle="-|>", color="#27ae60", lw=1.3))
    ax.text(ox + 0.55, oy - 0.05, "X", fontsize=9, color="#c0392b", fontweight="bold", va="center")
    ax.text(ox - 0.05, oy + 0.58, "+Y Blender\n−Z Godot", fontsize=8, color="#27ae60", ha="center", va="bottom")
    ax.text(ox + 0.12, oy - 0.3, "eje de giro sale\nhacia el lector", fontsize=7.5, color="#555", va="top")
    ax.text(0.75, 1.75, "Sala destino", fontsize=10, color="#555", ha="center", style="italic")
    ax.text(0.75, -1.05, "Sala de origen", fontsize=10, color="#555", ha="center", style="italic")
    ax.set_xlim(-1.75, 2.6); ax.set_ylim(-1.75, 2.15)
    ax.set_title("3 · Planta de giro (vista superior)", fontsize=13, fontweight="bold", loc="left")
    ax.axis("off")

    fig.suptitle("Ficha técnica · Asset interactivo: Puerta (Puerta_Hoja)", fontsize=17, fontweight="bold", x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(OUT / archivo, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ───────────────────────────── Diagrama de flujo ─────────────────────────────
def caja(ax, x, y, texto, tipo="proc", w=3.7, h=0.95, color="#eaf2f8", borde="#2e86c1"):
    if tipo == "term":
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=0.45",
                                    fc=color, ec=borde, lw=1.4, zorder=3))
    elif tipo == "dec":
        w, h = 3.3, 1.45
        ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)],
                             closed=True, fc="#fef9e7", ec="#b7950b", lw=1.4, zorder=3))
    elif tipo == "io":
        s = 0.3
        ax.add_patch(Polygon([(x - w / 2 + s, y + h / 2), (x + w / 2 + s, y + h / 2),
                              (x + w / 2 - s, y - h / 2), (x - w / 2 - s, y - h / 2)],
                             closed=True, fc="#e8f8f5", ec="#17a589", lw=1.4, zorder=3))
    else:
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=color, ec=borde, lw=1.4, zorder=3))
    ax.text(x, y, texto, ha="center", va="center", fontsize=10, zorder=4)


def flecha(ax, pts, texto=None, tpos=0, toff=(0.15, 0.12), ls="-", color="#333"):
    for (x0, y0), (x1, y1) in zip(pts[:-2], pts[1:-1]):
        ax.plot([x0, x1], [y0, y1], color=color, lw=1.3, ls=ls, zorder=2)
    ax.annotate("", xy=pts[-1], xytext=pts[-2],
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.3, ls=ls, mutation_scale=14, shrinkA=0, shrinkB=0),
                zorder=2)
    if texto:
        (x0, y0), (x1, y1) = pts[tpos], pts[tpos + 1]
        ax.text(x0 + toff[0], y0 + toff[1], texto, fontsize=10, fontweight="bold", color="#555", zorder=5)


def dibujar_flujo(archivo):
    fig, ax = plt.subplots(figsize=(15, 13))
    ax.set_aspect("equal")
    D = 0.725  # media altura del rombo
    W = 1.65   # media anchura del rombo

    caja(ax, 0, 12.0, "INICIO\nEl jugador explora la sala", "term", color="#eafaf1", borde="#27ae60")
    caja(ax, 0, 10.3, "¿Entra al área de\ndetección (Area3D)?", "dec")
    caja(ax, 0, 8.3, "¿La puerta está\nbloqueada?", "dec")
    caja(ax, 0, 6.3, "¿La puerta ya\nestá abierta?", "dec")
    caja(ax, 0, 4.65, "Mensaje en pantalla:\n«Presiona E · Abrir»", "io")
    caja(ax, 0, 3.0, "¿Presiona la\ntecla E?", "dec")
    caja(ax, 0, 1.4, "Ocultar el mensaje")
    caja(ax, 0, -0.15, "La puerta rota +90° sobre su pivote\n(Quaternion.Slerp / Tween · 0.6 s)", w=4.6, h=1.05,
         color="#fdedec", borde="#c0392b")
    caja(ax, 0, -1.7, "Estado = abierta\n(ya no vuelve a pedir E)")
    caja(ax, 0, -3.1, "FIN", "term", w=2.2, color="#eafaf1", borde="#27ae60")

    caja(ax, 4.9, 8.3, "Mensaje:\n«Cerrada · activa el interruptor»", "io", w=3.9)
    caja(ax, 4.9, 6.3, "No muestra mensaje\n(el jugador puede pasar)", "term", w=3.9, color="#f4f6f7", borde="#7f8c8d")
    caja(ax, -4.5, 3.0, "¿Sale del área\nde detección?", "dec")
    caja(ax, -8.3, 3.0, "Ocultar el\nmensaje", w=2.6)

    # Columna principal
    flecha(ax, [(0, 12.0 - 0.475), (0, 10.3 + D)])
    flecha(ax, [(0, 10.3 - D), (0, 8.3 + D)], "Sí", 0, (0.15, -0.32))
    flecha(ax, [(0, 8.3 - D), (0, 6.3 + D)], "No", 0, (0.15, -0.32))
    flecha(ax, [(0, 6.3 - D), (0, 4.65 + 0.475)], "No", 0, (0.15, -0.32))
    flecha(ax, [(0, 4.65 - 0.475), (0, 3.0 + D)])
    flecha(ax, [(0, 3.0 - D), (0, 1.4 + 0.475)], "Sí", 0, (0.15, -0.32))
    flecha(ax, [(0, 1.4 - 0.475), (0, -0.15 + 0.525)])
    flecha(ax, [(0, -0.15 - 0.525), (0, -1.7 + 0.475)])
    flecha(ax, [(0, -1.7 - 0.475), (0, -3.1 + 0.475)])

    # ¿Entra? No → vuelve al inicio
    flecha(ax, [(-W, 10.3), (-2.7, 10.3), (-2.7, 12.0), (-1.85, 12.0)], "No", 0, (-0.75, 0.12))
    # Bloqueada: Sí → mensaje → vuelve al inicio
    flecha(ax, [(W, 8.3), (2.95 - 0.05, 8.3)], "Sí", 0, (0.12, 0.12))
    flecha(ax, [(4.9, 8.3 + 0.475), (4.9, 12.0), (1.85, 12.0)])
    # Ya abierta: Sí
    flecha(ax, [(W, 6.3), (2.95, 6.3)], "Sí", 0, (0.12, 0.12))
    # ¿Presiona E? No → ¿Sale del área?
    flecha(ax, [(-W, 3.0), (-4.5 + W, 3.0)], "No", 0, (-0.75, 0.12))
    # ¿Sale? No → sigue mostrando el mensaje
    flecha(ax, [(-4.5, 3.0 + D), (-4.5, 4.65), (-1.85 - 0.25, 4.65)], "No", 0, (0.12, 0.15))
    # ¿Sale? Sí → ocultar → inicio
    flecha(ax, [(-4.5 - W, 3.0), (-8.3 + 1.3, 3.0)], "Sí", 0, (-0.6, 0.12))
    flecha(ax, [(-8.3, 3.0 + 0.475), (-8.3, 12.0), (-2.7, 12.0)])

    # Carril del interruptor
    ax.add_patch(FancyBboxPatch((6.85, -0.85), 4.3, 6.75, boxstyle="round,pad=0.05,rounding_size=0.3",
                                fc="#f5eef8", ec="#8e44ad", lw=1.2, ls="--", zorder=0))
    ax.text(9.0, 5.55, "Interruptor (sala del interruptor)", ha="center", fontsize=10.5, fontweight="bold", color="#6c3483")
    caja(ax, 9.0, 4.45, "Jugador presiona E\nsobre el interruptor", w=3.7, color="#f4ecf7", borde="#8e44ad")
    caja(ax, 9.0, 2.75, "Señal GameEvents:\nInterruptorActivado", w=3.7, color="#f4ecf7", borde="#8e44ad")
    caja(ax, 9.0, 1.05, "Puerta del jefe:\nbloqueada = false", w=3.7, color="#f4ecf7", borde="#8e44ad")
    caja(ax, 9.0, -0.3, "(antorcha: mismo esquema,\nE → enciende la luz)", w=3.7, h=0.75, color="#ffffff", borde="#bbbbbb")
    flecha(ax, [(9.0, 4.45 - 0.475), (9.0, 2.75 + 0.475)])
    flecha(ax, [(9.0, 2.75 - 0.475), (9.0, 1.05 + 0.475)])
    flecha(ax, [(9.0 + 1.85, 1.05), (11.6, 1.05), (11.6, 9.55), (0.85, 9.55), (0.85, 8.3 + 0.36)],
           ls="--", color="#8e44ad")
    ax.text(6.4, 9.68, "desbloquea", fontsize=10, color="#8e44ad", fontweight="bold")

    ax.set_xlim(-10.0, 12.2)
    ax.set_ylim(-3.9, 12.9)
    ax.axis("off")
    ax.set_title("Diagrama de flujo · Interacción con la puerta", fontsize=17, fontweight="bold", loc="left")
    fig.tight_layout()
    fig.savefig(OUT / archivo, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    dibujar_planta(BASEMENT_1, "planta_basement_1.png")
    dibujar_planta(BASEMENT_2, "planta_basement_2.png")
    dibujar_ficha("ficha_puerta.png")
    dibujar_flujo("flujo_interaccion.png")
    c1, c2 = contar(BASEMENT_1), contar(BASEMENT_2)
    print(f"Nivel: {ANCHO_NIVEL:g} × {ALTO_NIVEL:g} m · sala {PASO_X:g} × {PASO_Y:g} m (eje a eje)")
    print(f"{'Asset':26} {'B1':>4} {'B2':>4} {'Total':>6}")
    for k in c1:
        print(f"{k:26} {c1[k]:>4} {c2[k]:>4} {c1[k] + c2[k]:>6}")
    print("Instancias:", sum(c1.values()), sum(c2.values()), sum(c1.values()) + sum(c2.values()))
