using Godot;

/// <summary>
/// Sala: va en la raíz de cada escena de sala (scenes/rooms/*.tscn).
///
/// - Su hijo "Zona" (Area3D con una caja "Forma") cubre el interior. Cuando Isaac entra, la sala lo avisa
///   con GameEvents.RoomEntered; la cámara escucha esa señal para encuadrar esta sala.
/// - El centro de cada pared queda libre, marcado con un nodo en "Huecos" (Norte, Sur, Este, Oeste).
///   Al arrancar, la sala pone ahí un vano (si hay sala vecina de ese lado) o un muro sólido (si no hay),
///   según DoorNorth, DoorSouth, DoorEast y DoorWest. Así el generador de pisos solo tiene que marcar esas casillas.
///
/// Más adelante aquí van los estados del plan (sin visitar → en combate → despejada) y la señal RoomCleared.
/// </summary>
public partial class Room : Node3D
{
	[ExportGroup("Puertas")]
	/// <summary>Hay sala vecina al norte (-Z): en el centro de esa pared va un vano.</summary>
	[Export] public bool DoorNorth { get; set; }

	/// <summary>Hay sala vecina al sur (+Z).</summary>
	[Export] public bool DoorSouth { get; set; }

	/// <summary>Hay sala vecina al este (+X).</summary>
	[Export] public bool DoorEast { get; set; }

	/// <summary>Hay sala vecina al oeste (-X).</summary>
	[Export] public bool DoorWest { get; set; }

	/// <summary>Módulo que va en el centro de una pared sin vecina (scenes/rooms/modulos/muro.tscn).</summary>
	[Export] public PackedScene SolidWallScene { get; set; }

	/// <summary>Módulo que va en el centro de una pared con vecina (scenes/rooms/modulos/muro_vano.tscn).</summary>
	[Export] public PackedScene DoorwayScene { get; set; }

	/// <summary>Mitad del interior de la sala en X y en Z (metros). Sale del tamaño de la caja de "Zona".</summary>
	public Vector2 HalfSize { get; private set; }

	public override void _Ready()
	{
		Area3D zone = GetNode<Area3D>("Zona");
		BoxShape3D box = (BoxShape3D)zone.GetNode<CollisionShape3D>("Forma").Shape;
		HalfSize = new Vector2(box.Size.X, box.Size.Z) / 2;
		zone.BodyEntered += OnBodyEntered;

		BuildWallCenter("Huecos/Norte", DoorNorth);
		BuildWallCenter("Huecos/Sur", DoorSouth);
		BuildWallCenter("Huecos/Este", DoorEast);
		BuildWallCenter("Huecos/Oeste", DoorWest);
	}

	/// <summary>Pone un vano o un muro sólido en el centro de una pared.
	/// Si la escena no tiene ese marcador (por ejemplo, una sala graybox), no hace nada.</summary>
	private void BuildWallCenter(string markerPath, bool hasNeighbor)
	{
		Node3D marker = GetNodeOrNull<Node3D>(markerPath);
		PackedScene module = hasNeighbor ? DoorwayScene : SolidWallScene;
		if (marker == null || module == null)
		{
			return;
		}

		marker.AddChild(module.Instantiate());
	}

	private void OnBodyEntered(Node3D body)
	{
		// La zona solo mira la capa 2 (Jugador), pero se revisa el grupo por si algún día entra otra cosa.
		if (body.IsInGroup("jugador"))
		{
			GameEvents.Instance.EmitSignal(GameEvents.SignalName.RoomEntered, this);
		}
	}
}
