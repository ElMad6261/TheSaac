using System;
using System.Collections.Generic;
using Godot;

/// <summary>
/// Arma un piso aleatorio: va en la raíz de scenes/rooms/nivel_aleatorio.tscn.
/// Pide el mapa a FloorGenerator y, por cada celda, instancia una sala del tipo que toca (FloorConfig.PickRoom)
/// dentro del nodo "Salas". Antes de agregarla pone sus puertas según las salas vecinas:
/// Room.cs arma los vanos en _Ready, así que las banderas tienen que estar puestas antes de AddChild.
/// Después coloca a Isaac en la sala inicial.
/// </summary>
public partial class FloorLoader : Node3D
{
	/// <summary>Datos del piso: data/floors/basement_1.tres.</summary>
	[Export] public FloorConfig Floor { get; set; }

	/// <summary>Semilla del mapa. Con un número distinto de 0 sale siempre el mismo piso (útil para la demo). Con 0 se usa la del GameState o, si no hay, una al azar.</summary>
	[Export] public int Seed { get; set; }

	// Dónde aparece Isaac respecto al centro de la sala inicial (un poco al sur, mirando a la sala).
	private static readonly Vector3 PlayerSpawnOffset = new Vector3(0, 0.05f, 1);

	public override void _Ready()
	{
		// Manda la semilla del Inspector; si no hay, se repite la del GameState (por ejemplo al reintentar el piso);
		// si tampoco hay, Build elige una al azar.
		Build(Seed != 0 ? Seed : GameState.Instance.Seed);
	}

	/// <summary>Arma el piso con esa semilla (0 = al azar). Si ya había uno armado, lo reemplaza.</summary>
	public void Build(int seed)
	{
		if (Floor == null)
		{
			GD.PushError("FloorLoader: falta asignar el FloorConfig (data/floors/basement_1.tres).");
			return;
		}

		if (seed == 0)
		{
			seed = (int)(GD.Randi() % 1000000) + 1;
		}

		FloorLayout layout = FloorGenerator.Generate(Floor, seed);
		if (layout == null)
		{
			return;
		}

		GameState.Instance.StartFloor(Floor, seed);

		// Se quitan las salas del piso anterior (RemoveChild primero para que desaparezcan en este mismo cuadro).
		Node3D rooms = GetNode<Node3D>("Salas");
		foreach (Node old in rooms.GetChildren())
		{
			rooms.RemoveChild(old);
			old.QueueFree();
		}

		// Otro generador de azar para elegir qué escena va en cada celda (separado del que arma el mapa).
		Random rng = new Random(seed + 1);
		foreach (KeyValuePair<Vector2I, RoomType> cell in layout.Cells)
		{
			RoomData data = Floor.PickRoom(cell.Value, rng);
			if (data == null || data.Scene == null)
			{
				GD.PushError($"FloorLoader: el piso no tiene ninguna sala de tipo {cell.Value}.");
				continue;
			}

			Room room = data.Scene.Instantiate<Room>();
			room.Name = $"Sala_{cell.Key.X}_{cell.Key.Y}_{cell.Value}";
			room.Position = layout.ToWorld(cell.Key, Floor.CellSize);
			room.DoorNorth = layout.HasNeighbor(cell.Key, FloorLayout.North);
			room.DoorSouth = layout.HasNeighbor(cell.Key, FloorLayout.South);
			room.DoorEast = layout.HasNeighbor(cell.Key, FloorLayout.East);
			room.DoorWest = layout.HasNeighbor(cell.Key, FloorLayout.West);
			rooms.AddChild(room);
		}

		CharacterBody3D player = GetNode<CharacterBody3D>("Jugador");
		player.Position = layout.ToWorld(layout.Start, Floor.CellSize) + PlayerSpawnOffset;
		player.Velocity = Vector3.Zero;

		GD.Print($"{Floor.FloorName}, semilla {seed}:\n{layout.ToAscii()}");
	}
}
