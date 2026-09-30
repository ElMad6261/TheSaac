# TheSaac — Isaac 3D

Recreación en primera persona de los sótanos de *The Binding of Isaac* (Basement 1 y 2), hecha con **Blender 5.1** y **Godot 4.7.2 .NET (C#)**.

Proyecto Integrador de Creación de Entornos 3D e Interacción · Universidad Tecnológica de Panamá.

> Proyecto académico sin fines comerciales. Todos los modelos, texturas y sonidos son propios, inspirados en el juego original; no se incluyen assets, música ni logos de *The Binding of Isaac*.

- **Documento completo del proyecto:** [`docs/proyecto.md`](docs/proyecto.md) (alcance, equivalencias Unity → Godot, arquitectura, roadmap, riesgos)
- **Tablero de tareas:** [Trello — TheBindingOfIsaac](https://trello.com/b/bx1K8Xef/thebindingofisaac)

---

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

# 2. Clonar
git clone https://github.com/ElMad6261/TheSaac.git
cd TheSaac
```

3. **Solo la primera persona:** en Godot 4.7.2 .NET → *Nuevo proyecto* → carpeta `TheSaac` (la del repositorio) → renderizador **Forward+**. Luego *Proyecto → Herramientas → C# → Crear solución C#*. Commit y push de `project.godot`, `*.csproj` y `*.sln`.
4. **Los demás:** después de ese commit, `git pull` y abrir `project.godot` en Godot.
5. En Godot: *Editor → Configuración del editor → FileSystem → Import → Blender* y apuntar a la ruta de Blender 5.1.

## Estructura

```
res://
  assets/        blend/, texturas/, audio/            ← archivos fuente (van por Git LFS)
  data/          floors/, items/, enemies/, rooms/    ← Resources .tres (contenido por datos)
  scenes/        player/, rooms/, props/, enemies/, items/, ui/
  scripts/
    core/        GameEvents.cs, GameState.cs          ← autoloads
    components/  HealthComponent.cs, Hitbox.cs, Hurtbox.cs
    interaction/ IInteractable.cs, Interactor.cs, DoorInteraction.cs
    rooms/       Room.cs, FloorGenerator.cs
    data/        PlayerStats.cs, ItemData.cs, EnemyData.cs, RoomData.cs, FloorConfig.cs
  docs/          proyecto.md, LDD
```

Las carpetas de enemigos e ítems están vacías a propósito: son para después de la entrega (ver `docs/proyecto.md`, sección 5).

## Reglas del repositorio

- **Un `.blend` por pieza o colección.** Antes de editar un `.blend` que otro también podría tocar: `git lfs lock assets/blend/archivo.blend` y al terminar `git lfs unlock ...`.
- **No subir** los respaldos `.blend1` ni la carpeta `.godot/` (ya están en `.gitignore`).
- **Sí subir** los archivos `.import` de Godot: guardan la configuración de importación de cada asset.
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
