# CLAUDE.md — TheSaac

Contexto para Claude (Claude Code, MCP de Godot) al trabajar en este repositorio.

## Proyecto
- Recreación 3D en **vista 2.5D estilo Isaac**: cámara fija desde arriba que encuadra una sala a la vez y se desliza a la siguiente al cruzar una puerta; Isaac se ve en pantalla. Alcance máximo: **Basement 1 y Basement 2**.
- Entrega académica: exploración de salas modulares + puertas interactivas. Enemigos, lágrimas, ítems y jefes son **post-entrega**; no implementarlos antes de que el equipo lo pida.
- Documento completo: `docs/proyecto.md`. Tareas: tablero de Trello "TheBindingOfIsaac".
- El equipo escribe en **español**; comentarios, commits y documentación en español.

## Stack
- Godot **4.7.2 .NET**, renderizador Forward+, scripts en **C#** (no GDScript).
- Blender 5.1. Los `.blend` se importan directamente; si falla, se exporta `.glb`.
- Git LFS para binarios (ver `.gitattributes`).

## Convenciones de arquitectura
- Nada exclusivo para la puerta o el jugador: piezas genéricas (`IInteractable`, `HealthComponent`, `Hitbox`/`Hurtbox`).
- Contenido por datos: Resources `.tres` (`PlayerStats`, `ItemData`, `EnemyData`, `RoomData`, `FloorConfig`).
- Comunicación entre sistemas por señales del autoload `GameEvents`; estado persistente en `GameState`.
- Salas: mismo tamaño exterior, una abertura de puerta centrada en cada pared, cada sala es su propia escena `.tscn`.
- Capas de colisión: 1 Mundo · 2 Jugador · 3 Enemigos · 4 Lágrimas jugador · 5 Lágrimas enemigas · 6 Interactuables · 7 Recogibles.
- Input Map: `move_forward`, `move_back`, `move_left`, `move_right`, `interact` (E).
- Jugador: `scenes/player/jugador.tscn` + `scripts/player/PlayerController.cs`. CharacterBody3D (capa 2) con `Modelo` (Isaac, gira hacia donde camina). WASD = arriba/abajo/izquierda/derecha de la pantalla; el ratón no se usa.
- Cámara: una por nivel, `scripts/rooms/RoomCamera.cs` (Camera3D que mira al norte, -Z, desde arriba). Escucha `GameEvents.RoomEntered` y se desliza a la sala nueva.
- Salas: raíz con `scripts/rooms/Room.cs` y un Area3D `Zona/Forma` que cubre el interior. Plantilla: `scenes/rooms/sala_normal.tscn` (piso, muros, pilares y antorchas del kit, con colisión). El centro de cada pared lo llena `Room.cs` al arrancar: vano si `DoorNorth/DoorSouth/DoorEast/DoorWest` está activo, muro sólido si no. Piezas en `scenes/rooms/modulos/` (muro, muro_vano, pilar, piso) y `scenes/props/` (antorcha, roca, pedestal). En el nivel, las salas van cada 12 m en X y 8 m en Z. Sin techo visible (la cámara está arriba). Muros, pilares, puertas y antorchas de las paredes van en el grupo `muros`: la cámara deja en "solo sombra" los que quedan entre ella y la sala.

## Reglas al trabajar
- El equipo debe poder explicar cada línea en la presentación: código claro, comentado donde no sea obvio, sin abstracciones innecesarias.
- No editar escenas abiertas con cambios sin guardar; pedir commit antes de cambios grandes por MCP.
- No añadir assets del juego original (sprites, música, logos).
