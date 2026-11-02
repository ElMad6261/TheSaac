using System.Collections.Generic;
using System.Text;
using Godot;

/// <summary>
/// Herramienta de prueba, no es parte del juego: genera muchos mapas, los valida y devuelve un resumen en texto.
/// Se usa con el juego corriendo (godot_exec o un script cualquiera):
///   var t = load("res://scripts/debug/FloorGeneratorTest.cs").new()
///   print(t.Run("res://data/floors/basement_1.tres", 200, 0))
/// </summary>
public partial class FloorGeneratorTest : Node
{
	/// <summary>Prueba las semillas 1..count con el FloorConfig de configPath.
	/// Si roomCount es mayor que 0, prueba con ese número de salas en vez del del .tres (sin guardarlo).</summary>
	public string Run(string configPath, int count, int roomCount)
	{
		FloorConfig config = ResourceLoader.Load<FloorConfig>(configPath);
		if (config == null)
		{
			return "No se pudo cargar " + configPath;
		}

		int originalRoomCount = config.RoomCount;
		if (roomCount > 0)
		{
			config.RoomCount = roomCount;
		}

		int failures = 0;
		HashSet<string> distinctMaps = new HashSet<string>();
		StringBuilder problems = new StringBuilder();

		for (int seed = 1; seed <= count; seed++)
		{
			FloorLayout layout = FloorGenerator.Generate(config, seed);
			if (layout == null)
			{
				failures++;
				problems.AppendLine($"semilla {seed}: no se pudo generar");
				continue;
			}

			List<string> errors = FloorGenerator.Validate(layout, config);
			if (errors.Count > 0)
			{
				failures++;
				problems.AppendLine($"semilla {seed}: " + string.Join("; ", errors));
			}

			distinctMaps.Add(layout.ToAscii());
		}

		// Misma semilla = mismo mapa.
		bool repeatable = FloorGenerator.Generate(config, 42).ToAscii() == FloorGenerator.Generate(config, 42).ToAscii();

		StringBuilder report = new StringBuilder();
		report.AppendLine($"{config.FloorName} con {config.RoomCount} salas: {count} semillas, {failures} con problemas, {distinctMaps.Count} mapas distintos, misma semilla repite el mapa: {repeatable}");
		report.Append(problems);
		for (int seed = 1; seed <= 3; seed++)
		{
			report.AppendLine($"--- semilla {seed} ---");
			report.Append(FloorGenerator.Generate(config, seed).ToAscii());
		}

		config.RoomCount = originalRoomCount;   // el recurso queda como estaba
		return report.ToString();
	}

	/// <summary>
	/// Ruta para caminar de la sala inicial a la primera sala del tipo pedido (0 normal, 1 inicio, 2 tesoro, 3 jefe):
	/// el centro de cada sala del camino, en metros del mundo. Sirve para que un bot de prueba recorra el piso.
	/// </summary>
	public Vector3[] Route(string configPath, int seed, int roomType)
	{
		FloorConfig config = ResourceLoader.Load<FloorConfig>(configPath);
		FloorLayout layout = FloorGenerator.Generate(config, seed);

		// Búsqueda en anchura guardando de qué sala se llegó a cada una, para reconstruir el camino al final.
		Dictionary<Vector2I, Vector2I> cameFrom = new Dictionary<Vector2I, Vector2I>();
		Queue<Vector2I> pending = new Queue<Vector2I>();
		cameFrom[layout.Start] = layout.Start;
		pending.Enqueue(layout.Start);
		Vector2I? target = null;

		while (pending.Count > 0 && target == null)
		{
			Vector2I cell = pending.Dequeue();
			if ((int)layout.Cells[cell] == roomType)
			{
				target = cell;
				break;
			}

			foreach (Vector2I direction in FloorLayout.Directions)
			{
				Vector2I next = cell + direction;
				if (layout.Cells.ContainsKey(next) && !cameFrom.ContainsKey(next))
				{
					cameFrom[next] = cell;
					pending.Enqueue(next);
				}
			}
		}

		List<Vector3> route = new List<Vector3>();
		if (target == null)
		{
			return route.ToArray();
		}

		Vector2I step = target.Value;
		while (step != layout.Start)
		{
			route.Add(layout.ToWorld(step, config.CellSize));
			step = cameFrom[step];
		}

		route.Add(layout.ToWorld(layout.Start, config.CellSize));
		route.Reverse();
		return route.ToArray();
	}
}
