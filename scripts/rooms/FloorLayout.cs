using System.Collections.Generic;
using System.Text;
using Godot;

/// <summary>
/// Resultado del generador: qué sala hay en cada celda de la cuadrícula. Es solo información, no crea nodos.
///
/// Regla clave del generador: una sala nueva nunca toca a más de una sala ya puesta. Por eso dos salas pegadas
/// siempre están unidas por una puerta, y las puertas de una sala salen de sus vecinas:
/// HasNeighbor(celda, North) → DoorNorth de esa sala, y así con las demás direcciones.
/// </summary>
public class FloorLayout
{
	// Direcciones en la cuadrícula. Norte es -Z en el mundo, igual que en Room.cs y la cámara.
	public static readonly Vector2I North = new Vector2I(0, -1);
	public static readonly Vector2I South = new Vector2I(0, 1);
	public static readonly Vector2I East = new Vector2I(1, 0);
	public static readonly Vector2I West = new Vector2I(-1, 0);
	public static readonly Vector2I[] Directions = { North, South, East, West };

	/// <summary>Semilla con la que se generó. Con la misma semilla y el mismo FloorConfig sale el mismo mapa.</summary>
	public int Seed { get; }

	/// <summary>Celda de la sala inicial (el centro de la cuadrícula).</summary>
	public Vector2I Start { get; }

	/// <summary>Tipo de sala de cada celda ocupada.</summary>
	public Dictionary<Vector2I, RoomType> Cells { get; } = new Dictionary<Vector2I, RoomType>();

	public FloorLayout(int seed, Vector2I start)
	{
		Seed = seed;
		Start = start;
	}

	/// <summary>¿Hay una sala en la celda pegada a esta, en esa dirección?</summary>
	public bool HasNeighbor(Vector2I cell, Vector2I direction)
	{
		return Cells.ContainsKey(cell + direction);
	}

	/// <summary>Cuántas salas tocan a esta celda (0 a 4).</summary>
	public int NeighborCount(Vector2I cell)
	{
		int count = 0;
		foreach (Vector2I direction in Directions)
		{
			if (HasNeighbor(cell, direction))
			{
				count++;
			}
		}

		return count;
	}

	/// <summary>Posición de la sala en el nivel, con la sala inicial en (0, 0, 0): cada celda son 12 m en X y 8 m en Z.</summary>
	public Vector3 ToWorld(Vector2I cell, Vector2 cellSize)
	{
		return new Vector3((cell.X - Start.X) * cellSize.X, 0, (cell.Y - Start.Y) * cellSize.Y);
	}

	/// <summary>Cuántas salas hay que cruzar desde la inicial hasta cada celda (búsqueda en anchura).</summary>
	public Dictionary<Vector2I, int> DistancesFromStart()
	{
		Dictionary<Vector2I, int> distances = new Dictionary<Vector2I, int>();
		Queue<Vector2I> pending = new Queue<Vector2I>();
		distances[Start] = 0;
		pending.Enqueue(Start);

		while (pending.Count > 0)
		{
			Vector2I cell = pending.Dequeue();
			foreach (Vector2I direction in Directions)
			{
				Vector2I next = cell + direction;
				if (Cells.ContainsKey(next) && !distances.ContainsKey(next))
				{
					distances[next] = distances[cell] + 1;
					pending.Enqueue(next);
				}
			}
		}

		return distances;
	}

	/// <summary>Dibujo del mapa en texto para depurar: I inicio, J jefe, T tesoro, N normal; "-" y "|" son puertas.</summary>
	public string ToAscii()
	{
		int minX = int.MaxValue, minY = int.MaxValue, maxX = int.MinValue, maxY = int.MinValue;
		foreach (Vector2I cell in Cells.Keys)
		{
			minX = Mathf.Min(minX, cell.X);
			maxX = Mathf.Max(maxX, cell.X);
			minY = Mathf.Min(minY, cell.Y);
			maxY = Mathf.Max(maxY, cell.Y);
		}

		StringBuilder text = new StringBuilder();
		for (int y = minY; y <= maxY; y++)
		{
			StringBuilder rooms = new StringBuilder();   // salas de esta fila, con "-" entre las conectadas
			StringBuilder links = new StringBuilder();   // "|" hacia la fila de abajo
			for (int x = minX; x <= maxX; x++)
			{
				Vector2I cell = new Vector2I(x, y);
				bool exists = Cells.TryGetValue(cell, out RoomType type);
				rooms.Append(exists ? Letter(type) : ' ');
				rooms.Append(exists && HasNeighbor(cell, East) ? '-' : ' ');
				links.Append(exists && HasNeighbor(cell, South) ? '|' : ' ');
				links.Append(' ');
			}

			text.AppendLine(rooms.ToString().TrimEnd());
			if (y < maxY)
			{
				text.AppendLine(links.ToString().TrimEnd());
			}
		}

		return text.ToString();
	}

	private static char Letter(RoomType type)
	{
		switch (type)
		{
			case RoomType.Start: return 'I';
			case RoomType.Boss: return 'J';
			case RoomType.Treasure: return 'T';
			default: return 'N';
		}
	}
}
