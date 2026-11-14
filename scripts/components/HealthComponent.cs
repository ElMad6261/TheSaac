using Godot;

/// <summary>
/// Vida de quien lo lleve como hijo (hoy Isaac; después los enemigos). Pieza genérica: no sabe de quién es.
/// - La vida se cuenta en MEDIOS corazones, como en Isaac: 6 = tres corazones.
/// - QuitarVida(cantidad) baja la vida, avisa con las señales y deja al dueño invulnerable un momento
///   (SegundosInvulnerable), para que un mismo golpe no pegue varias veces.
/// - Se mete al grupo "con_vida": así una explosión encuentra a todos los que puede lastimar sin conocerlos.
///
/// Uso: agregar un Node hijo con este script (en jugador.tscn se llama "Vida"). El "cuerpo" es su padre.
/// </summary>
public partial class HealthComponent : Node
{
	/// <summary>Vida al empezar, en medios corazones (6 = tres corazones).</summary>
	[Export] public int VidaMaxima { get; set; } = 6;

	/// <summary>Segundos sin recibir daño después de un golpe. 0 = sin invulnerabilidad.</summary>
	[Export] public float SegundosInvulnerable { get; set; } = 1.0f;

	/// <summary>La vida cambió (por daño o por curación).</summary>
	[Signal] public delegate void VidaCambioEventHandler(int vida, int vidaMaxima);

	/// <summary>Recibió un golpe que sí le quitó vida.</summary>
	[Signal] public delegate void HeridoEventHandler(int cantidad);

	/// <summary>La vida llegó a cero.</summary>
	[Signal] public delegate void MurioEventHandler();

	/// <summary>Vida actual, en medios corazones.</summary>
	public int Vida { get; private set; }

	/// <summary>true mientras dura la invulnerabilidad de después de un golpe.</summary>
	public bool Invulnerable => _invulnerable > 0;

	private double _invulnerable;   // segundos de invulnerabilidad que quedan

	/// <summary>Devuelve el HealthComponent que lleva un nodo como hijo directo, o null si no tiene vida.
	/// Lo usa quien hace daño al tocar (por ejemplo los pinchos), que solo conoce el cuerpo que entró.</summary>
	public static HealthComponent De(Node cuerpo)
	{
		foreach (Node hijo in cuerpo.GetChildren())
		{
			if (hijo is HealthComponent vida)
			{
				return vida;
			}
		}
		return null;
	}

	public override void _Ready()
	{
		Vida = VidaMaxima;
		AddToGroup("con_vida");
	}

	public override void _Process(double delta)
	{
		if (_invulnerable > 0)
		{
			_invulnerable -= delta;
		}
	}

	/// <summary>Quita vida (en medios corazones). Devuelve false si no hizo nada: ya estaba muerto o es invulnerable.</summary>
	public bool QuitarVida(int cantidad)
	{
		if (cantidad <= 0 || Vida <= 0 || Invulnerable)
		{
			return false;
		}

		Vida = Mathf.Max(Vida - cantidad, 0);
		_invulnerable = SegundosInvulnerable;
		EmitSignal(SignalName.VidaCambio, Vida, VidaMaxima);
		EmitSignal(SignalName.Herido, cantidad);
		if (Vida == 0)
		{
			EmitSignal(SignalName.Murio);
		}
		return true;
	}

	/// <summary>Devuelve vida (en medios corazones), sin pasar de la máxima.</summary>
	public void Curar(int cantidad)
	{
		if (cantidad <= 0 || Vida <= 0)
		{
			return;
		}

		Vida = Mathf.Min(Vida + cantidad, VidaMaxima);
		EmitSignal(SignalName.VidaCambio, Vida, VidaMaxima);
	}
}
