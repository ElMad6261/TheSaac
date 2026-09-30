# CLAUDE.md — TheSaac

Contexto para Claude (Claude Code, MCP de Godot) al trabajar en este repositorio.

## Proyecto
- Recreación 3D en primera persona de *The Binding of Isaac*. Alcance máximo: **Basement 1 y Basement 2**.
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

## Reglas al trabajar
- El equipo debe poder explicar cada línea en la presentación: código claro, comentado donde no sea obvio, sin abstracciones innecesarias.
- No editar escenas abiertas con cambios sin guardar; pedir commit antes de cambios grandes por MCP.
- No añadir assets del juego original (sprites, música, logos).
