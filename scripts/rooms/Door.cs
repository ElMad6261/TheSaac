using Godot;

/// <summary>
/// Puerta entre dos salas. Se abre sola, como en Isaac: cuando se despeja una de las dos salas que une.
/// - Escucha GameEvents.RoomCleared. Si la sala despejada es una de las suyas (Room.EstaJuntoA), abre.
/// - Isaac no la usa con E, y una vez abierta no se vuelve a cerrar: la única animación que corre es la de abrir.
/// - Mientras está cerrada no deja pasar: la colisión de la hoja ("Hoja") sigue a la animación.
///
/// Va en la raíz de puerta.tscn, puerta_jefe.tscn y puerta_tesoro.tscn. Necesita su hijo directo "AnimationPlayer".
/// Las animaciones salen de tools/godot/generar_animaciones_puerta.py ("Cerrar" y "Bloqueada" siguen en la
/// biblioteca por si hacen falta cuando haya enemigos, pero hoy nadie las reproduce).
/// </summary>
public partial class Door : Node3D
{
	/// <summary>Animación con la que abre: "Abrir", o "Desbloquear" en la puerta del tesoro
	/// (la llave gira, se esfuma y la hoja abre).</summary>
	[Export] public StringName AnimacionAbrir { get; set; } = "Abrir";

	/// <summary>La hoja terminó de abrir.</summary>
	[Signal] public delegate void PuertaAbiertaEventHandler();

	/// <summary>True desde que la puerta empieza a abrir (ya no vuelve a cerrarse).</summary>
	public bool Abierta { get; private set; }

	private AnimationPlayer _anim;

	public override void _Ready()
	{
		_anim = GetNode<AnimationPlayer>("AnimationPlayer");
		_anim.AnimationFinished += OnAnimacionTerminada;
		GameEvents.Instance.RoomCleared += OnRoomCleared;
	}

	public override void _ExitTree()
	{
		// GameEvents vive toda la partida y la puerta no: al salir del árbol hay que soltarse de la señal.
		if (IsInstanceValid(GameEvents.Instance))
		{
			GameEvents.Instance.RoomCleared -= OnRoomCleared;
		}
	}

	private void OnRoomCleared(Room sala)
	{
		// Cada puerta está en la pared que comparten dos salas: abre si se despejó cualquiera de las dos.
		if (sala.EstaJuntoA(GlobalPosition))
		{
			Abrir();
		}
	}

	/// <summary>Abre la puerta (una sola vez). También lo puede llamar otro objeto, por ejemplo un interruptor.</summary>
	public void Abrir()
	{
		if (Abierta)
		{
			return;
		}

		Abierta = true;
		_anim.Play(AnimacionAbrir);
	}

	private void OnAnimacionTerminada(StringName nombre)
	{
		if (nombre == AnimacionAbrir)
		{
			EmitSignal(SignalName.PuertaAbierta);
		}
	}
}
