# -*- coding: utf-8 -*-
"""
generar_animaciones_puerta.py - Animaciones de las puertas (Godot 4.7).

Escribe dos bibliotecas de animaciones (AnimationLibrary, en texto) en scenes/props/puerta/:

    animaciones_puerta.tres          puerta normal y puerta del jefe
        Abrir        0.70 s   la hoja se echa un poco atras (anticipacion), gira 90 grados pasandose 4 y asienta
        Cerrar       0.54 s   la hoja cae acelerando, golpea el marco, se pasa 1.5 grados y rebota
        Bloqueada    0.40 s   la hoja intenta abrir y tiembla cada vez menos (sala con enemigos, sin llave...)
        RESET                 puerta cerrada

    animaciones_puerta_tesoro.tres   puerta de la sala del tesoro: lo mismo y ademas la llave
        Desbloquear  1.65 s   Isaac usa una llave: la llave de la hoja se agranda y brilla, gira 360 grados, hace
                              "clic" (la hoja da un tiron), se esfuma hacia arriba y la hoja abre. Termina ABIERTA
                              y con la llave oculta (como en el juego original, el candado desaparece para siempre).
        Bloqueada    0.45 s   Isaac no tiene llave: tiembla la hoja y se sacude la llave
        (Abrir, Cerrar y RESET incluyen tambien la llave y las luces en su pose de reposo)

Que mueve cada pista (rutas relativas al AnimationPlayer, que cuelga de la raiz "Puerta"):
    Hoja                                   AnimatableBody3D con la colision de la hoja: es lo que empuja a Isaac
    Modelo/Puerta_Hoja                     la malla importada del .blend (misma rotacion que la anterior)
    Modelo/Puerta_Hoja/Puerta_Llave        la llave de oro (solo en puerta_tesoro.blend)
    DestelloFrente, DestelloAtras          OmniLight3D dorados a cada lado de la hoja (solo en la del tesoro)

Las claves de la hoja son pocas: gira en un solo eje, asi que Godot interpola exacto entre ellas. La llave se
hornea a 60 claves por segundo porque gira sobre SU centro y no sobre el origen de la hoja: la posicion se
compensa en cada clave (pos = P - R*S*P) y Godot interpola la posicion en linea recta entre claves, asi que
cuantas mas claves, menos se desvia el centro (verificar() comprueba que no pasa de 2 cm).

Las curvas de aceleracion usan el campo "transicion" de Godot: es la curva del tramo que SALE de esa clave
(1 = lineal, > 1 acelera, entre 0 y 1 frena al final, menor que -1 arranca y frena suave).

Uso, desde la raiz del repositorio (no necesita Godot ni Blender):
    python tools/godot/generar_animaciones_puerta.py
    python tools/godot/generar_animaciones_puerta.py --grafica curvas.png     (necesita matplotlib)
"""
import argparse
import math
import os

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DIR_SALIDA = os.path.join(RAIZ, "scenes", "props", "puerta")

# ------------------------------------------------------------------ parametros (metros, grados, segundos)
ABIERTA = 90.0                      # lo que gira la hoja al abrir; positivo = hacia -Z (en Blender, +Z)
PIVOTE_LLAVE = (0.6, 1.4355, 0.0)   # centro de la llave en coordenadas de la hoja (la bisagra es el origen)
HZ_LLAVE = 60                       # claves por segundo de la llave
DESTELLO_MAX = 4.0                  # energia maxima de la luz dorada al desbloquear
T_ABRE = 0.95                       # en Desbloquear: cuando empieza a abrir la hoja

HOJA_FISICA = "Hoja"
HOJA_MALLA = "Modelo/Puerta_Hoja"
LLAVE = "Modelo/Puerta_Hoja/Puerta_Llave"
LUCES = ("DestelloFrente", "DestelloAtras")

# Claves de la hoja: (segundo, grados, transicion del tramo que sale de esa clave)
ABRIR = [(0.00, 0.0, -2.0),               # anticipacion: se echa 4 grados hacia atras...
         (0.10, -4.0, -2.0),              # ...y sale con un arranque suave
         (0.55, ABIERTA + 4.0, 0.5),      # se pasa del tope 4 grados
         (0.70, ABIERTA, 1.0)]            # y asienta frenando
CERRAR = [(0.00, ABIERTA, 2.0),           # cae acelerando
          (0.38, -1.5, 0.5),              # golpe contra el marco
          (0.46, 1.0, 0.5),               # rebote
          (0.54, 0.0, 1.0)]
TEMBLOR = [(0.00, 0.0, -2.0), (0.05, 2.5, -2.0), (0.12, -1.8, -2.0), (0.19, 1.2, -2.0),
           (0.26, -0.7, -2.0), (0.33, 0.3, -2.0), (0.40, 0.0, 1.0)]
DESBLOQUEAR = ([(0.00, 0.0, 1.0), (0.68, 0.0, 0.5),   # quieta mientras la llave gira
                (0.74, -3.0, -2.0),                    # "clic": un tiron hacia atras...
                (0.80, 0.0, 1.0)]                      # ...y vuelve
               + [(t + T_ABRE, g, tr) for t, g, tr in ABRIR])


# ------------------------------------------------------------------ curvas de Godot
def ease(x, curva):
    """Igual a ease() de Godot (@GlobalScope): es la que aplica Animation a la transicion de cada clave."""
    x = max(0.0, min(1.0, x))
    if curva > 0:
        return 1 - (1 - x) ** (1 / curva) if curva < 1 else x ** curva
    if curva < 0:
        if x < 0.5:
            return ((x * 2) ** -curva) * 0.5
        return (1 - (1 - (x - 0.5) * 2) ** -curva) * 0.5 + 0.5
    return 0.0


def mezclar(a, b, c):
    if isinstance(a, tuple):
        return tuple(x + (y - x) * c for x, y in zip(a, b))
    return a + (b - a) * c


def tramos(t, inicial, segs):
    """Valor en t de una curva hecha de tramos (t0, t1, desde, hasta, curva); entre tramos se queda quieta."""
    v = inicial
    for t0, t1, a, b, c in segs:
        if t < t0:
            return v
        if t <= t1:
            return a + (b - a) * ease((t - t0) / (t1 - t0), c)
        v = b
    return v


# ------------------------------------------------------------------ pistas y animaciones
def num(v):
    s = f"{v:.5f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def texto_valor(tipo, v):
    if tipo == "vec3":
        return "Vector3(%s, %s, %s)" % tuple(num(x) for x in v)
    if tipo == "float":
        # Siempre con punto decimal: en un .tres "0" se lee como entero y "2.5" como decimal. Una pista con valores
        # mezclados se toma como entera y Godot REDONDEA lo que interpola (un destello de 2.5 llega como 3).
        s = num(v)
        return s if "." in s else s + ".0"
    return "true" if v else "false"


class Pista:
    """Pista de valores de una propiedad. claves = [(segundo, valor, transicion)]."""

    def __init__(self, ruta, tipo, claves, discreta=False):
        self.ruta, self.tipo, self.discreta = ruta, tipo, discreta
        self.claves = sorted(((round(t, 5), v, tr) for t, v, tr in claves), key=lambda k: k[0])

    def valor(self, t):
        """Valor que le daria Godot en el segundo t (interpolacion lineal con la curva de cada tramo)."""
        ks = self.claves
        if t <= ks[0][0]:
            return ks[0][1]
        if t >= ks[-1][0]:
            return ks[-1][1]
        for (t0, v0, tr), (t1, v1, _) in zip(ks, ks[1:]):
            if t0 <= t < t1:
                if self.discreta:
                    return v0
                c = (t - t0) / (t1 - t0)
                return mezclar(v0, v1, ease(c, tr) if tr != 1.0 else c)

    def texto(self, i):
        tiempos = ", ".join(num(k[0]) for k in self.claves)
        trans = ", ".join(num(k[2]) for k in self.claves)
        valores = ", ".join(texto_valor(self.tipo, k[1]) for k in self.claves)
        return (f'tracks/{i}/type = "value"\n'
                f'tracks/{i}/imported = false\n'
                f'tracks/{i}/enabled = true\n'
                f'tracks/{i}/path = NodePath("{self.ruta}")\n'
                f'tracks/{i}/interp = 1\n'
                f'tracks/{i}/loop_wrap = true\n'
                f'tracks/{i}/keys = {{\n'
                f'"times": PackedFloat32Array({tiempos}),\n'
                f'"transitions": PackedFloat32Array({trans}),\n'
                f'"update": {1 if self.discreta else 0},\n'
                f'"values": [{valores}]\n'
                f'}}\n')


class Animacion:
    def __init__(self, nombre, largo, pistas):
        self.nombre, self.largo, self.pistas = nombre, largo, pistas

    def pista(self, ruta):
        return next(p for p in self.pistas if p.ruta == ruta)

    def texto(self):
        cab = (f'[sub_resource type="Animation" id="Animation_{self.nombre}"]\n'
               f'resource_name = "{self.nombre}"\nlength = {num(self.largo)}\n')
        return cab + "".join(p.texto(i) for i, p in enumerate(self.pistas)) + "\n"


def texto_libreria(anims):
    out = '[gd_resource type="AnimationLibrary" format=3]\n\n'
    out += "".join(a.texto() for a in anims)
    out += "[resource]\n_data = {\n"
    out += ",\n".join(f'&"{a.nombre}": SubResource("Animation_{a.nombre}")' for a in anims)
    return out + "\n}\n"


def pistas_hoja(claves_grados):
    """La hoja se anima dos veces con las mismas claves: el cuerpo fisico y la malla del modelo."""
    claves = [(t, (0.0, math.radians(g), 0.0), tr) for t, g, tr in claves_grados]
    return [Pista(HOJA_FISICA + ":rotation", "vec3", claves),
            Pista(HOJA_MALLA + ":rotation", "vec3", claves)]


# ------------------------------------------------------------------ la llave: girar sobre su centro
def matriz_llave(ry_grados, rz_grados):
    """Basis de Godot para la rotacion Euler (0, ry, rz): orden YXZ, o sea Ry * Rz cuando rx = 0."""
    cy, sy = math.cos(math.radians(ry_grados)), math.sin(math.radians(ry_grados))
    cz, sz = math.cos(math.radians(rz_grados)), math.sin(math.radians(rz_grados))
    ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    return [[sum(ry[i][k] * rz[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def transformar_llave(s, ry, rz, dy):
    """(posicion, rotacion, escala) del nodo Puerta_Llave para que gire (ry, rz grados) y se agrande (s) sobre su
    centro P, y ademas suba dy metros. El nodo gira sobre su origen (la bisagra), asi que se compensa:
    pos = P - R*S*P (+ dy en Y)."""
    b = matriz_llave(ry, rz)
    p = PIVOTE_LLAVE
    bp = [s * sum(b[i][j] * p[j] for j in range(3)) for i in range(3)]
    return ((p[0] - bp[0], p[1] - bp[1] + dy, p[2] - bp[2]),
            (0.0, math.radians(ry), math.radians(rz)), (s, s, s))


def pistas_llave(pose, t0, t1):
    """Hornea posicion, rotacion y escala de la llave: pose(t) -> (escala, giro Y, giro Z, subida)."""
    n = max(1, round((t1 - t0) * HZ_LLAVE))
    pos, rot, esc = [], [], []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        p, r, e = transformar_llave(*pose(t))
        pos.append((t, p, 1.0))
        rot.append((t, r, 1.0))
        esc.append((t, e, 1.0))
    return [Pista(LLAVE + ":position", "vec3", pos), Pista(LLAVE + ":rotation", "vec3", rot),
            Pista(LLAVE + ":scale", "vec3", esc)]


def pose_desbloquear(t):
    s = tramos(t, 1.0, [(0.00, 0.18, 1.0, 1.4, 0.5),      # se agranda de golpe (pop)
                        (0.18, 0.68, 1.4, 1.25, -1.5),     # se encoge un poco mientras gira
                        (0.68, 0.80, 1.25, 1.65, 0.5),     # "clic": otro pop
                        (0.80, 1.00, 1.65, 0.001, 2.0)])   # y se esfuma acelerando
    ry = tramos(t, 0.0, [(0.18, 0.68, 0.0, 360.0, -2.0)])  # una vuelta completa
    rz = tramos(t, 0.0, [(0.80, 1.00, 0.0, 25.0, 0.5)])    # se ladea al irse
    dy = tramos(t, 0.0, [(0.80, 1.00, 0.0, 0.25, 0.5)])    # y sube 25 cm
    return s, ry, rz, dy


def pose_sacudida(t, largo=0.45):
    """Llave sacudida (sin llave en el inventario): vaiven en el plano de la hoja que se apaga, y un pulso."""
    rz = 16.0 * math.exp(-7.0 * t) * (1 - t / largo) * math.sin(2 * math.pi * 9.0 * t)
    s = 1.0 + (0.15 * math.sin(math.pi * t / 0.30) if t < 0.30 else 0.0)
    return s, 0.0, rz, 0.0


def pistas_luces(claves):
    return [Pista(f"{luz}:light_energy", "float", claves) for luz in LUCES]


def pistas_reposo_llave():
    return [Pista(LLAVE + ":position", "vec3", [(0.0, (0.0, 0.0, 0.0), 1.0)]),
            Pista(LLAVE + ":rotation", "vec3", [(0.0, (0.0, 0.0, 0.0), 1.0)]),
            Pista(LLAVE + ":scale", "vec3", [(0.0, (1.0, 1.0, 1.0), 1.0)]),
            Pista(LLAVE + ":visible", "bool", [(0.0, True, 1.0)], discreta=True)] + \
           pistas_luces([(0.0, 0.0, 1.0)])


# ------------------------------------------------------------------ las bibliotecas
def animaciones_basicas():
    return [Animacion("RESET", 0.001, pistas_hoja([(0.0, 0.0, 1.0)])),
            Animacion("Abrir", 0.70, pistas_hoja(ABRIR)),
            Animacion("Cerrar", 0.54, pistas_hoja(CERRAR)),
            Animacion("Bloqueada", 0.40, pistas_hoja(TEMBLOR))]


def animaciones_tesoro():
    reset = Animacion("RESET", 0.001, pistas_hoja([(0.0, 0.0, 1.0)]) + pistas_reposo_llave())
    desbloquear = Animacion(
        "Desbloquear", T_ABRE + 0.70,
        pistas_hoja(DESBLOQUEAR)
        + pistas_llave(pose_desbloquear, 0.0, 1.00)
        + [Pista(LLAVE + ":visible", "bool", [(0.0, True, 1.0), (1.00, False, 1.0)], discreta=True)]
        + pistas_luces([(0.00, 0.0, 0.5), (0.18, 0.625 * DESTELLO_MAX, 1.0), (0.68, 0.875 * DESTELLO_MAX, 0.5),
                        (0.74, DESTELLO_MAX, 0.5), (1.10, 0.0, 1.0)]))
    bloqueada = Animacion("Bloqueada", 0.45,
                          pistas_hoja(TEMBLOR) + pistas_llave(pose_sacudida, 0.0, 0.45))
    return [reset, Animacion("Abrir", 0.70, pistas_hoja(ABRIR)), Animacion("Cerrar", 0.54, pistas_hoja(CERRAR)),
            bloqueada, desbloquear]


# ------------------------------------------------------------------ verificacion (simula lo que hara Godot)
def centro_llave(a, t):
    """Centro de la llave en coordenadas de la hoja, leido de las pistas ya interpoladas como lo haria Godot."""
    pos = a.pista(LLAVE + ":position").valor(t)
    rot = a.pista(LLAVE + ":rotation").valor(t)
    esc = a.pista(LLAVE + ":scale").valor(t)
    b = matriz_llave(math.degrees(rot[1]), math.degrees(rot[2]))
    p = PIVOTE_LLAVE
    return tuple(pos[i] + esc[0] * sum(b[i][j] * p[j] for j in range(3)) for i in range(3))


def verificar(librerias):
    def comprobar(cond, msg):
        assert cond, "FALLA: " + msg

    for nombre, anims in librerias.items():
        for a in anims:
            for p in a.pistas:
                ts = [k[0] for k in p.claves]
                comprobar(all(y > x for x, y in zip(ts, ts[1:])), f"{a.nombre} {p.ruta}: tiempos no crecientes")
                comprobar(ts[-1] <= a.largo + 1e-9, f"{a.nombre} {p.ruta}: clave despues del final")
    bas = {a.nombre: a for a in librerias["animaciones_puerta.tres"]}
    tes = {a.nombre: a for a in librerias["animaciones_puerta_tesoro.tres"]}
    hoja = lambda a, t: math.degrees(a.pista(HOJA_FISICA + ":rotation").valor(t)[1])
    barrido = lambda a: [i * a.largo / 600 for i in range(601)]

    for lib in (bas, tes):
        a = lib["Abrir"]
        comprobar(abs(hoja(a, a.largo) - ABIERTA) < 1e-6, "Abrir no termina en 90 grados")
        comprobar(min(hoja(a, t) for t in barrido(a)) >= -4.2, "Abrir: la anticipacion pasa de 4 grados")
        comprobar(max(hoja(a, t) for t in barrido(a)) <= ABIERTA + 4.2, "Abrir: se pasa mas de 4 grados")
        a = lib["Cerrar"]
        comprobar(abs(hoja(a, 0) - ABIERTA) < 1e-6 and abs(hoja(a, a.largo)) < 1e-6, "Cerrar no va de 90 a 0")
        comprobar(min(hoja(a, t) for t in barrido(a)) >= -1.6, "Cerrar: se pasa del marco mas de 1.5 grados")
        a = lib["Bloqueada"]
        comprobar(abs(hoja(a, 0)) < 1e-6 and abs(hoja(a, a.largo)) < 1e-6, "Bloqueada no vuelve a 0")
        comprobar(max(abs(hoja(a, t)) for t in barrido(a)) <= 2.6, "Bloqueada: tiembla mas de 2.5 grados")
        for a in lib.values():
            comprobar(len({p.ruta for p in a.pistas}) == len(a.pistas), f"{a.nombre}: ruta repetida")
            comprobar(abs(hoja(a, 0) - math.degrees(a.pista(HOJA_MALLA + ":rotation").valor(0)[1])) < 1e-9,
                      f"{a.nombre}: cuerpo y malla no coinciden")
            comprobar(hoja(a, a.largo / 3) == math.degrees(a.pista(HOJA_MALLA + ":rotation").valor(a.largo / 3)[1]),
                      f"{a.nombre}: cuerpo y malla se separan")

    # El reposo de RESET tiene que ser el primer fotograma de las animaciones que parten de la puerta cerrada
    reset = tes["RESET"]
    for nombre in ("Abrir", "Bloqueada", "Desbloquear"):
        for p in tes[nombre].pistas:
            ruta_reset = next((r for r in reset.pistas if r.ruta == p.ruta), None)
            comprobar(ruta_reset is not None, f"{nombre}: {p.ruta} no esta en RESET")
            v0, vr = p.valor(0.0), ruta_reset.valor(0.0)
            ok = (all(abs(x - y) < 1e-9 for x, y in zip(v0, vr)) if isinstance(v0, tuple) else
                  (abs(v0 - vr) < 1e-9 if isinstance(v0, float) else v0 == vr))
            comprobar(ok, f"{nombre}: {p.ruta} no arranca en la pose de RESET")

    d = tes["Desbloquear"]
    comprobar(abs(hoja(d, d.largo) - ABIERTA) < 1e-6, "Desbloquear no termina con la puerta abierta")
    comprobar(d.pista(LLAVE + ":visible").valor(d.largo) is False, "Desbloquear deja la llave visible")
    comprobar(all(abs(d.pista(f"{l}:light_energy").valor(d.largo)) < 1e-9 for l in LUCES), "las luces quedan prendidas")
    comprobar(max(abs(hoja(d, t)) for t in barrido(d) if t < T_ABRE) <= 3.1, "la hoja se mueve de mas antes de abrir")

    peor = 0.0                     # desvio del centro de la llave respecto de donde deberia estar
    for i in range(601):
        t = i / 600
        s, ry, rz, dy = pose_desbloquear(t)
        c = centro_llave(d, t)
        esperado = (PIVOTE_LLAVE[0], PIVOTE_LLAVE[1] + dy, PIVOTE_LLAVE[2])
        peor = max(peor, math.dist(c, esperado))
    comprobar(peor < 0.02, f"la llave se desvia {peor * 100:.1f} cm de su centro al girar")
    b = tes["Bloqueada"]
    peor_b = max(math.dist(centro_llave(b, i / 450 * 0.45), PIVOTE_LLAVE) for i in range(451))
    comprobar(peor_b < 0.02, f"la llave sacudida se desvia {peor_b * 100:.1f} cm")

    import re
    for nombre, anims in librerias.items():
        for a in anims:
            for p in a.pistas:
                if p.tipo == "float":
                    vals = re.search(r"\[(.*)\]", "[" + ", ".join(texto_valor("float", k[1]) for k in p.claves) + "]").group(1)
                    comprobar(all("." in v for v in vals.split(", ")),
                              f"{a.nombre} {p.ruta}: hay un valor decimal escrito como entero ({vals})")

    print("Verificacion correcta:")
    for nombre, lib in (("puerta", bas), ("puerta del tesoro", tes)):
        for a in lib.values():
            print(f"  {nombre:18s} {a.nombre:12s} {a.largo:5.2f} s  {len(a.pistas):2d} pistas  "
                  f"{sum(len(p.claves) for p in a.pistas):4d} claves")
    print(f"  desvio maximo del centro de la llave al girar: {peor * 100:.2f} cm; sacudida: {peor_b * 100:.2f} cm")


# ------------------------------------------------------------------ grafica de control (opcional)
def graficar(librerias, salida):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle

    bas = {a.nombre: a for a in librerias["animaciones_puerta.tres"]}
    tes = {a.nombre: a for a in librerias["animaciones_puerta_tesoro.tres"]}
    d = tes["Desbloquear"]
    ang = lambda a, t: a.pista(HOJA_FISICA + ":rotation").valor(t)[1]
    rotY = lambda g, v: (v[0] * math.cos(g) + v[2] * math.sin(g), v[1], -v[0] * math.sin(g) + v[2] * math.cos(g))

    def a_puerta(a, t, q):
        """Punto q (coordenadas de la llave) llevado al marco de la puerta, con la hoja girada."""
        pos = a.pista(LLAVE + ":position").valor(t)
        esc = a.pista(LLAVE + ":scale").valor(t)[0]
        r = a.pista(LLAVE + ":rotation").valor(t)
        b = matriz_llave(math.degrees(r[1]), math.degrees(r[2]))
        hoja = tuple(pos[i] + esc * sum(b[i][j] * q[j] for j in range(3)) for i in range(3))
        x, y, z = rotY(ang(a, t), hoja)
        return x - 0.6, y, z

    fig = plt.figure(figsize=(17, 11))
    gs = fig.add_gridspec(4, 8, hspace=0.5, wspace=0.4)

    ax = fig.add_subplot(gs[0, 0:4])
    for etiqueta, a in (("Abrir", bas["Abrir"]), ("Cerrar", bas["Cerrar"]), ("Bloqueada", bas["Bloqueada"]),
                        ("Desbloquear (tesoro)", d)):
        ts = [i * a.largo / 400 for i in range(401)]
        ax.plot(ts, [math.degrees(ang(a, t)) for t in ts], label=etiqueta)
    ax.set_title("Giro de la hoja (grados)")
    ax.set_xlabel("segundos")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    ax = fig.add_subplot(gs[0, 4:8])
    ts = [i * 1.1 / 400 for i in range(401)]
    ax.plot(ts, [pose_desbloquear(t)[0] for t in ts], label="escala de la llave")
    ax.plot(ts, [pose_desbloquear(t)[1] / 360 for t in ts], label="giro Y (vueltas)")
    ax.plot(ts, [d.pista(f"{LUCES[0]}:light_energy").valor(t) / DESTELLO_MAX for t in ts], label="luz (0-1)")
    ax.plot(ts, [100 * math.dist(centro_llave(d, min(t, 1.0)),
                                 (PIVOTE_LLAVE[0], PIVOTE_LLAVE[1] + pose_desbloquear(t)[3], 0)) for t in ts],
            label="desvio del centro (cm)")
    ax.set_title("Desbloquear: la llave")
    ax.set_xlabel("segundos")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    instantes = [0.0, 0.18, 0.35, 0.50, 0.74, 0.90, 1.25, 1.65]
    for k, t in enumerate(instantes):
        # vista de planta (X horizontal, Z vertical hacia abajo = hacia la camara)
        ax = fig.add_subplot(gs[1:3, k])
        ax.set_title(f"t = {t:.2f} s", fontsize=9)
        ax.add_patch(Rectangle((-0.75, -0.25), 0.15, 0.5, color="#999"))
        ax.add_patch(Rectangle((0.6, -0.25), 0.15, 0.5, color="#999"))
        g = ang(d, t)
        ax.plot([-0.6, -0.6 + 1.2 * math.cos(g)], [0, -1.2 * math.sin(g)], lw=6, color="#8a5a2b", solid_capstyle="butt")
        if d.pista(LLAVE + ":visible").valor(t):
            p0, p1 = a_puerta(d, t, (PIVOTE_LLAVE[0] - 0.163, PIVOTE_LLAVE[1], 0)), \
                a_puerta(d, t, (PIVOTE_LLAVE[0] + 0.163, PIVOTE_LLAVE[1], 0))
            ax.plot([p0[0], p1[0]], [p0[2], p1[2]], lw=3, color="#e0a800")
        ax.set_xlim(-1.0, 1.0)
        ax.set_ylim(0.6, -1.5)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        # vista de frente de la llave
        ax = fig.add_subplot(gs[3, k])
        ax.add_patch(Rectangle((-0.6 + 0.0, 0), 1.2 * max(math.cos(g), 0.02), 2.3, fill=False, ec="#8a5a2b"))
        if d.pista(LLAVE + ":visible").valor(t):
            pts = [a_puerta(d, t, (PIVOTE_LLAVE[0] + sx * 0.163, PIVOTE_LLAVE[1] + sy * 0.2565, 0))
                   for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            ax.add_patch(Polygon([(p[0], p[1]) for p in pts], color="#e0a800", alpha=0.8))
        ax.set_xlim(-0.9, 0.9)
        ax.set_ylim(0.6, 2.6)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle("Puerta del tesoro - Desbloquear: planta (fila de arriba) y frente de la llave (fila de abajo)")
    fig.savefig(salida, dpi=80, bbox_inches="tight")
    print("Grafica:", salida)


def main():
    ap = argparse.ArgumentParser(description="Genera las animaciones de las puertas de TheSaac.")
    ap.add_argument("--grafica", help="PNG con las curvas y fotogramas de control (necesita matplotlib)")
    args = ap.parse_args()
    os.makedirs(DIR_SALIDA, exist_ok=True)
    librerias = {"animaciones_puerta.tres": animaciones_basicas(),
                 "animaciones_puerta_tesoro.tres": animaciones_tesoro()}
    for nombre, anims in librerias.items():
        ruta = os.path.join(DIR_SALIDA, nombre)
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto_libreria(anims))
        print("Escrito", os.path.relpath(ruta, RAIZ))
    verificar(librerias)
    if args.grafica:
        graficar(librerias, args.grafica)


if __name__ == "__main__":
    main()
