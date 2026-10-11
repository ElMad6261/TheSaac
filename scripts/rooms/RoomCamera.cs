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
/// Proyección: por defecto perspectiva con poco ángulo (Fov 32), que deja ver las paredes de los lados.
/// Para una vista isométrica pura, en el Inspector de la Camera3D: Projection = Orthogonal y Size ≈ 8.7
/// (con Pitch 55 y FocusOffset (0, 1, -0.9) queda bien encuadrada).
/// </summary>
public partial class RoomCamera : Camera3D
{
	/// <summary>Grupo de lo que la cámara puede esconder: muros, pilares, puertas y antorchas de las paredes.</summary>
	public const string WallGroup = "muros";

	/// <summary>Inclinación hacia abajo, en grados (90 = vista desde arriba del todo).</summary>
	[Export(PropertyHint.Range, "30,90,1")]
	public float Pitch { get; set; } = 60.0f;

	/// <summary>Distancia de la cámara al punto que encuadra, en metros.</summary>
	[Export] public float Distance { get; set; } = 17.0f;

	/// <summary>Punto que se encuadra, relativo al centro de la sala. Subirlo o moverlo al norte (-Z) muestra más pared de arriba.</summary>
	[Export] public Vector3 FocusOffset { get; set; } = new Vector3(0, 0.6f, -0.45f);

	/// <summary>Segundos que tarda en deslizarse de una sala a otra.</summary>
	[Export] public float TransitionTime { get; set; } = 0.4f;

	/// <summary>Metros al sur del borde interior de la sala que se esconden: alcanza su muro sur y el muro norte de la sala vecina.</summary>
	[Export] public float CutawayDepth { get; set; } = 1.6f;

	private Tween _tween;
	private bool _hasRoom;

	public override void _Ready()
	{
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
		_tween?.Kill();   // si iba a otra sala, se cancela y sale desde donde está

		if (!_hasRoom)
		{
			// Primera sala del nivel: aparece ahí directamente, sin deslizarse.
			GlobalPosition = target;
			_hasRoom = true;
		}
		else
		{
			_tween = CreateTween();
			_tween.TweenProperty(this, "global_position", target, TransitionTime)
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
