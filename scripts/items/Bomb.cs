using Godot;

/// <summary>
/// Bomba encendida: la que Isaac deja en el piso con E. Va en la raíz de scenes/items/bomba.tscn.
/// - Al aparecer hace un pequeño "pop" y enciende la chispa de la mecha.
/// - Mientras corre la mecha (SegundosMecha) late y parpadea en rojo, cada vez más rápido.
/// - Al terminar crea la explosión (EscenaExplosion → Explosion.cs) en su lugar y se borra.
///   Todo lo que hace la explosión (romper rocas, quitar vida, mancha) está en Explosion.cs, no aquí.
///
/// La bomba no tiene colisión: Isaac puede pasar por encima para alejarse.
/// Escena: Bomba (este script) → Giro (inclina el modelo hacia la cámara) → Modelo (assets/blend/bomba.blend).
/// </summary>
public partial class Bomb : Node3D
{
	/// <summary>Segundos desde que se coloca hasta que explota.</summary>
	[Export] public float SegundosMecha { get; set; } = 1.5f;

	/// <summary>Escena de la explosión (scenes/items/explosion.tscn).</summary>
	[Export] public PackedScene EscenaExplosion { get; set; }

	private const float LatidosAlEmpezar = 2.0f;   // latidos por segundo recién colocada
	private const float LatidosAlFinal = 9.0f;     // latidos por segundo justo antes de explotar
	private const float TamanoLatido = 0.14f;      // cuánto crece en cada latido (0.14 = 14 %)

	private Node3D _giro;                 // lo que late (el modelo ya inclinado)
	private StandardMaterial3D _rojo;     // capa roja encima del modelo: su transparencia hace el parpadeo
	private double _tiempo;               // segundos desde que se colocó
	private float _fase;                  // avance del latido, en vueltas (1 vuelta = un latido)
	private bool _exploto;

	public override void _Ready()
	{
		_giro = GetNode<Node3D>("Giro");

		// Capa roja: un material que se dibuja encima del modelo (MaterialOverlay). Arranca invisible.
		_rojo = new StandardMaterial3D
		{
			ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded,
			Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
			AlbedoColor = new Color(1.0f, 0.2f, 0.1f, 0.0f),
		};
		GetNode<MeshInstance3D>("Giro/Modelo/Bomba").MaterialOverlay = _rojo;

		// Pop al aparecer: crece desde chica y se pasa un poco, como el globo del aviso.
		Scale = Vector3.One * 0.4f;
		CreateTween().TweenProperty(this, "scale", Vector3.One, 0.18f)
			.SetTrans(Tween.TransitionType.Back).SetEase(Tween.EaseType.Out);
	}

	public override void _Process(double delta)
	{
		if (_exploto)
		{
			return;
		}

		_tiempo += delta;
		float avance = Mathf.Clamp((float)_tiempo / SegundosMecha, 0, 1);   // 0 = recién puesta, 1 = explota

		// El latido se acelera con la mecha. Seno de 0 a 1: 0 = tamaño normal, 1 = hinchada y roja.
		_fase += Mathf.Lerp(LatidosAlEmpezar, LatidosAlFinal, avance) * (float)delta;
		float latido = 0.5f - 0.5f * Mathf.Cos(_fase * Mathf.Tau);
		_giro.Scale = Vector3.One * (1.0f + TamanoLatido * latido);
		_rojo.AlbedoColor = new Color(1.0f, 0.2f, 0.1f, 0.55f * latido * avance);

		if (_tiempo >= SegundosMecha)
		{
			Explotar();
		}
	}

	private void Explotar()
	{
		_exploto = true;

		if (EscenaExplosion != null)
		{
			// La explosión queda como hermana de la bomba (en la sala o el nivel), en el mismo punto.
			Explosion explosion = EscenaExplosion.Instantiate<Explosion>();
			GetParent().AddChild(explosion);
			explosion.GlobalPosition = GlobalPosition;
			explosion.Detonar();
		}

		QueueFree();
	}
}
