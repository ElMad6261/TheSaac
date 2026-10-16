# Mapa graybox (7 salas)

Mapa fijo para la entrega, hecho con nodos CSG. Croquis: `docs/capturas/croquis_mapa_graybox.png`.
Nivel: `scenes/rooms/nivel_graybox.tscn` (se corre con "Ejecutar escena actual"; la escena principal sigue siendo `nivel_prueba.tscn`).

```
                 [TESORO]
                    |
[DESPENSA]-[INICIO]-[CRUCE]-[GALERÍA]-[JEFE]
               |
           [SÓTANO]
```

Norte arriba (-Z), este a la derecha (+X). Cada caja es una sala de 11 × 7 m; en el nivel van cada 12 m en X y 8 m en Z.

| Sala | Celda (col, fila) | Posición en el nivel (X, Z) | Puertas | Distancia al inicio | Tipo |
|---|---|---|---|---|---|
| Inicio | (0, 0) | (0, 0) | E, S, O | 0 | Inicio (piso verde) |
| Despensa | (-1, 0) | (-12, 0) | E | 1 | Normal |
| Sótano | (0, 1) | (0, 8) | N | 1 | Normal |
| Cruce | (1, 0) | (12, 0) | N, E, O | 1 | Normal |
| Tesoro | (1, -1) | (12, -8) | S | 2 | Tesoro (piso dorado) |
| Galería | (2, 0) | (24, 0) | E, O | 2 | Normal |
| Jefe | (3, 0) | (36, 0) | O | 3 | Jefe (piso rojo) |

Reglas que cumple (docs/proyecto.md §6):
- Mapa en árbol, sin ciclos: ninguna sala queda pegada a otra sin estar conectada con ella (§6.2).
- Sin salida hay cuatro salas: Despensa, Sótano, Tesoro y Jefe. El **jefe** es la más lejana al inicio (3 salas) y el **tesoro** es otra sin salida.
- Cada puerta tiene su pareja en la sala vecina (ambas salas activan el lado que se toca).

## Piezas CSG (`scenes/rooms/graybox/`)
- `sala_graybox.tscn`: plantilla con `Room.cs`. Piso (CSGBox3D 11.5 × 0.2 × 7.5), 8 tramos de muro de 0.5 m × 3 m, 4 pilares de 1 m, `Zona/Forma` y los marcadores `Huecos/Norte, Sur, Este, Oeste`.
- `muro_graybox.tscn` y `vano_graybox.tscn`: lo que `Room.cs` pone en el centro de cada pared. El vano es un CSGBox3D de muro al que otra caja (operación Sustracción) le abre 1.5 × 2.5 m, y un umbral (Unión) cruza el hueco de 0.5 m entre salas.
- `roca_graybox`, `columna_graybox`, `pedestal_graybox`: obstáculos de caja para probar el recorrido.
- Una escena por sala (`sala_inicio.tscn`, `sala_cruce.tscn`, ...): heredan de la plantilla, activan sus puertas (`DoorNorth/DoorSouth/DoorEast/DoorWest`), cambian el color del piso y llevan un `Label3D` con su nombre.

Muros, pilares y vanos van en el grupo `muros` (la cámara de sala los pone en "solo sombra" cuando tapan la vista). Todo el CSG tiene `use_collision` y queda en la capa 1 (Mundo).

## Verificación
- Revisión por código en el juego: puertas con pareja, un vano por puerta, zona 10.5 × 6.5 y 4 pilares por sala (0 errores).
- Recorrido con el teclado (WASD): Inicio → Cruce → Galería → Jefe → Cruce → Tesoro → Cruce → Inicio → Sótano → Inicio → Despensa, sin atascos y con la cámara deslizándose en cada puerta.
