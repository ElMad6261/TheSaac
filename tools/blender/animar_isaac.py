# -*- coding: utf-8 -*-
"""
animar_isaac.py - Ciclo de caminata y pose quieta de Isaac (Blender 5.1).

Aplica al rig FK de isaac.blend las tecnicas del Taller 07 "El ciclo de caminata":
  1. Periodo de 24 fotogramas = 2 pasos de 12. Marcadores cada 3 fotogramas con las fases
     Contacto / Bajo / Pase / Alto (izquierdo y derecho).
  2. Animacion "en el sitio" (cinta de correr): el avance lo da el juego (CharacterBody3D). El pie de
     apoyo retrocede a velocidad constante (tramos diagonales de la curva F) y el ciclo termina
     exactamente como empezo, asi que no hace falta "Repetir con desplazamiento".
  3. Pelvis: bote en Z (periodo de 12), balanceo en X (senoide), giro de cadera y pecho en sentidos
     contrarios e inclinacion de cadera desfasada 6 fotogramas.
  4. Pies: rodaje del pie (talon -> plano -> punta), elevacion con doble joroba en el balanceo, pie
     derecho = pie izquierdo desfasado 12 fotogramas y rodilla siempre flexionada (sin "knee pop").
     Isaac no tiene huesos IK: el script resuelve una IK de dos huesos por fotograma y deja solo claves
     de rotacion FK en UpperLeg / LowerLeg / Foot.
  5. Brazos FK: balanceo opuesto a las piernas, con retraso hombro > codo > mano.
  6. Todo ciclico: modificador Cycles en cada curva F, accion ciclica con rango manual 0-24 y
     Cycle-Aware Keying activado.

La cabeza (hueso Head) NO se anima aqui: el cuello (Neck) la mantiene estable y Godot la gira con las
flechas (ver PlayerController.cs).

Uso: abrir assets/blend/isaac.blend en Blender y ejecutar este script (Scripting > Run Script).
Es repetible: borra las acciones "Caminar-loop" y "Quieto-loop" anteriores y las vuelve a generar.
Para cambiar el estilo basta con tocar los parametros de abajo (metros y radianes).
"""
import bpy
import math
from mathutils import Vector, Matrix

# ====================================================================== PARAMETROS
NOMBRE_ARMADURA = "Isaac"
FPS = 24
CICLO = 24            # fotogramas del ciclo completo (dos pasos)
PASO_FR = 12          # fotogramas de un paso

ACCION_CAMINAR = "Caminar-loop"   # el sufijo "-loop" hace que Godot la importe en bucle
ACCION_QUIETO = "Quieto-loop"

# --- Caminar
LONG_PASO = 0.12                  # m que avanza el cuerpo en un paso (zancada = 2 x LONG_PASO)
AGACHE = 0.010                    # cadera mas baja que en reposo: las piernas nunca quedan rectas
BOTE = {0: -0.002, 3: -0.008, 6: 0.0, 9: 0.003}     # Z de la pelvis: Contacto / Bajo / Pase / Alto
BALANCEO = 0.006                  # m de vaiven lateral de la pelvis (maximo en los Pase)
GIRO_CADERA = math.radians(7)     # giro de la cadera en los Contacto
GIRO_PECHO = math.radians(4)      # giro del pecho, en sentido contrario
INCLINA_CADERA = math.radians(3)  # inclinacion lateral de la cadera, desfasada 6 fotogramas
ANG_TALON = math.radians(12)      # punta arriba al apoyar el talon (Contacto)
ANG_PUNTA = math.radians(10)      # talon arriba al despegar la punta
ELEVA = (0.014, 0.006, 0.011)     # elevacion del pie: joroba (15), valle (18), joroba (21)
BRAZO = math.radians(24)          # balanceo del hombro
CODO = math.radians(12)           # balanceo del codo (retrasado 2 fotogramas)
MANO = math.radians(8)            # balanceo de la mano (retrasada 4 fotogramas)

# --- Quieto (respiracion)
Q_AGACHE = 0.006
Q_RESPIRA = 0.003
Q_PECHO = math.radians(1.5)

# --- Geometria del pie respecto al tobillo en reposo: (dy hacia atras, dz hacia arriba)
TALON_REL = (0.063, -0.050)
BOLA_REL = (-0.099, -0.050)
PUNTA_REL = (-0.127, -0.048)

MARCADORES = ["Contacto izquierdo", "Bajo izquierdo", "Pase izquierdo", "Alto izquierdo",
              "Contacto derecho", "Bajo derecho", "Pase derecho", "Alto derecho",
              "Contacto izquierdo"]

# ====================================================================== MATEMATICA
def rx(a): return Matrix.Rotation(a, 3, 'X')
def ry(a): return Matrix.Rotation(a, 3, 'Y')
def rz(a): return Matrix.Rotation(a, 3, 'Z')

def suave(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)

def rodar(v, phi):
    """Gira el vector (dy, dz) en el plano lateral. phi > 0 = punta del pie hacia arriba."""
    c, s = math.cos(phi), math.sin(phi)
    return (v[0] * c + v[1] * s, -v[0] * s + v[1] * c)

def a4(m3, loc=None):
    m = m3.to_4x4()
    if loc is not None:
        m.translation = loc
    return m

# ====================================================================== RIG
ARM = None
HUESOS = None
REST = {}

def preparar(arm):
    global ARM, HUESOS, REST
    ARM = arm
    HUESOS = arm.data.bones
    REST = {b.name: b.matrix_local.copy() for b in HUESOS}

def calcular_pose(bases):
    """Cinematica directa: pose de cada hueso en el espacio de la armadura.
    bases = {hueso: Matrix 4x4 con la pose local (lo que se anima)}."""
    pose = {}
    def pose_de(n):
        if n in pose:
            return pose[n]
        b = HUESOS[n]
        base = bases.get(n, Matrix.Identity(4))
        if b.parent is None:
            pose[n] = REST[n] @ base
        else:
            rel = REST[b.parent.name].inverted() @ REST[n]
            pose[n] = pose_de(b.parent.name) @ rel @ base
        return pose[n]
    for b in HUESOS:
        pose_de(b.name)
    return pose

def base_en_ejes(nombre, R_eje, loc=None):
    """Pose local que equivale a girar el hueso con R_eje (ejes del mundo en reposo)."""
    Rr = REST[nombre].to_3x3()
    Ri = Rr.inverted()
    return a4(Ri @ R_eje @ Rr, None if loc is None else Ri @ loc)

def marco(y_dir, x_ref):
    """Rotacion con el eje Y del hueso en y_dir y el eje X lo mas cerca posible de x_ref."""
    y = y_dir.normalized()
    x = (x_ref - y * x_ref.dot(y)).normalized()
    z = x.cross(y)
    return Matrix((x, y, z)).transposed()

def ik_pierna(H, A, l1, l2, polo):
    """IK analitica de dos huesos: devuelve (rodilla, tobillo alcanzable)."""
    v = A - H
    d = min(max(v.length, abs(l1 - l2) + 1e-5), (l1 + l2) * 0.999)
    u = v.normalized()
    a = (l1 * l1 - l2 * l2 + d * d) / (2.0 * d)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    pp = polo - u * polo.dot(u)
    pp.normalize()
    return H + u * a + pp * h, H + u * d

# ====================================================================== TRAYECTORIA DEL PIE
def crear_tobillo_caminar(ank_y, ank_z):
    """Trayectoria del tobillo (en el marco del cuerpo, cinta de correr) de UN pie.
    tau en fotogramas: 0-12 apoyo (talon, plano, punta), 12-24 balanceo. Devuelve (y, z, phi)."""
    vb = LONG_PASO / PASO_FR           # el pie de apoyo retrocede vb por fotograma
    y6 = ank_y                         # al final de la fase plana el tobillo esta bajo la cadera

    def phi_apoyo(t):
        if t < 3:
            return ANG_TALON * (1.0 - suave(t / 3.0))
        if t < 6:
            return 0.0
        return -ANG_PUNTA * suave((t - 6.0) / 6.0)

    def tobillo_apoyo(t):
        p = phi_apoyo(t)
        if t < 3:                      # rueda sobre el talon, que no se mueve en el mundo
            yh3 = (y6 - 3 * vb) + TALON_REL[0]
            r = rodar(TALON_REL, p)
            return (yh3 + vb * (t - 3) - r[0], -r[1], p)
        if t < 6:                      # pie plano
            return (y6 + vb * (t - 6), -TALON_REL[1], 0.0)
        yb6 = y6 + BOLA_REL[0]         # rueda sobre la punta, que no se mueve en el mundo
        r = rodar(BOLA_REL, p)
        return (yb6 + vb * (t - 6) - r[0], -r[1], p)

    a12 = tobillo_apoyo(12.0)
    a0 = tobillo_apoyo(0.0)

    def elevacion(t):
        pts = [(12, 0.0), (15, ELEVA[0]), (18, ELEVA[1]), (21, ELEVA[2]), (24, 0.0)]
        for i in range(4):
            if pts[i][0] <= t <= pts[i + 1][0]:
                s = suave((t - pts[i][0]) / 3.0)
                return pts[i][1] * (1.0 - s) + pts[i + 1][1] * s
        return 0.0

    def tobillo(tau):
        t = tau % CICLO
        if t < PASO_FR:
            return tobillo_apoyo(t)
        u = (t - PASO_FR) / float(PASO_FR)
        s = suave(u)
        phi = -ANG_PUNTA + (ANG_PUNTA + ANG_TALON) * suave(u)
        y = a12[0] + (a0[0] - a12[0]) * s
        z = a12[1] + (a0[1] - a12[1]) * s + elevacion(t)
        bajo = min(z + rodar(q, phi)[1] for q in (TALON_REL, BOLA_REL, PUNTA_REL))
        if bajo < 0.0:                 # que ningun punto del pie atraviese el suelo
            z -= bajo
        return (y, z, phi)
    return tobillo

def crear_tobillo_quieto(ank_y, ank_z):
    return lambda tau: (ank_y, ank_z, 0.0)

# ====================================================================== TORSO (claves cada 3 fotogramas)
def torso_caminar(t):
    w = 2.0 * math.pi * t / CICLO
    yaw = -GIRO_CADERA * math.cos(w)               # lado izquierdo adelante en Contacto izquierdo
    roll = INCLINA_CADERA * math.sin(w)            # desfasada 6 fotogramas: maximo en los Pase
    d = Vector((BALANCEO * math.sin(w), 0.0, -AGACHE + BOTE[int(round(t)) % PASO_FR]))
    rot = {
        'Hips': rz(yaw) @ ry(roll),
        'Spine': ry(-0.6 * roll),
        'Chest': rz(GIRO_PECHO * math.cos(w)) @ ry(-0.4 * roll),
    }
    for lado, signo in (('L', 1.0), ('R', -1.0)):
        for hueso, amp, retraso in (('UpperArm', BRAZO, 0), ('LowerArm', CODO, 2), ('Hand', MANO, 4)):
            adelante = -signo * amp * math.cos(2.0 * math.pi * (t - 3 - retraso) / CICLO)
            rot['%s.%s' % (hueso, lado)] = rx(-adelante)
    return rot, d

def torso_quieto(t):
    w = 2.0 * math.pi * t / CICLO
    d = Vector((0.0, 0.0, -Q_AGACHE + Q_RESPIRA * math.sin(w)))
    rot = {'Chest': rx(Q_PECHO * math.sin(w - 0.6))}
    for lado in ('L', 'R'):
        for hueso, retraso in (('UpperArm', 0), ('LowerArm', 2), ('Hand', 4)):
            rot['%s.%s' % (hueso, lado)] = rx(math.radians(1.2) * math.sin(2.0 * math.pi * (t - 3 - retraso) / CICLO))
    return rot, d

# ====================================================================== ANIMACION
def euler_de(base4, previo):
    m3 = base4.to_3x3()
    return m3.to_euler('XYZ', previo) if previo is not None else m3.to_euler('XYZ')

def construir_accion(nombre, torso_fn, tobillo_fn, fase_pie_derecho):
    scene = bpy.context.scene
    ad = ARM.animation_data or ARM.animation_data_create()
    ad.action = None
    vieja = bpy.data.actions.get(nombre)
    if vieja:
        bpy.data.actions.remove(vieja)
    accion = bpy.data.actions.new(nombre)
    slot = accion.slots.new(id_type='OBJECT', name=ARM.name)
    ad.action = accion
    ad.action_slot = slot

    pb = ARM.pose.bones
    for p in pb:
        p.location = (0, 0, 0)
        p.rotation_quaternion = (1, 0, 0, 0)
        p.rotation_euler = (0, 0, 0)
        p.scale = (1, 1, 1)
    for n in ('Hips', 'Spine', 'Chest', 'Neck', 'UpperArm.L', 'LowerArm.L', 'Hand.L', 'UpperArm.R',
              'LowerArm.R', 'Hand.R', 'UpperLeg.L', 'LowerLeg.L', 'Foot.L', 'UpperLeg.R', 'LowerLeg.R',
              'Foot.R'):
        pb[n].rotation_mode = 'XYZ'

    previos, primeros = {}, {}

    def poner(n, eul, loc=None, frame=0):
        p = pb[n]
        p.rotation_euler = eul
        p.keyframe_insert('rotation_euler', frame=frame, group=n)
        if loc is not None:
            p.location = loc
            p.keyframe_insert('location', frame=frame, group=n)

    # ---- Pasada 1: pelvis, torso, cuello y brazos, una clave cada 3 fotogramas
    for t in range(0, CICLO + 1, 3):
        rot, d = torso_fn(t)
        bases = {}
        for n, R in rot.items():
            bases[n] = base_en_ejes(n, R, d if n == 'Hips' else None)
        if 'Hips' not in bases:
            bases['Hips'] = base_en_ejes('Hips', Matrix.Identity(3), d)
        pose = calcular_pose(bases)
        # El cuello deshace el giro del torso: la cabeza queda estable y mirando al frente.
        rel = REST['Chest'].inverted() @ REST['Neck']
        base_cuello = (pose['Chest'] @ rel).to_3x3().inverted() @ REST['Neck'].to_3x3()
        bases['Neck'] = a4(base_cuello)
        for n, b in bases.items():
            if t == CICLO:
                eul, loc = primeros[n]
            else:
                eul = euler_de(b, previos.get(n))
                loc = b.translation.copy() if n == 'Hips' else None
                primeros[n] = (eul.copy(), loc.copy() if loc is not None else None) if t == 0 else primeros.get(n)
            previos[n] = eul
            poner(n, eul, loc, t)

    # ---- Pasada 2: piernas. IK de dos huesos por fotograma (pies plantados en el marco del cuerpo)
    lados = (('L', 0), ('R', fase_pie_derecho))
    longs = {l: (HUESOS['UpperLeg.' + l].length, HUESOS['LowerLeg.' + l].length) for l, _ in lados}
    polo = Vector((0.0, -1.0, 0.0))        # las rodillas apuntan hacia adelante (frente = -Y)
    valores0 = {}
    for f in range(0, CICLO + 1):
        if f == CICLO:
            for n, (eul) in valores0.items():
                poner(n, eul, None, f)
            break
        scene.frame_set(f)
        bpy.context.view_layer.update()
        Mh = pb['Hips'].matrix.copy()
        for lado, desfase in lados:
            sup, inf, pie = 'UpperLeg.' + lado, 'LowerLeg.' + lado, 'Foot.' + lado
            rel_sup = REST['Hips'].inverted() @ REST[sup]
            M_sup = Mh @ rel_sup
            H = M_sup.translation
            tx = REST[pie].translation.x
            ay, az, phi = tobillo_fn[lado](f + desfase)
            K, A = ik_pierna(H, Vector((tx, ay, az)), longs[lado][0], longs[lado][1], polo)
            xr = Vector(REST[sup].col[0][:3])
            G_sup = marco(K - H, xr)
            b_sup = a4(M_sup.to_3x3().inverted() @ G_sup)
            P_sup = M_sup @ b_sup
            M_inf = P_sup @ (REST[sup].inverted() @ REST[inf])
            G_inf = marco(A - K, xr)
            b_inf = a4(M_inf.to_3x3().inverted() @ G_inf)
            P_inf = M_inf @ b_inf
            M_pie = P_inf @ (REST[inf].inverted() @ REST[pie])
            G_pie = rx(-phi) @ REST[pie].to_3x3()
            b_pie = a4(M_pie.to_3x3().inverted() @ G_pie)
            for n, b in ((sup, b_sup), (inf, b_inf), (pie, b_pie)):
                eul = euler_de(b, previos.get(n))
                previos[n] = eul
                if f == 0:
                    valores0[n] = eul.copy()
                poner(n, eul, None, f)

    # ---- Ciclico: curvas F con Cycles, accion ciclica con rango manual 0-24
    for capa in accion.layers:
        for franja in capa.strips:
            for bolsa in franja.channelbags:
                for fc in bolsa.fcurves:
                    if not any(m.type == 'CYCLES' for m in fc.modifiers):
                        fc.modifiers.new('CYCLES')
                    fc.update()
    accion.use_frame_range = True
    accion.frame_start = 0
    accion.frame_end = CICLO
    accion.use_cyclic = True
    accion.use_fake_user = True
    ad.action = None
    return accion, slot

def verificar(nombre_accion, accion, slot):
    """Mide el resultado: pies sobre el suelo, rodillas y pelvis (se imprime un resumen)."""
    scene = bpy.context.scene
    ad = ARM.animation_data
    ad.action = accion
    ad.action_slot = slot
    cu = bpy.data.objects['Isaac_Cuerpo']
    gi = {g.name: g.index for g in cu.vertex_groups}
    pts = {}
    for lado in ('L', 'R'):
        g = gi['Foot.' + lado]
        pts[lado] = [v.co.copy() for v in cu.data.vertices
                     if any(x.group == g and x.weight >= 0.99 for x in v.groups)]
    minz, rod = 9.0, []
    for f in range(0, CICLO + 1):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        P = {b.name: ARM.pose.bones[b.name].matrix.copy() for b in HUESOS}
        for lado in ('L', 'R'):
            n = 'Foot.' + lado
            T = P[n] @ REST[n].inverted()
            z = min((T @ v).z for v in pts[lado])
            minz = min(minz, z)
            H = P['UpperLeg.' + lado].translation
            K = P['LowerLeg.' + lado].translation
            A = P[n].translation
            c = (H - K).normalized().dot((A - K).normalized())
            rod.append(math.degrees(math.acos(max(-1.0, min(1.0, c)))))
    ad.action = None
    print("[%s] suela mas baja = %.4f m | rodilla (interior) %.0f..%.0f grados"
          % (nombre_accion, minz, min(rod), max(rod)))
    return minz, min(rod), max(rod)

def main(guardar=False):
    arm = bpy.data.objects[NOMBRE_ARMADURA]
    preparar(arm)
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 0
    scene.frame_end = CICLO
    scene.tool_settings.use_keyframe_cycle_aware = True      # Cycle-Aware Keying

    ank = REST['Foot.L'].translation
    caminar = crear_tobillo_caminar(ank.y, ank.z)
    quieto = crear_tobillo_quieto(ank.y, ank.z)

    a_cam, s_cam = construir_accion(ACCION_CAMINAR, torso_caminar,
                                    {'L': caminar, 'R': caminar}, PASO_FR)
    a_qui, s_qui = construir_accion(ACCION_QUIETO, torso_quieto,
                                    {'L': quieto, 'R': quieto}, 0)

    # Marcadores del taller: Contacto / Bajo / Pase / Alto cada 3 fotogramas
    for m in list(scene.timeline_markers):
        if m.name in MARCADORES:
            scene.timeline_markers.remove(m)
    for i, nombre in enumerate(MARCADORES):
        scene.timeline_markers.new(nombre, frame=i * 3)

    r1 = verificar('Caminar', a_cam, s_cam)
    r2 = verificar('Quieto', a_qui, s_qui)

    # Cada accion en su pista NLA (asi el exportador a glTF las saca como animaciones separadas)
    ad = arm.animation_data
    for pista in list(ad.nla_tracks):
        ad.nla_tracks.remove(pista)
    for accion, slot in ((a_cam, s_cam), (a_qui, s_qui)):
        pista = ad.nla_tracks.new()
        pista.name = accion.name
        franja = pista.strips.new(accion.name, 0, accion)
        try:
            franja.action_slot = slot
        except Exception:
            pass
    ad.action = None

    # Armadura en reposo y fotograma 0, para que el exportador la lea sin pose
    for p in arm.pose.bones:
        p.location = (0, 0, 0)
        p.rotation_quaternion = (1, 0, 0, 0)
        p.rotation_euler = (0, 0, 0)
        p.scale = (1, 1, 1)
    scene.frame_set(0)
    print("Listo: acciones %s y %s (%d fotogramas, %d fps)." % (ACCION_CAMINAR, ACCION_QUIETO, CICLO, FPS))
    if guardar:
        bpy.ops.wm.save_mainfile()
        print("Guardado:", bpy.data.filepath)
    return r1, r2

if __name__ == "__main__":
    main(guardar=False)
