# TheSaac — Isaac 3D

Recreación en **2.5D** (cámara fija desde arriba, como el juego original pero en 3D) de los sótanos de *The Binding of Isaac* (Basement 1 y 2), hecha con **Blender 5.1** y **Godot 4.7.2 .NET (C#)**.

Proyecto Integrador de Creación de Entornos 3D e Interacción · Universidad Tecnológica de Panamá.

> Proyecto académico sin fines comerciales. Todos los modelos, texturas y sonidos son propios, inspirados en el juego original; no se incluyen assets, música ni logos de *The Binding of Isaac*.

- **Documento completo del proyecto:** [`docs/proyecto.md`](docs/proyecto.md) (alcance, equivalencias Unity → Godot, arquitectura, roadmap, riesgos)
- **Contexto para la IA:** [`CLAUDE.md`](CLAUDE.md) · **Mapa graybox:** [`docs/mapa_graybox.md`](docs/mapa_graybox.md)
- **Tablero de tareas:** [Trello — TheBindingOfIsaac](https://trello.com/b/bx1K8Xef/thebindingofisaac)

---

## Características

- **Vista 2.5D estilo Isaac.** Cámara fija desde arriba que encuadra una sala completa y se desliza a la siguiente al cruzar una puerta (`RoomCamera.cs`). Los muros que quedan entre la cámara y la sala pasan a "solo sombra", así la pared de abajo no tapa a Isaac.
- **Salas modulares.** Cada sala es su propia escena con el mismo tamaño exterior y una abertura centrada en cada pared. `Room.cs` llena cada centro al arrancar: vano si hay sala vecina de ese lado, muro sólido si no.
- **Generación de pisos tipo Isaac.** `FloorGenerator.cs` + `FloorLayout.cs` deciden qué sala va en cada celda a partir de un `FloorConfig`; misma semilla, mismo mapa. `FloorLoader.cs` instancia el piso y `GameState` guarda la semilla entre recargas.
- **Kit propio hecho en Blender.** 12 piezas modulares y variantes de puerta, con texturas pixeladas de línea negra, generadas por script (`tools/blender/`) para poder rehacerlas desde cero.
- **Animación a mano y por script.** Ciclo de caminata de Isaac con las técnicas del taller, y cuatro animaciones de puerta con anticipación, sobretiro y asiento.
- **Contenido por datos.** Salas, pisos y estadísticas viven en Resources `.tres`, no en código, para agregar variantes sin tocar C#.

## Animaciones

### Isaac

Dos acciones en bucle de 24 fotogramas a 24 fps, hechas en `assets/blend/isaac.blend` y exportadas por pistas NLA para que Godot las separe: **`Caminar`** y **`Quieto`**. `PlayerController.cs` las cambia según la velocidad del cuerpo.

Están animadas "en el sitio": el avance lo da el `CharacterBody3D` y el pie de apoyo retrocede a velocidad constante. Llevan bote vertical y vaivén de pelvis, giro opuesto de cadera y pecho, rodaje de pie talón → plano → punta y brazos FK opuestos a las piernas con retraso hombro → codo → mano. Isaac no tiene huesos IK: el script resuelve una IK de dos huesos por fotograma y deja solo claves de rotación.

Las **flechas** giran únicamente la cabeza (hueso `Head`) respecto al cuerpo; sin flechas, la cabeza sigue al cuerpo. En el Inspector del jugador se ajustan `Speed`, `WalkAnimSpeed` y `HeadTurnSpeed`.

Regenerarlas: abrir `isaac.blend` y correr `tools/blender/animar_isaac.py` desde *Scripting → Run Script*.

### Puertas

Cada puerta (`scenes/props/puerta/`) es `Modelo` (el `.blend`) + `Jambas` (colisión de jambas y dintel) + `Hoja` (un `AnimatableBody3D` con el origen en la bisagra) + un `AnimationPlayer` en modo física. Cada animación mueve la colisión y la malla con las mismas claves, sin `RemoteTransform3D`.

| Animación | Dura | Qué hace |
| --- | --- | --- |
| `Abrir` | 0.70 s | Anticipación de 4° atrás, gira 90°, se pasa 4° del tope y asienta |
| `Cerrar` | 0.54 s | Cae acelerando, golpea el marco 1.5°, rebota 1° y queda cerrada |
| `Bloqueada` | 0.40 s | La hoja intenta abrir y tiembla con amplitud decreciente (máx. 2.5°) |
| `Desbloquear` | 1.65 s | Solo en la del tesoro: la llave crece, gira 360° sobre su centro, hace clic, se esfuma con destello dorado y la hoja abre |
| `RESET` | — | Cerrada, llave visible y sin destello |

La hoja gira 90° hacia **-Z local**; para que abra al otro lado, se gira la puerta 180° en Y.

Las bibliotecas `.tres` **no se editan a mano**: se cambian los parámetros de `tools/godot/generar_animaciones_puerta.py` y se vuelve a correr (no necesita Godot ni Blender). El script verifica el resultado simulando la interpolación de Godot, y con `--grafica salida.png` dibuja las curvas.

```bash
python tools/godot/generar_animaciones_puerta.py
```

Para verlas: abrir `scenes/props/puerta/puerta.tscn`, seleccionar el `AnimationPlayer` y darle Play en el panel *Animation*. Las tres juntas están en `prueba_puertas.tscn`.

Desde C#:

```csharp
var anim = GetNode<AnimationPlayer>("AnimationPlayer");
anim.Play("Abrir");
anim.AnimationFinished += (StringName nombre) => { /* avisar a la sala */ };
```

## Versiones (todo el equipo usa exactamente estas)

| Herramienta | Versión |
| --- | --- |
| Godot | 4.7.2 **edición .NET** + plantillas de exportación 4.7.2 .NET |
| .NET SDK | El que indica la página de descarga de Godot 4.7.2 |
| Blender | 5.1 |
| Git LFS | Cualquier versión reciente |
| Node.js | 20+ (solo para el MCP de Godot) |

Nadie actualiza a mitad de semestre.

## Primeros pasos

```bash
# 1. Una sola vez por computadora
git lfs install

# 2. Clonar (el proyecto de Godot ya viene versionado)
git clone https://github.com/ElMad6261/TheSaac.git
cd TheSaac
```

3. Abrir `project.godot` con Godot 4.7.2 .NET. La primera importación tarda: Godot convierte los `.blend`.
4. En Godot: *Editor → Configuración del editor → FileSystem → Import → Blender* y apuntar a la ruta de Blender 5.1. Sin esto los `.blend` no importan y no se ven las animaciones.
5. La escena principal es `scenes/rooms/nivel_prueba.tscn` (F5). También se pueden abrir `nivel_graybox.tscn` (mapa fijo de 7 salas) y `nivel_aleatorio.tscn` (piso generado; exporta `Floor` y `Seed`).

**Controles:** WASD mueve a Isaac según la pantalla · flechas giran su cabeza · E interactúa · el ratón no se usa.

El addon del MCP de Godot **no va en el repositorio**: cada quien lo instala en su máquina (ver `docs/proyecto.md` §9). Godot reescribe entonces unas líneas en `project.godot`; **no las commitees**.

## Estructura

```
res://
  assets/        blend/, texturas/, audio/            ← archivos fuente (van por Git LFS)
  data/          floors/, rooms/, items/, enemies/    ← Resources .tres (contenido por datos)
  scenes/
    player/      jugador.tscn
    rooms/       nivel_prueba.tscn, sala_normal.tscn, modulos/, graybox/
    props/       antorcha, pedestal, roca, vasija, puerta/
    enemies/, items/, ui/                             ← vacías a propósito (post-entrega)
  scripts/
    core/        GameEvents.cs, GameState.cs          ← autoloads
    player/      PlayerController.cs
    rooms/       Room.cs, RoomCamera.cs, FloorGenerator.cs, FloorLayout.cs, FloorLoader.cs
    data/        RoomData.cs, FloorConfig.cs
    components/, interaction/                         ← vacías: HealthComponent, IInteractable… (post-entrega)
  tools/
    blender/     generar_kit.py, animar_isaac.py      ← regeneran los .blend
    godot/       generar_animaciones_puerta.py        ← regenera las bibliotecas de animación
  docs/          proyecto.md, mapa_graybox.md, capturas/
```

Regenerar el kit desde cero (Blender 5.1, desde la raíz del repositorio):

```bash
blender --background --factory-startup --python tools/blender/generar_kit.py
```

## Pendientes conocidos

- **`DoorInteraction.cs`**: falta el script que decida cuándo reproducir cada animación (tecla E, llaves en `GameState`, sala despejada). Las puertas tampoco están puestas todavía en los vanos: `Room.cs` sigue instanciando `muro_vano.tscn`.
- **No cerrar una puerta con Isaac en el umbral**: la hoja lo empuja y lo deja al otro lado del vano. Usar un `Area3D` o cerrar solo a más de ~1.2 m.
- **`Cornisa_C`**: `muro.tscn` y `muro_vano.tscn` todavía referencian un nodo que ya no existe en `cornisa.blend`; el editor lo reporta como error. Hay que quitar esas líneas.
- **Sin sonido**: `assets/audio` está vacío.
- Enemigos, lágrimas, ítems y jefes son **post-entrega**.

## Reglas del repositorio

- **Un `.blend` por pieza o colección.** Antes de editar un `.blend` que otro también podría tocar: `git lfs lock assets/blend/archivo.blend` y al terminar `git lfs unlock ...`.
- **No subir** los respaldos `.blend1`, la carpeta `.godot/` ni `addons/` (ya están en `.gitignore`).
- **Sí subir** los archivos `.import` y `.uid` de Godot: guardan la configuración de importación y la identidad de cada asset.
- Trabajar en ramas `feat/...` y fusionar a `main` por Pull Request. **Nunca `git push --force`** sobre una rama compartida.
- Commit antes de dejar que una IA (Claude, MCP) edite escenas.
- Cada tarea cerrada en Trello lleva el enlace a su commit.

## Capas de colisión (Project Settings → Layer Names → 3D Physics)

| # | Capa |
| --- | --- |
| 1 | Mundo |
| 2 | Jugador |
| 3 | Enemigos |
| 4 | Lágrimas del jugador |
| 5 | Lágrimas enemigas |
| 6 | Interactuables |
| 7 | Recogibles |

Motor de física: **Jolt**. Renderizador: **Forward+**.