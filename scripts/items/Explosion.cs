using Godot;

/// <summary>
/// Explosión de una bomba. Va en la raíz de scenes/items/explosion.tscn. Quien la crea (Bomb.cs) la agrega
/// a la escena, la pone en su sitio y llama a Detonar(). Entonces, una sola vez:
/// 1. Rompe lo "explotable" que esté dentro de Radio (grupo "explotables", interfaz IExplotable: las rocas).
/// 2. Quita vida a todo lo que tenga HealthComponent dentro de Radio (grupo "con_vida": Isaac, y después enemigos).
/// 3. Deja una mancha de quemadura en el piso (EscenaMancha).
/// 4. Muestra el destello, el fuego y el humo, y se borra sola.
///
/// Las distancias se miden en el piso (sin contar la altura), igual que en la interacción.
/// </summary>
public partial class Explosion : Node3D
{
	/// <summary>Radio de la explosión en metros, medido en el piso desde su centro.</summary>
	[Export] public float Radio { get; set; } = 1.7f;

	/// <summary>Vida que quita, en medios corazones (2 = un corazón entero, como la bomba de Isaac).</summary>
	[Export] public int VidaQueQuita { get; set; } = 2;

	/// <summary>Escena de la mancha que queda en el piso (scenes/items/mancha_explosion.tscn). Vacía = sin mancha.</summary>
	[Export] public PackedScene EscenaMancha { get; set; }

	private const float SegundosDestello = 0.12f;   // lo que tarda la bola de fuego en crecer
	private const float SegundosApagado = 0.25f;    // lo que tarda en desvanecerse
	private const float SegundosDeVida = 1.4f;      // después de esto el nodo se borra (el humo ya terminó)

	public void Detonar()
	{
		RomperExplotables();
		QuitarVidaCercana();
		DejarMancha();
		MostrarEfecto();
	}

	private void RomperExplotables()
	{
		foreach (Node nodo in GetTree().GetNodesInGroup("explotables"))
		{
			if (nodo is IExplotable explotable && nodo is Node3D objeto && EnRadio(objeto.GlobalPosition))
			{
				explotable.RecibirExplosion(GlobalPosition);
			}
		}
	}

	private void QuitarVidaCercana()
	{
		foreach (Node nodo in GetTree().GetNodesInGroup("con_vida"))
		{
			// El HealthComponent es hijo de su dueño: la posición que cuenta es la del padre (el cuerpo).
			if (nodo is HealthComponent vida && vida.GetParent() is Node3D cuerpo && EnRadio(cuerpo.GlobalPosition))
			{
				vida.QuitarVida(VidaQueQuita);
			}
		}
	}

	/// <summary>true si el punto está dentro del radio, midiendo en el piso (X y Z).</summary>
	private bool EnRadio(Vector3 punto)
	{
		Vector3 diferencia = punto - GlobalPosition;
		diferencia.Y = 0;
		return diferencia.Length() <= Radio;
	}

	private void DejarMancha()
	{
		if (EscenaMancha == null)
		{
			return;
		}

		// La mancha es hermana de la explosión (queda en la sala cuando la explosión se borra).
		Node3D mancha = EscenaMancha.Instantiate<Node3D>();
		GetParent().AddChild(mancha);
		// Un poco arriba del piso para que no parpadee contra él; la altura al azar evita que dos manchas
		// encimadas parpadeen entre sí. Gira en pasos de 90° para que cada una se vea distinta sin torcer los píxeles.
		mancha.GlobalPosition = GlobalPosition + Vector3.Up * (0.015f + GD.Randf() * 0.01f);
		mancha.RotationDegrees = new Vector3(0, 90 * GD.RandRange(0, 3), 0);
	}

	private void MostrarEfecto()
	{
		MeshInstance3D destello = GetNode<MeshInstance3D>("Destello");
		OmniLight3D luz = GetNode<OmniLight3D>("Luz");
		GetNode<CpuParticles3D>("Fuego").Emitting = true;
		GetNode<CpuParticles3D>("Humo").Emitting = true;

		// Bola de fuego: crece de golpe hasta el radio (la esfera mide 1 m de diámetro) y se desvanece.
		destello.Scale = Vector3.One * 0.3f;
		Tween tween = CreateTween();
		tween.TweenProperty(destello, "scale", Vector3.One * Radio * 2, SegundosDestello)
			.SetTrans(Tween.TransitionType.Quad).SetEase(Tween.EaseType.Out);
		tween.TweenProperty(destello, "transparency", 1.0f, SegundosApagado);
		tween.Parallel().TweenProperty(luz, "light_energy", 0.0f, SegundosApagado);
		tween.TweenCallback(Callable.From(destello.Hide));
		tween.TweenInterval(SegundosDeVida - SegundosDestello - SegundosApagado);
		tween.TweenCallback(Callable.From(QueueFree));
	}
}
