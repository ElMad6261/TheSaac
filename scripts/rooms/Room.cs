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
/// - Una sala empieza sin despejar. Cuando Isaac entra y no hay enemigos dentro (nodos del grupo "enemigos"),
///   se despeja: avisa con GameEvents.RoomCleared (las puertas de esa sala se abren) y, si tiene un
///   PremioAlDespejar, lo suelta: cae desde arriba en el centro de la sala (o en el hijo "PuntoPremio", si existe).
///   Cuando haya enemigos, quien los maneje llama a Despejar() al morir el último.
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

	/// <summary>Puerta distinta solo para el vano norte (por ejemplo puerta_jefe.tscn si al norte está el jefe).
	/// Vacía = se usa DoorScene.</summary>
	[Export] public PackedScene DoorSceneNorth { get; set; }

	/// <summary>Puerta distinta solo para el vano oeste (por ejemplo puerta_tesoro.tscn). Vacía = se usa DoorScene.</summary>
	[Export] public PackedScene DoorSceneWest { get; set; }

	[ExportGroup("Al despejar")]
	/// <summary>Recogible que cae del cielo cuando la sala se despeja (scenes/items/bomba_recogible.tscn). Vacío = nada.</summary>
	[Export] public PackedScene PremioAlDespejar { get; set; }

	/// <summary>True cuando la sala ya no tiene enemigos: sus puertas están abiertas.</summary>
	public bool Despejada { get; private set; }

	// Hasta dónde llega una sala para saber si una puerta es suya: su interior más este margen (m).
	// Alcanza la pared propia y la mitad del hueco de 1 m hacia la sala vecina, donde gira la hoja.
	private const float MargenPuertas = 1.6f;

	/// <summary>Mitad del interior de la sala en X y en Z (metros). Sale del tamaño de la caja de "Zona".</summary>
	public Vector2 HalfSize { get; private set; }

	public override void _Ready()
	{
		Area3D zone = GetNode<Area3D>("Zona");
		BoxShape3D box = (BoxShape3D)zone.GetNode<CollisionShape3D>("Forma").Shape;
		HalfSize = new Vector2(box.Size.X, box.Size.Z) / 2;
		zone.BodyEntered += OnBodyEntered;

		BuildWallCenter("Huecos/Norte", DoorNorth, DoorSceneNorth ?? DoorScene);
		BuildWallCenter("Huecos/Sur", DoorSouth, null);
		BuildWallCenter("Huecos/Este", DoorEast, null);
		BuildWallCenter("Huecos/Oeste", DoorWest, DoorSceneWest ?? DoorScene);
	}

	/// <summary>Pone un vano o un muro sólido en el centro de una pared y, si toca, la puerta dentro del vano.
	/// Si la escena no tiene ese marcador (por ejemplo, una sala graybox), no hace nada.
	/// doorScene = la puerta que va en ese vano, o null si ese lado no lleva puerta (sur y este).</summary>
	private void BuildWallCenter(string markerPath, bool hasNeighbor, PackedScene doorScene)
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
		if (hasNeighbor && doorScene != null)
		{
			marker.AddChild(doorScene.Instantiate());
		}
	}

	private void OnBodyEntered(Node3D body)
	{
		// La zona solo mira la capa 2 (Jugador), pero se revisa el grupo por si algún día entra otra cosa.
		if (body.IsInGroup("jugador"))
		{
			GameEvents.Instance.EmitSignal(GameEvents.SignalName.RoomEntered, this);

			// Sin enemigos dentro, la sala se despeja en cuanto Isaac entra.
			if (!Despejada && !TieneEnemigos())
			{
				Despejar();
			}
		}
	}

	/// <summary>Marca la sala como despejada: avisa a las puertas y suelta el premio. Solo pasa una vez.</summary>
	public void Despejar()
	{
		if (Despejada)
		{
			return;
		}

		Despejada = true;
		GameEvents.Instance.EmitSignal(GameEvents.SignalName.RoomCleared, this);

		if (PremioAlDespejar != null)
		{
			// Diferido: esto puede venir de la señal de la zona (física) y ahí no se pueden crear áreas nuevas.
			Callable.From(SoltarPremio).CallDeferred();
		}
	}

	/// <summary>True si el punto (global) está dentro de la sala o pegado a sus paredes. Lo usan las puertas
	/// para saber si son de esta sala: cada puerta está en la pared que comparten dos salas vecinas.</summary>
	public bool EstaJuntoA(Vector3 punto)
	{
		Vector3 local = ToLocal(punto);
		return Mathf.Abs(local.X) <= HalfSize.X + MargenPuertas && Mathf.Abs(local.Z) <= HalfSize.Y + MargenPuertas;
	}

	// Enemigos = nodos del grupo "enemigos" que estén dentro de esta sala (hijos, nietos...).
	private bool TieneEnemigos()
	{
		foreach (Node enemigo in GetTree().GetNodesInGroup("enemigos"))
		{
			if (IsAncestorOf(enemigo))
			{
				return true;
			}
		}
		return false;
	}

	private void SoltarPremio()
	{
		Node3D premio = PremioAlDespejar.Instantiate<Node3D>();
		AddChild(premio);

		// Cae en el centro de la sala, o donde diga el hijo "PuntoPremio" si la sala tiene el centro ocupado.
		Node3D punto = GetNodeOrNull<Node3D>("PuntoPremio");
		premio.Position = punto != null ? punto.Position : Vector3.Zero;

		if (premio is IDrop drop)
		{
			drop.CaerDesdeArriba();
		}
	}
}
