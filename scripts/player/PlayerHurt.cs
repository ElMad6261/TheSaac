using Godot;

/// <summary>
/// Lo que le pasa a Isaac cuando pierde vida. Va en scenes/player/jugador.tscn → Herido, junto a "Vida"
/// (HealthComponent), que es quien lleva la cuenta y la invulnerabilidad. Aquí solo va lo propio del jugador:
/// - Al recibir el golpe entra en la pose de daño (PlayerController.MostrarHerido) y se pone rojo un instante.
/// - Cuando termina la pose y mientras siga invulnerable, el modelo parpadea.
/// - Si la vida llega a cero, se reintenta el nivel: se recarga la escena y las bombas vuelven a las del inicio.
///   GameState conserva el piso y la semilla, así que sale el mismo mapa.
/// </summary>
public partial class PlayerHurt : Node
{
	/// <summary>Segundos que dura la pose de daño (y el destello rojo). Debe ser menor que la invulnerabilidad.</summary>
	[Export] public float SegundosPose { get; set; } = 0.45f;

	/// <summary>Veces por segundo que el modelo aparece y desaparece mientras Isaac es invulnerable.</summary>
	[Export] public float ParpadeosPorSegundo { get; set; } = 10.0f;

	private HealthComponent _vida;
	private PlayerController _control;
	private Node3D _modelo;
	private StandardMaterial3D _rojo;   // capa roja encima del modelo: su transparencia hace el destello
	private double _pose;               // segundos que le quedan a la pose de daño
	private double _reloj;

	public override void _Ready()
	{
		_vida = GetNode<HealthComponent>("../Vida");
		_control = GetParent<PlayerController>();
		_modelo = GetNode<Node3D>("../Modelo");
		_vida.Herido += OnHerido;
		_vida.Murio += OnMurio;

		// Capa roja: un material que se dibuja encima de cada malla de Isaac (MaterialOverlay). Arranca invisible.
		_rojo = new StandardMaterial3D
		{
			ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded,
			Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
			AlbedoColor = new Color(1.0f, 0.15f, 0.1f, 0.0f),
		};
		foreach (Node nodo in _modelo.FindChildren("*", "MeshInstance3D", true, false))
		{
			((MeshInstance3D)nodo).MaterialOverlay = _rojo;
		}
	}

	public override void _Process(double delta)
	{
		// 1) Pose de daño: visible, con el rojo apagándose.
		if (_pose > 0)
		{
			_pose -= delta;
			float resto = Mathf.Clamp((float)_pose / SegundosPose, 0, 1);   // 1 = recién golpeado, 0 = termina la pose
			_rojo.AlbedoColor = new Color(1.0f, 0.15f, 0.1f, 0.6f * resto);
			_modelo.Visible = true;
			return;
		}

		// 2) Sin invulnerabilidad: normal.
		if (!_vida.Invulnerable)
		{
			_modelo.Visible = true;
			return;
		}

		// 3) Resto de la invulnerabilidad: parpadea (visible en la primera mitad de cada parpadeo).
		_reloj += delta;
		_modelo.Visible = (_reloj * ParpadeosPorSegundo) % 1.0 < 0.5;
	}

	private void OnHerido(int cantidad)
	{
		_pose = SegundosPose;
		_reloj = 0;
		_control.MostrarHerido(SegundosPose);
	}

	private void OnMurio()
	{
		GameState.Instance.ReiniciarBombas();
		// Diferido: la escena no se puede recargar a la mitad de un fotograma (la explosión sigue corriendo).
		GetTree().CallDeferred(SceneTree.MethodName.ReloadCurrentScene);
	}
}
