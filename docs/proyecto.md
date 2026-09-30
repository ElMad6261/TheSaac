# Isaac 3D — Proyecto Integrador de Entornos 3D e Interacción

> Recreación en primera persona de *The Binding of Isaac* (Basement 1 y 2) con Blender 5.1 y Godot 4.7.2 (.NET / C#).
> Documento vivo del equipo · creado el 27 de septiembre de 2026.

---

## 1. Resumen

| Campo | Valor |
| --- | --- |
| Materia | Proyecto Integrador de Creación de Entornos 3D e Interacción |
| Idea | Explorar en primera persona los sótanos de *The Binding of Isaac*: salas modulares conectadas por puertas que se abren con interacción |
| Motor | Godot 4.7.2, edición .NET (C#), renderizador Forward+ — **reemplaza a Unity 6.3 URP del enunciado** |
| Modelado | Blender 5.1 |
| Seguimiento | Trello (un tablero, cinco listas) |
| Control de versiones | Git + Git LFS (GitHub) |
| Entregables | Build ejecutable, Level Design Document (LDD), presentación el día del semestral |
| Fecha del semestral | **Por confirmar** (se asume la semana del 7 de diciembre de 2026) |

### Rúbrica (del enunciado)

| Criterio | Peso | Qué se evalúa |
| --- | --- | --- |
| Modelado 3D e interoperabilidad Blender–motor | 30% | Escala 1:1, pivote en la bisagra, mallas limpias, Asset Browser y scripts de importación |
| Texturizado y shaders PBR | 25% | UV sin distorsión, horneado de Normal Maps, shaders PBR funcionales |
| Programación e interacción C# | 25% | Detección limpia (Trigger/Raycast), rotación fluida de la puerta sin colisiones erróneas, input correcto |
| Diseño de entorno y presentación | 20% | Composición, iluminación, fluidez en primera persona, build sin errores |

---

## 2. Decisiones pendientes (resolver en la semana 1)

- [ ] **Aprobación escrita del profesor** para usar Godot en lugar de Unity, aceptando la tabla de equivalencias (sección 4). Plan B: si no aprueba, el roadmap se mantiene con Unity 6.3.
- [ ] Confirmar si **C#** es obligatorio (se asume que sí).
- [ ] Confirmar la **fecha real del semestral** y ajustar el roadmap.
- [ ] Preguntar la **política de uso de IA** en el proyecto.
- [ ] Definir integrantes y roles.

---

## 3. Alcance

### Alcance máximo del proyecto (incluso después de la entrega)
**Basement 1 y Basement 2.** Nada más allá de eso.

### Niveles de alcance

| Nivel | Incluye | Cuándo |
| --- | --- | --- |
| Obligatorio (entrega) | 5 a 7 salas estilo sótano conectadas, puertas que se abren con E, rocas y detalles con Geometry Nodes, antorchas, un interruptor, iluminación y post-procesado, build ejecutable | Roadmap completo |
| Deseable (entrega) | Generador aleatorio de salas estilo Isaac, puertas que abren tras activar algo, sala del tesoro y del jefe con look propio, sonido | Solo si la rebanada vertical del 25 oct sale a tiempo (semana 7) |
| Post-entrega | Enemigos, lágrimas (disparo), ítems, jefes, Basement 2 como segundo piso | Después del semestral |

### Reglas de contenido
- Todos los modelos, texturas y sonidos son **propios**, "inspirados en" el juego.
- No se incluyen sprites, música ni el logo originales de *The Binding of Isaac* en el build.

---

## 4. Equivalencias Unity → Godot

Todo lo de Blender (modelado, Geometry Nodes, Asset Browser, UV, horneado) no cambia.

| Enunciado (Unity 6) | En Godot 4.7 | Ojo con |
| --- | --- | --- |
| Unity 6.3 LTS + URP | Godot 4.7.2 .NET, renderizador Forward+ | Descargar la edición .NET |
| Guardar .blend en Assets | Guardar .blend dentro del proyecto; Godot invoca a Blender y lo convierte a glTF | Configurar la ruta de Blender en Editor Settings → FileSystem → Import. Si falla con Blender 5.1, exportar .glb manualmente |
| Y-Up (Unity) vs Z-Up (Blender) | Godot es Y-Up; el importador convierte | Frente del modelo hacia −Y en Blender; aplicar escala y rotación (Ctrl+A) |
| Pivote en la bisagra | El origen del objeto en Blender es el pivote en Godot | Hoja de la puerta separada del marco |
| ProBuilder (graybox) | Nodos CSG (CSGBox3D, CSGCombiner3D) | Exportar el blocking: Escena → Exportar como → glTF; convertir a .obj en Blender si se exige |
| on_scene_load.py | Script de post-importación (EditorScenePostImport) + sufijos (-col, -noimp) | Los sufijos generan colisiones y excluyen objetos sin código |
| Shader Graph | Visual Shader (ShaderMaterial) con parámetros de tiling, roughness y opacidad | Godot usa roughness (= 1 − smoothness) |
| Texturas Non-Color | Mapas normales se marcan al asignarlos; AO/roughness/metal en un ORM lineal | Revisar el preset de importación |
| Input System | Input Map (Project Settings): move, look, interact = E | Mismos nombres de acción en todo el código |
| CharacterController | CharacterBody3D + cápsula + Camera3D | |
| Trigger Collider | Area3D con señales body_entered / body_exited | |
| Raycast | RayCast3D hijo de la cámara | |
| Quaternion.Slerp / Lerp | Quaternion.Slerp en C#, o un Tween | |
| Puerta sin colisiones erróneas | Hoja como AnimatableBody3D | Empuja al jugador en vez de atravesarlo |
| Directional / Point Lights | DirectionalLight3D / OmniLight3D | |
| Volumen URP (Bloom, Tonemapping) | WorldEnvironment: Glow y Tonemap | |
| Build | Exportar con plantillas .NET para Windows | Instalarlas en la semana 1 |

---

## 5. Arquitectura (pensada para crecer hasta Basement 2)

Regla principal: **nada se escribe exclusivo para la puerta ni para el jugador.** Todo son piezas genéricas donde después se enchufan enemigos, lágrimas e ítems sin rehacer lo existente.

### 5.1 Salas con estados, como en Isaac
- `Room.cs` tiene estados: **sin visitar → en combate → despejada**.
- Las puertas escuchan `RoomCleared` para abrirse.
- Hoy (sin enemigos) una sala se marca despejada al entrar y la puerta abre con E.
- Con enemigos, la sala pasa a despejada al morir el último, **sin tocar el script de la puerta**.
- Cada sala tiene `Marker3D` vacíos para futuros enemigos e ítems.

### 5.2 Componentes reutilizables
| Componente | Qué hace | Lo usa hoy | Lo usará después |
| --- | --- | --- | --- |
| `HealthComponent` | Vida, daño, muerte | Rocas destructibles (opcional) | Jugador, enemigos |
| `Hitbox` / `Hurtbox` (Area3D) | Lo que hace daño / lo que lo recibe | — | Lágrimas, enemigos |
| `IInteractable` | Método `Interact()` | Puerta, interruptor, antorcha | Pedestal de ítem, cofre |
| `Interactor` | Raycast del jugador que llama a `Interact()` | Jugador | Jugador |

### 5.3 Contenido definido por datos (Resources `.tres`)
Agregar contenido = crear un `.tres`, no código nuevo.

| Resource | Contenido |
| --- | --- |
| `PlayerStats` | Velocidad, daño, cadencia, alcance, velocidad de disparo (estadísticas de Isaac) |
| `ItemData` | Nombre, modelo, lista de modificadores de estadísticas |
| `EnemyData` | Vida, velocidad, escena del enemigo |
| `RoomData` | Tipo de sala (normal, inicio, tesoro, jefe), escena |
| `FloorConfig` | Número de salas, grupo de salas, jefe. **`basement_1.tres` y `basement_2.tres`** |

### 5.4 Autoloads
- `GameEvents`: señales globales (`RoomEntered`, `RoomCleared`, `PlayerDamaged`, `ItemPicked`).
- `GameState`: piso actual, semilla del generador, estadísticas del jugador (persisten de Basement 1 a 2).

### 5.5 Capas de colisión (fijas desde el día 1)
| # | Capa |
| --- | --- |
| 1 | Mundo |
| 2 | Jugador |
| 3 | Enemigos |
| 4 | Lágrimas del jugador |
| 5 | Lágrimas enemigas |
| 6 | Interactuables |
| 7 | Recogibles |

### 5.6 Estructura de carpetas
```
res://
  assets/        blend/, texturas/, audio/
  data/          floors/ (basement_1.tres, basement_2.tres), items/, enemies/, rooms/
  scenes/        player/, rooms/, props/ (puerta, antorcha, interruptor), enemies/, items/, ui/
  scripts/
    core/        GameEvents.cs, GameState.cs
    components/  HealthComponent.cs, Hitbox.cs, Hurtbox.cs
    interaction/ IInteractable.cs, Interactor.cs, DoorInteraction.cs
    rooms/       Room.cs, FloorGenerator.cs
    data/        PlayerStats.cs, ItemData.cs, EnemyData.cs, RoomData.cs, FloorConfig.cs
  addons/        godot_mcp/ (ver sección 9)
```

---

## 6. Salas y generación aleatoria

### 6.1 Reglas de las salas (obligatorias desde la semana 2)
- Todas las salas tienen el **mismo tamaño exterior** (p. ej. 13 × 7 módulos de 1 m).
- Una **abertura de puerta centrada en cada pared**.
- Cada sala es una **escena independiente** (`.tscn`).
- Donde no hay sala vecina se coloca un muro sólido; donde hay, una puerta con `DoorInteraction.cs`.

### 6.2 Algoritmo tipo Isaac (versión simplificada)
1. Cuadrícula pequeña (p. ej. 9 × 8); sala inicial en el centro.
2. Desde cada sala se intenta abrir una vecina (arriba, abajo, izquierda, derecha). Se descarta si:
   - la celda ya está ocupada,
   - la nueva sala quedaría pegada a más de una sala existente,
   - falla una tirada al 50%.
3. Repetir hasta el número de salas de `FloorConfig`.
4. Salas sin salida (un solo vecino) → especiales: **jefe = la más lejana** a la inicial; tesoro = otra sin salida.
5. Guardar la **semilla** para repetir mapas (depuración y demo).

### 6.3 Implicaciones
- **Iluminación:** con mapa aleatorio no se hornea la luz del nivel entero; luces en tiempo real o horneado por sala.
- **LDD:** dos modos — mapa fijo diseñado a mano para la presentación y modo aleatorio con semilla. El LDD documenta las reglas del generador y el diseño de cada tipo de sala.
- **Costo:** ~1 semana para una persona si las salas cumplen las reglas.

---

## 7. Roadmap (10 semanas)

| Fase | Fechas |
| --- | --- |
| Setup y aprobación | 28 sep – 4 oct |
| Hito: OK del profesor | 2 oct |
| F1 · Graybox + jugador | 5 – 11 oct |
| F2 · Modelado modular | 12 – 25 oct |
| F4 · Interacciones C# (en paralelo) | 12 oct – 15 nov |
| **Hito: rebanada vertical** | 25 oct |
| F3 · Texturas y shaders | 26 oct – 8 nov |
| Integración y luces | 9 – 22 nov |
| Build, pruebas y LDD | 16 – 29 nov |
| **Hito: build congelado** | 29 nov |
| Colchón y ensayo | 30 nov – 6 dic |
| **Semestral (supuesto)** | 7 dic |

### Semana 1 · 28 sep – 4 oct · Setup y aprobación
- [ ] Enviar al profesor la tabla de equivalencias y pedir aprobación por escrito
- [ ] Instalar Godot 4.7.2 .NET, SDK de .NET, Blender 5.1 y plantillas de exportación en todas las máquinas
- [ ] Repositorio Git con Git LFS para .blend, .png y .glb, y .gitignore de Godot
- [ ] Prueba de pipeline: puerta de prueba en .blend que gira sobre su bisagra en Godot
- [ ] Alcance en una página
- [ ] Tablero de Trello y reparto de roles

### Semana 2 · 5 – 11 oct · Fase 1: graybox y jugador
- [ ] Fijar medida del módulo y reglas de las salas (sección 6.1)
- [ ] Definir capas de colisión y autoloads vacíos (sección 5)
- [ ] Graybox de 5 a 7 salas con nodos CSG y croquis del mapa
- [ ] CharacterBody3D con cámara, WASD y ratón desde el Input Map
- [ ] Exportar el blocking a Blender como referencia
- [ ] Instalar y probar el MCP de Godot (sección 9)

### Semanas 3 y 4 · 12 – 25 oct · Fase 2: modelado modular (+ programación en paralelo)
- [ ] Kit 1:1: muro recto, esquina, muro con hueco de puerta, piso, columna, arco
- [ ] Puerta: marco, hoja y cerrojo separados; origen de la hoja en la bisagra
- [ ] Geometry Nodes: rocas y escombros, variaciones de cornisa o bóveda
- [ ] Módulos marcados en el Asset Browser, ordenados por colección
- [ ] Script de post-importación o sufijos para colecciones auxiliares y luces de prueba
- [ ] `IInteractable`, `Interactor` y `DoorInteraction.cs` sobre la puerta gris (Area3D + E + giro de 90°)
- [ ] Variante con RayCast3D y decisión final
- [ ] `Room.cs` con estados y señal `RoomCleared`
- [ ] Interruptor y antorcha que se enciende

**Hito 25 oct — rebanada vertical:** una sala con módulos reales (sin textura) y la puerta abriéndose dentro de un build.

### Semanas 5 y 6 · 26 oct – 8 nov · Fase 3: UV, horneado y shaders
- [ ] UV de puerta y módulos, revisado con textura de cuadrícula
- [ ] High-poly de puerta, roca y un muro; horneado de Normal y AO a la low-poly
- [ ] Texturas en Godot con el preset correcto
- [ ] Visual Shader con tiling, roughness y opacidad; materiales de piedra, madera y metal
- [ ] Look del sótano: paleta de cafés y grises, suciedad con mapa de detalle

### Semana 7 · 9 – 15 nov · Cierre de interacciones e inicio de integración
- [ ] Hoja de la puerta como AnimatableBody3D; no atraviesa ni atrapa al jugador
- [ ] Aviso en pantalla "E · Abrir"
- [ ] Un solo script de puerta parametrizado (ángulo, velocidad, bloqueada)
- [ ] *(Deseable)* `FloorGenerator.cs` + `basement_1.tres`

### Semana 8 · 16 – 22 nov · Integración, luces y post-procesado
- [ ] Reemplazar todo el graybox por escenas finales
- [ ] Sala con tragaluz para la DirectionalLight3D; OmniLight3D con parpadeo en antorchas
- [ ] WorldEnvironment: Glow, Tonemap, niebla ligera
- [ ] Prueba de rendimiento en la PC más lenta del grupo

### Semana 9 · 23 – 29 nov · Build, pruebas y LDD
- [ ] Build de Windows probado en una PC sin Godot
- [ ] Dos personas ajenas al grupo lo juegan; bugs a Trello
- [ ] LDD: mapa, flujo del jugador, lista de assets, decisiones de pipeline, capturas
- [ ] **29 nov: build congelado** — después solo se arreglan bugs

### Semana 10 · 30 nov – 6 dic · Colchón y ensayo
- [ ] Cerrar bugs pendientes
- [ ] Video del recorrido como respaldo
- [ ] Ensayo de la demo en el orden de la rúbrica: Blender → shaders → interacción → escena final

### Post-entrega (hasta Basement 2)
- [ ] Lágrimas: escena de proyectil con `Hitbox`, dirección desde la cámara, stats de `PlayerStats`
- [ ] Enemigos básicos con `HealthComponent` y `EnemyData`; salas pasan a "en combate"
- [ ] Ítems: pedestal (`IInteractable`) + `ItemData` con modificadores
- [ ] Jefe de Basement 1
- [ ] `basement_2.tres` y transición entre pisos conservando `GameState`

---

## 8. Trello

### Listas
| Lista | Qué va ahí | Regla |
| --- | --- | --- |
| Backlog | Todas las tarjetas del roadmap | Ordenadas por semana |
| Esta semana | Compromiso del equipo | Se llena el domingo |
| En proceso | Trabajo actual | Máximo 2 tarjetas por persona |
| En revisión | Terminado, falta que otro lo pruebe en Godot | Nadie aprueba su propia tarjeta |
| Hecho | Revisado y en el repositorio | |

### Etiquetas
- Por criterio de rúbrica: **Modelado e interoperabilidad (30%)**, **Texturas y shaders (25%)**, **Programación C# (25%)**, **Entorno y presentación (20%)**.
- Extra: **Bug**, **Bloqueado**, **Deseable**, **Post-entrega**.

### Formato de tarjeta
- Título con verbo ("Modelar la hoja de la puerta con origen en la bisagra").
- Un responsable y fecha de vencimiento (domingo de su semana).
- Checklist "Hecho cuando" (ej.: origen en la bisagra, escala aplicada, entra en Godot sin rotaciones raras, está en el repo).
- Captura o enlace al commit al cerrarla (alimenta el LDD).

### Ritual
- **Domingo, 20 min:** revisar Hecho, mover Backlog → Esta semana, pasar a Deseable lo que no llega.
- **Mitad de semana:** mensaje corto sobre lo Bloqueado.

### Roles sugeridos
| Rol | Responsabilidad |
| --- | --- |
| Arte | Blender: modelado, Geometry Nodes, UV, horneado |
| Código | Godot/C#: jugador, interacciones, salas, generador |
| Nivel y producción | Composición, iluminación, LDD, tablero de Trello |

Con dos personas, el tercer rol se reparte. El dueño de un área revisa y aprueba lo de esa área.

---

## 9. Herramientas de IA (MCP)

### Elección: `satelliteoflove/godot-mcp`
Comparado con `Coding-Solo/godot-mcp`:

| | satelliteoflove/godot-mcp | Coding-Solo/godot-mcp |
| --- | --- | --- |
| Enfoque | Puente con el editor abierto + juego en ejecución | Godot por línea de comandos + script GDScript de operaciones |
| Probar el juego | Inyecta input (acciones, teclas, mouse-look), congela y avanza el tiempo, lee el estado en JSON | Ejecuta el proyecto y lee la salida de depuración |
| 3D | Transformaciones, cajas de colisión y visibilidad calculadas por el motor; GridMap; validación de mallas | Exportar MeshLibrary; utilidades de escena más orientadas a 2D (Sprite2D) |
| Seguridad | Solo `127.0.0.1`; herramientas de lectura separadas de las de escritura; modo `--read-only` | Local |
| Requisitos | Godot 4.5+, Node.js 20+ | Godot instalado, Node.js 18+ |
| Madurez | 165 estrellas, 311 commits, versión 4 | 5.6k estrellas, 60 commits, 34 PR abiertos |
| Licencia | MIT | MIT |

**Por qué:** para este proyecto lo valioso es verificar comportamiento en 3D, por ejemplo: "entra a la zona de la puerta, presiona E, avanza 1 segundo y dime la rotación de la hoja y si el jugador quedó atrapado". Eso solo lo permite satelliteoflove.

### Instalación (semana 2, con el proyecto ya creado y en Git)
1. Instalar Node.js 20+.
2. Instalar el addon en el proyecto:
   ```
   npx @satelliteoflove/godot-mcp --install-addon /ruta/al/proyecto
   ```
3. En Godot: **Project → Project Settings → Plugins → Godot MCP** (activar).
4. Configurar el cliente (Claude Code o app de escritorio de Claude):
   ```json
   {
     "mcpServers": {
       "godot-mcp": {
         "command": "npx",
         "args": ["-y", "@satelliteoflove/godot-mcp"]
       }
     }
   }
   ```
5. Abrir el proyecto en Godot y reiniciar el cliente de IA.

### Reglas de uso
- Hacer **commit antes** de dejar que la IA cambie escenas.
- Permitir automáticamente solo las herramientas de lectura; las de escritura, con confirmación.
- Un editor atiende a un solo cliente MCP a la vez.
- La arquitectura y los scripts clave (puerta, salas, generador) los escribe el equipo con apoyo de la IA: en el semestral hay que poder explicar cada línea.

### Otros conectores
- **Trello:** conectado. Tablero: https://trello.com/b/bx1K8Xef/thebindingofisaac
- **GitHub:** conectado. Repositorio público: https://github.com/ElMad6261/TheSaac

---

## 10. Riesgos

| Riesgo | Señal temprana | Plan B |
| --- | --- | --- |
| El profesor no acepta Godot | Sin respuesta al 2 oct | Volver a Unity 6.3 esa semana; roadmap igual |
| Importación de .blend falla con Blender 5.1 | Prueba de la semana 1 no carga | Exportar .glb a mano |
| El alcance crece | Tarjetas de combate antes del 25 oct | Etiqueta Deseable/Post-entrega; nada nuevo hasta la rebanada vertical |
| Conflictos con .blend en Git | Dos personas en el mismo archivo | Un .blend por módulo y bloqueo de archivos con Git LFS |
| Horneado con artefactos | Falla la primera prueba de la semana 5 | Ajustar jaula/extrusión con la puerta sola antes del resto |
| Alguien deja de avanzar | Tarjetas sin moverse una semana | Redistribuir en el ritual del domingo |

### Hábitos
1. Exportar un build cada semana desde la semana 4, aunque esté feo.
2. Anotar cada decisión de pipeline (escala, ejes, nombres, sufijos) en una tarjeta fija; el LDD sale casi escrito.
3. Capturas del progreso cada semana para la presentación.

---

## 11. Referencias
- Godot releases: https://godotengine.org/blog/release/
- satelliteoflove/godot-mcp: https://github.com/satelliteoflove/godot-mcp
- Coding-Solo/godot-mcp: https://github.com/Coding-Solo/godot-mcp
