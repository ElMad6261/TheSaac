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
- **Isaac animado.** Ciclo de caminata y pose de reposo hechos con las técnicas del taller de animación, más giro de cabeza independiente del cuerpo con las flechas.
- **Contenido por datos.** Salas, pisos y estadísticas viven en Resources `.tres`, no en código, para agregar variantes sin tocar C#.

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
4. En Godot: *Editor → Configuración del editor → FileSystem → Import → Blender* y apuntar a la ruta de Blender 5.1. Sin esto los `.blend` no importan.
5. La escena principal es `scenes/rooms/nivel_prueba.tscn` (F5). También se pueden abrir `nivel_graybox.tscn` (mapa fijo de 7 salas) y `nivel_aleatorio.tscn` (piso generado; exporta `Floor` y `Seed`).

**Controles:** WASD mueve a Isaac según la pantalla · flechas giran su cabeza · E interactúa · el ratón no se usa.

## Estructura

```
res://
  assets/        blend/, texturas/, audio/            ← archivos fuente (van por Git LFS)
  data/          floors/, rooms/, items/, enemies/    ← Resources .tres (contenido por datos)
  scenes/
    player/      jugador.tscn
    rooms/       nivel_prueba.tscn, sala_normal.tscn, modulos/, graybox/
    props/       antorcha, pedestal, roca, vasija
    enemies/, items/, ui/                             ← vacías a propósito (post-entrega)
  scripts/
    core/        GameEvents.cs, GameState.cs          ← autoloads
    player/      PlayerController.cs
    rooms/       Room.cs, RoomCamera.cs, FloorGenerator.cs, FloorLayout.cs, FloorLoader.cs
    data/        RoomData.cs, FloorConfig.cs
    components/, interaction/                         ← vacías: HealthComponent, IInteractable… (post-entrega)
  tools/blender/ generar_kit.py, animar_isaac.py…     ← regeneran los .blend, no se importan en Godot
  docs/          proyecto.md, mapa_graybox.md, capturas/
```

Regenerar el kit desde cero (Blender 5.1, desde la raíz del repositorio):

```bash
blender --background --factory-startup --python tools/blender/generar_kit.py
```

## Reglas del repositorio

- **Un `.blend` por pieza o colección.** Antes de editar un `.blend` que otro también podría tocar: `git lfs lock assets/blend/archivo.blend` y al terminar `git lfs unlock ...`.
- **No subir** los respaldos `.blend1` ni la carpeta `.godot/` (ya están en `.gitignore`).
- **Sí subir** los archivos `.import` y `.uid` de Godot: guardan la configuración de importación y la identidad de cada asset.
- Trabajar en ramas `feat/...` y fusionar a `main` por Pull Request.
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
