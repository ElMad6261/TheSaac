using Godot;

/// <summary>
/// Sala: va en la raíz de cada escena de sala (scenes/rooms/*.tscn).
///
/// - Su hijo "Zona" (Area3D con una caja "Forma") cubre el interior. Cuando Isaac entra, la sala lo avisa
///   con GameEvents.RoomEntered; la cámara escucha esa señal para encuadrar esta sala.
/// - El centro de cada pared queda libre, marcado con un nodo en "Huecos" (Norte, Sur, Este, Oeste).
///   Al arrancar, la sala pone ahí un vano (si hay sala vecina de ese lado) o un muro sólido (si no hay),
///   según DoorNorth, DoorSouth, DoorEast y DoorWest. Así el generador de pisos solo tiene que marcar esas casillas.
/// - Entre dos salas vecinas hay un solo paso con dos vanos (uno en la pared de cada sala) y UNA puerta:
///   la pone la sala de abajo (vano norte) o la de la derecha (vano oeste). Su hoja abre hacia afuera, hacia la sala
///   vecina, y cabe en el hueco entre las dos paredes, así que se abre igual desde cualquiera de las dos salas.
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

	/// <summary>Puerta que va dentro del vano norte y del oeste (scenes/props/puerta/puerta.tscn).
	/// Si se deja vacía, los vanos quedan abiertos, sin hoja.</summary>
	[Export] public PackedScene DoorScene { get; set; }

	/// <summary>Mitad del interior de la sala en X y en Z (metros). Sale del tamaño de la caja de "Zona".</summary>
	public Vector2 HalfSize { get; private set; }

	public override void _Ready()
	{
		Area3D zone = GetNode<Area3D>("Zona");
		BoxShape3D box = (BoxShape3D)zone.GetNode<CollisionShape3D>("Forma").Shape;
		HalfSize = new Vector2(box.Size.X, box.Size.Z) / 2;
		zone.BodyEntered += OnBodyEntered;

		BuildWallCenter("Huecos/Norte", DoorNorth, withDoor: true);
		BuildWallCenter("Huecos/Sur", DoorSouth, withDoor: false);
		BuildWallCenter("Huecos/Este", DoorEast, withDoor: false);
		BuildWallCenter("Huecos/Oeste", DoorWest, withDoor: true);
	}

	/// <summary>Pone un vano o un muro sólido en el centro de una pared y, si toca, la puerta dentro del vano.
	/// Si la escena no tiene ese marcador (por ejemplo, una sala graybox), no hace nada.</summary>
	private void BuildWallCenter(string markerPath, bool hasNeighbor, bool withDoor)
	{
		Node3D marker = GetNodeOrNull<Node3D>(markerPath);
		PackedScene module = hasNeighbor ? DoorwayScene : SolidWallScene;
		if (marker == null || module == null)
		{
			return;
		}

		marker.AddChild(module.Instantiate());

		// El marco de la puerta (1.5 m de ancho y 2.5 m de alto) llena justo la abertura del vano.
		// El -Z del marcador apunta hacia afuera de la sala, que es hacia donde gira la hoja.
		if (hasNeighbor && withDoor && DoorScene != null)
		{
			marker.AddChild(DoorScene.Instantiate());
		}
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
