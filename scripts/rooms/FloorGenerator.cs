using System;
using System.Collections.Generic;
using Godot;

/// <summary>
/// Generador de pisos tipo Isaac (docs/proyecto.md §6.2). No crea nodos: devuelve un FloorLayout
/// (qué sala va en cada celda) y otro script se encarga de instanciar las escenas.
///
/// 1. Cuadrícula (FloorConfig.GridSize), sala inicial en el centro.
/// 2. Desde cada sala se intenta abrir una vecina (arriba, abajo, izquierda, derecha). Se descarta si la celda
///    está fuera de la cuadrícula, si ya está ocupada, si la sala nueva quedaría pegada a más de una sala,
///    o si falla la tirada (FloorConfig.SpawnChance).
/// 3. Se repite hasta tener FloorConfig.RoomCount salas.
/// 4. Salas sin salida (un solo vecino): el jefe es la más lejana del inicio y el tesoro es otra.
/// 5. La semilla se guarda en el FloorLayout: misma semilla = mismo mapa.
/// </summary>
public static class FloorGenerator
{
	// Si un intento no sirve (se atora o no salen dos salas sin salida), se hace otro con la misma semilla.
	private const int MaxAttempts = 100;

	// Cuántas veces se recorren todas las salas buscando dónde abrir una nueva antes de rendirse con ese intento.
	private const int MaxPasses = 20;

	/// <summary>Genera el mapa del piso. Devuelve null solo si la configuración no permite armar un mapa válido.</summary>
	public static FloorLayout Generate(FloorConfig config, int seed)
	{
		if (config.RoomCount < 3)
		{
			GD.PushError("FloorGenerator: hacen falta al menos 3 salas (inicio, tesoro y jefe).");
			return null;
		}

		// Un solo generador de números al azar por semilla: así los intentos también salen siempre iguales.
		Random rng = new Random(seed);
		for (int attempt = 0; attempt < MaxAttempts; attempt++)
		{
			FloorLayout layout = TryGenerate(config, seed, rng);
			if (layout != null)
			{
				return layout;
			}
		}

		GD.PushError("FloorGenerator: no se logró generar un mapa con esta configuración (revisa RoomCount y GridSize).");
		return null;
	}

	// Un intento de armar el mapa. Devuelve null si se atoró o si no hay dos salas sin salida para jefe y tesoro.
	private static FloorLayout TryGenerate(FloorConfig config, int seed, Random rng)
	{
		Vector2I start = config.GridSize / 2;
		FloorLayout layout = new FloorLayout(seed, start);
		layout.Cells[start] = RoomType.Start;

		Queue<Vector2I> pending = new Queue<Vector2I>();   // salas desde las que todavía se intenta abrir vecinas
		pending.Enqueue(start);
		int passes = 0;

		while (layout.Cells.Count < config.RoomCount)
		{
			if (pending.Count == 0)
			{
				// Se acabó la cola y faltan salas: se vuelve a intentar desde todas, con tiradas nuevas.
				passes++;
				if (passes > MaxPasses)
				{
					return null;
				}

				foreach (Vector2I cell in layout.Cells.Keys)
				{
					pending.Enqueue(cell);
				}
			}

			Vector2I current = pending.Dequeue();
			foreach (Vector2I direction in ShuffledDirections(rng))
			{
				if (layout.Cells.Count >= config.RoomCount)
				{
					break;
				}

				Vector2I candidate = current + direction;
				if (CanOpenRoom(layout, config, candidate, rng))
				{
					layout.Cells[candidate] = RoomType.Normal;
					pending.Enqueue(candidate);
				}
			}
		}

		return AssignSpecialRooms(layout, rng) ? layout : null;
	}

	// Las reglas del paso 2: dentro de la cuadrícula, libre, que no toque a más de una sala, y tirada al azar.
	private static bool CanOpenRoom(FloorLayout layout, FloorConfig config, Vector2I cell, Random rng)
	{
		bool insideGrid = cell.X >= 0 && cell.Y >= 0 && cell.X < config.GridSize.X && cell.Y < config.GridSize.Y;
		if (!insideGrid || layout.Cells.ContainsKey(cell))
		{
			return false;
		}

		if (layout.NeighborCount(cell) > 1)
		{
			return false;
		}

		return rng.NextDouble() < config.SpawnChance;
	}

	// Las 4 direcciones en orden al azar (Fisher-Yates), para que el mapa no crezca siempre hacia el mismo lado.
	private static Vector2I[] ShuffledDirections(Random rng)
	{
		Vector2I[] directions = (Vector2I[])FloorLayout.Directions.Clone();
		for (int i = directions.Length - 1; i > 0; i--)
		{
			int j = rng.Next(i + 1);
			(directions[i], directions[j]) = (directions[j], directions[i]);
		}

		return directions;
	}

	// Paso 4: de las salas sin salida, el jefe es la más lejana al inicio y el tesoro es otra elegida al azar.
	private static bool AssignSpecialRooms(FloorLayout layout, Random rng)
	{
		Dictionary<Vector2I, int> distances = layout.DistancesFromStart();

		List<Vector2I> deadEnds = new List<Vector2I>();
		foreach (Vector2I cell in layout.Cells.Keys)
		{
			if (cell != layout.Start && layout.NeighborCount(cell) == 1)
			{
				deadEnds.Add(cell);
			}
		}

		if (deadEnds.Count < 2)
		{
			return false;
		}

		Vector2I boss = deadEnds[0];
		foreach (Vector2I cell in deadEnds)
		{
			if (distances[cell] > distances[boss])
			{
				boss = cell;
			}
		}

		deadEnds.Remove(boss);
		Vector2I treasure = deadEnds[rng.Next(deadEnds.Count)];

		layout.Cells[boss] = RoomType.Boss;
		layout.Cells[treasure] = RoomType.Treasure;
		return true;
	}

	/// <summary>
	/// Revisa que un mapa cumpla las reglas. Devuelve la lista de problemas (vacía = el mapa es válido).
	/// </summary>
	public static List<string> Validate(FloorLayout layout, FloorConfig config)
	{
		List<string> errors = new List<string>();

		if (layout.Cells.Count != config.RoomCount)
		{
			errors.Add($"hay {layout.Cells.Count} salas y se pedían {config.RoomCount}");
		}

		int starts = 0, bosses = 0, treasures = 0, connections = 0;
		foreach (KeyValuePair<Vector2I, RoomType> room in layout.Cells)
		{
			Vector2I cell = room.Key;
			if (cell.X < 0 || cell.Y < 0 || cell.X >= config.GridSize.X || cell.Y >= config.GridSize.Y)
			{
				errors.Add($"la sala {cell} está fuera de la cuadrícula");
			}

			if (room.Value == RoomType.Start) starts++;
			if (room.Value == RoomType.Boss) bosses++;
			if (room.Value == RoomType.Treasure) treasures++;
			connections += layout.NeighborCount(cell);
		}

		if (starts != 1 || bosses != 1 || treasures != 1)
		{
			errors.Add($"debe haber 1 inicio, 1 jefe y 1 tesoro (hay {starts}, {bosses}, {treasures})");
		}

		// Cada puerta se cuenta desde sus dos salas, por eso se divide entre 2. Un árbol de N salas tiene N-1 puertas.
		if (connections / 2 != layout.Cells.Count - 1)
		{
			errors.Add($"hay {connections / 2} puertas y un mapa sin ciclos de {layout.Cells.Count} salas debería tener {layout.Cells.Count - 1}");
		}

		Dictionary<Vector2I, int> distances = layout.DistancesFromStart();
		if (distances.Count != layout.Cells.Count)
		{
			errors.Add("hay salas que no se alcanzan desde el inicio");
			return errors;
		}

		int farthestDeadEnd = 0;
		foreach (Vector2I cell in layout.Cells.Keys)
		{
			if (cell != layout.Start && layout.NeighborCount(cell) == 1)
			{
				farthestDeadEnd = Mathf.Max(farthestDeadEnd, distances[cell]);
			}
		}

		foreach (KeyValuePair<Vector2I, RoomType> room in layout.Cells)
		{
			if (room.Value == RoomType.Boss || room.Value == RoomType.Treasure)
			{
				if (layout.NeighborCount(room.Key) != 1)
				{
					errors.Add($"la sala {room.Value} en {room.Key} no es una sala sin salida");
				}
			}

			if (room.Value == RoomType.Boss && distances[room.Key] != farthestDeadEnd)
			{
				errors.Add("el jefe no es la sala sin salida más lejana");
			}
		}

		return errors;
	}
}
