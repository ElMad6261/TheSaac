using Godot;

/// <summary>
/// Coloca bombas. Va en Isaac (scenes/player/jugador.tscn → Bombas).
/// - Con E (acción "interact") deja una bomba encendida a sus pies, si le queda alguna en GameState.
/// - La E también abre puertas y enciende antorchas: si el Interactor tiene algo cerca para usar,
///   la tecla es de ese objeto y aquí no se hace nada. Sin nada cerca, E = bomba.
/// - Entre una bomba y la siguiente hay que esperar SegundosEntreBombas.
/// </summary>
public partial class BombPlacer : Node
{
	/// <summary>Escena de la bomba encendida (scenes/items/bomba.tscn).</summary>
	[Export] public PackedScene EscenaBomba { get; set; }

	/// <summary>Espera mínima entre dos bombas, para no soltar varias de un solo toque.</summary>
	[Export] public float SegundosEntreBombas { get; set; } = 0.35f;

	private Node3D _jugador;
	private Interactor _interactor;
	private double _espera;   // segundos que faltan para poder colocar otra

	public override void _Ready()
	{
		_jugador = GetParent<Node3D>();
		_interactor = _jugador.GetNodeOrNull<Interactor>("Interactor");
	}

	public override void _Process(double delta)
	{
		if (_espera > 0)
		{
			_espera -= delta;
		}
	}

	public override void _UnhandledInput(InputEvent evento)
	{
		if (!evento.IsActionPressed("interact") || evento.IsEcho())
		{
			return;
		}

		// Hay una puerta o antorcha al alcance: la E es para ella (la usa Interactor.cs).
		if (_interactor != null && _interactor.TieneObjetivo)
		{
			return;
		}

		if (_espera > 0 || EscenaBomba == null)
		{
			return;
		}

		// GastarBomba devuelve false si Isaac no tiene ninguna.
		if (!GameState.Instance.GastarBomba())
		{
			return;
		}

		// La bomba queda como hermana de Isaac (en el nivel), no como hija: así no se mueve con él.
		Node3D bomba = EscenaBomba.Instantiate<Node3D>();
		_jugador.GetParent().AddChild(bomba);
		bomba.GlobalPosition = _jugador.GlobalPosition;

		_espera = SegundosEntreBombas;
		GetViewport().SetInputAsHandled();
	}
}
