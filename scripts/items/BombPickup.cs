using Godot;

/// <summary>
/// Bomba recogible: el ítem que está en el piso y que Isaac agarra al tocarlo. No usa la E.
/// Va en la raíz de scenes/items/bomba_recogible.tscn, que es un Area3D en la capa 7 (Recogibles)
/// que solo mira la capa 2 (Jugador).
/// - Está quieta en el piso, sin animación de reposo: se reconoce por su forma y su contorno.
/// - Al tocarla, suma Cantidad a las bombas de GameState (el HUD se entera por GameEvents.BombsChanged)
///   y desaparece con un pequeño salto.
/// - Si es el premio de una sala despejada (IDrop), Room.cs le llama CaerDesdeArriba: cae una vez desde
///   arriba, rebota y se queda quieta. Mientras cae no se puede agarrar.
/// Usa el mismo modelo que la bomba encendida, más chico (escala de "Giro") y con la llama oculta.
/// </summary>
public partial class BombPickup : Area3D, IDrop
{
	/// <summary>Cuántas bombas da.</summary>
	[Export] public int Cantidad { get; set; } = 1;

	private const float AlturaCaida = 5.0f;     // desde qué altura cae cuando es un premio (m)
	private const float SegundosCaida = 0.8f;   // lo que tarda en caer y dejar de rebotar

	private Node3D _giro;       // el modelo ya inclinado hacia la cámara
	private bool _cayendo;      // true mientras cae: todavía no se puede agarrar
	private bool _recogida;

	public override void _Ready()
	{
		_giro = GetNode<Node3D>("Giro");
		GetNode<Node3D>("Giro/Modelo/Bomba/Bomba_Chispa").Visible = false;   // apagada: sin llama
		BodyEntered += OnBodyEntered;
	}

	/// <summary>Caída del premio: solo baja el modelo ("Giro"); la zona que detecta a Isaac ya está en el piso.</summary>
	public void CaerDesdeArriba()
	{
		_cayendo = true;
		float alturaEnPiso = _giro.Position.Y;
		_giro.Position += Vector3.Up * AlturaCaida;

		// La curva "Bounce" baja y rebota dos o tres veces al llegar, cada vez menos.
		Tween tween = CreateTween();
		tween.TweenProperty(_giro, "position:y", alturaEnPiso, SegundosCaida)
			.SetTrans(Tween.TransitionType.Bounce).SetEase(Tween.EaseType.Out);
		tween.TweenCallback(Callable.From(TerminarCaida));
	}

	private void TerminarCaida()
	{
		_cayendo = false;

		// Si Isaac estaba parado justo donde cayó, la agarra ahora (BodyEntered ya había pasado).
		foreach (Node3D cuerpo in GetOverlappingBodies())
		{
			OnBodyEntered(cuerpo);
		}
	}

	private void OnBodyEntered(Node3D cuerpo)
	{
		if (_recogida || _cayendo || !cuerpo.IsInGroup("jugador"))
		{
			return;
		}
		_recogida = true;

		GameState.Instance.AgregarBombas(Cantidad);

		// Salta, se encoge y se borra.
		Tween tween = CreateTween();
		tween.TweenProperty(_giro, "position:y", _giro.Position.Y + 0.5f, 0.15f)
			.SetTrans(Tween.TransitionType.Quad).SetEase(Tween.EaseType.Out);
		tween.Parallel().TweenProperty(_giro, "scale", _giro.Scale * 0.2f, 0.15f);
		tween.TweenCallback(Callable.From(QueueFree));
	}
}
