using Godot;

/// <summary>
/// Cámara 2.5D estilo The Binding of Isaac: fija, mirando hacia el norte (-Z) desde arriba,
/// encuadra la sala donde está Isaac. Cuando Isaac entra a otra sala (GameEvents.RoomEntered),
/// se desliza hasta ella.
///
/// También esconde lo que queda entre la cámara y la sala (el lado sur): los nodos del grupo "muros"
/// que están en esa franja pasan a "solo sombra". No se ven, pero siguen dando sombra y chocando.
/// Así la pared de abajo no tapa a Isaac, como en el juego original.
///
/// Proyección: ortográfica siempre (sin perspectiva, sin la "cuña" que juntaba las paredes en diagonal
/// hacia el fondo). El tamaño del encuadre (Size) no es un número fijo: se recalcula en cada sala a
/// partir de HalfSize y de WallHeight, para que la zona jugable llene la pantalla aunque cambie el
/// tamaño de la sala.
/// </summary>
public partial class RoomCamera : Camera3D
{
	/// <summary>Grupo de lo que la cámara puede esconder: muros, pilares, puertas y antorchas de las paredes.</summary>
	public const string WallGroup = "muros";

	/// <summary>Inclinación hacia abajo, en grados (90 = vista desde arriba del todo). Rango recomendado: 60-70.</summary>
	[Export(PropertyHint.Range, "30,90,1")]
	public float Pitch { get; set; } = 65.0f;

	/// <summary>Distancia de la cámara al punto que encuadra, en metros. Con proyección ortográfica no cambia
	/// el tamaño en pantalla: solo tiene que ser grande para que nada quede delante del plano cercano.</summary>
	[Export] public float Distance { get; set; } = 17.0f;

	/// <summary>Punto que se encuadra, relativo al centro de la sala. Subirlo o moverlo al norte (-Z) muestra más pared de arriba.</summary>
	[Export] public Vector3 FocusOffset { get; set; } = new Vector3(0, 0.5f, -0.3f);

	/// <summary>Altura de las paredes del kit, en metros (ver BoxShape3D de scenes/rooms/modulos/muro.tscn).
	/// Sirve para calcular cuánto encuadre vertical hace falta para que no se corten.</summary>
	[Export] public float WallHeight { get; set; } = 2.7f;

	/// <summary>Metros de margen horizontal más allá del interior de la sala (HalfSize.X), para que entren
	/// los pilares de las esquinas sin quedar pegados al borde de la pantalla.</summary>
	[Export] public float WallMargin { get; set; } = 0.5f;

	/// <summary>Margen general del encuadre: 1.0 deja la zona jugable tocando el borde de la pantalla;
	/// un poco más (ej. 1.12) da algo de aire sin perder tamaño.</summary>
	[Export] public float FrameMargin { get; set; } = 1.12f;

	/// <summary>Segundos que tarda en deslizarse de una sala a otra.</summary>
	[Export] public float TransitionTime { get; set; } = 0.4f;

	/// <summary>Metros al sur del borde interior de la sala que se esconden: alcanza su muro sur y el muro norte de la sala vecina.</summary>
	[Export] public float CutawayDepth { get; set; } = 1.6f;

	private Tween _tween;
	private bool _hasRoom;

	public override void _Ready()
	{
		Projection = ProjectionType.Orthogonal;        // sin perspectiva: paredes y ejes paralelos, como el original
		RotationDegrees = new Vector3(-Pitch, 0, 0);   // mira hacia el norte (-Z), inclinada hacia abajo
		GameEvents.Instance.RoomEntered += OnRoomEntered;
	}

	public override void _ExitTree()
	{
		// Al cerrar el juego el autoload puede irse antes que la cámara: solo se desconecta si sigue vivo.
		if (IsInstanceValid(GameEvents.Instance))
		{
			GameEvents.Instance.RoomEntered -= OnRoomEntered;
		}
	}

	private void OnRoomEntered(Room room)
	{
		Vector3 target = PositionFor(room);
		float targetSize = SizeFor(room);
		_tween?.Kill();   // si iba a otra sala, se cancela y sale desde donde está

		if (!_hasRoom)
		{
			// Primera sala del nivel: aparece ahí directamente, sin deslizarse.
			GlobalPosition = target;
			Size = targetSize;
			_hasRoom = true;
		}
		else
		{
			_tween = CreateTween();
			_tween.TweenProperty(this, "global_position", target, TransitionTime)
				.SetTrans(Tween.TransitionType.Sine)
				.SetEase(Tween.EaseType.InOut);
			// En paralelo, por si la sala vecina es de otro tamaño: el encuadre cambia a la vez que se desliza.
			_tween.Parallel().TweenProperty(this, "size", targetSize, TransitionTime)
				.SetTrans(Tween.TransitionType.Sine)
				.SetEase(Tween.EaseType.InOut);
		}

		UpdateCutaway(room);
	}

	/// <summary>Dónde va la cámara para encuadrar la sala: hacia atrás (sur, +Z) y hacia arriba del punto de enfoque.</summary>
	private Vector3 PositionFor(Room room)
	{
		float pitch = Mathf.DegToRad(Pitch);
		Vector3 backAndUp = new Vector3(0, Mathf.Sin(pitch), Mathf.Cos(pitch));
		return room.GlobalPosition + FocusOffset + backAndUp * Distance;
	}

	/// <summary>
	/// Tamaño ortográfico (alto total del encuadre, en metros) que hace falta para que quepan la sala y
	/// sus paredes, sin recortes.
	///
	/// La cámara solo gira en X (Pitch), nunca en Y: su eje horizontal de pantalla es siempre el eje X
	/// del mundo tal cual, y su eje vertical de pantalla es una mezcla de Z (el fondo de la sala) y de Y
	/// (la altura de pared), según el ángulo. Por trigonometría, un metro de fondo de sala ocupa
	/// sin(Pitch) metros de encuadre vertical, y un metro de alto de pared ocupa cos(Pitch): a 90°
	/// (mirando derecho hacia abajo) toda la altura de pared desaparece y el fondo se ve a tamaño real;
	/// a 0° (de lado) es al revés.
	/// </summary>
	private float SizeFor(Room room)
	{
		float pitch = Mathf.DegToRad(Pitch);

		// Vertical de pantalla: el fondo de la sala completo (norte + sur) más la altura de una pared.
		float verticalNeeded = room.HalfSize.Y * 2f * Mathf.Sin(pitch) + WallHeight * Mathf.Cos(pitch);

		// Horizontal de pantalla: el ancho de la sala más el margen de los pilares de las esquinas.
		float horizontalNeeded = (room.HalfSize.X + WallMargin) * 2f;

		Vector2 viewport = GetViewport().GetVisibleRect().Size;
		float aspect = viewport.Y > 0f ? viewport.X / viewport.Y : 16f / 9f;

		// Camera3D.Size es el alto del encuadre (keep_height); el ancho sale de dividir por el aspecto.
		// Se toma el que pida más tamaño, para que ninguno de los dos quede cortado.
		float sizeForHeight = verticalNeeded * FrameMargin;
		float sizeForWidth = horizontalNeeded * FrameMargin / aspect;
		return Mathf.Max(sizeForHeight, sizeForWidth);
	}

	/// <summary>Esconde los nodos del grupo "muros" que están en la franja sur de la sala y muestra todos los demás.</summary>
	private void UpdateCutaway(Room room)
	{
		Vector3 center = room.GlobalPosition;
		float southEdge = center.Z + room.HalfSize.Y;   // en Godot el sur es +Z: el lado de la cámara

		foreach (Node node in GetTree().GetNodesInGroup(WallGroup))
		{
			if (node is not Node3D wall)
			{
				continue;
			}

			Vector3 p = wall.GlobalPosition;
			bool betweenCameraAndRoom = p.Z >= southEdge && p.Z <= southEdge + CutawayDepth
				&& Mathf.Abs(p.X - center.X) <= room.HalfSize.X + 1.0f;
			SetHidden(wall, betweenCameraAndRoom);
		}
	}

	/// <summary>Pone "solo sombra" (o lo devuelve a normal) en el nodo y en todo lo que cuelga de él:
	/// un muro del kit trae sus mallas como hijos.</summary>
	private static void SetHidden(Node node, bool hidden)
	{
		if (node is GeometryInstance3D geometry)
		{
			geometry.CastShadow = hidden
				? GeometryInstance3D.ShadowCastingSetting.ShadowsOnly
				: GeometryInstance3D.ShadowCastingSetting.On;
		}

		foreach (Node child in node.GetChildren())
		{
			SetHidden(child, hidden);
		}
	}
}
