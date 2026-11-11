using Godot;

/// <summary>
/// Placa de presión en el piso: se activa cuando Isaac pasa encima. No usa la E.
/// - Su hijo "Zona" (Area3D que solo mira la capa 2, Jugador) detecta a Isaac.
/// - Al pisarla, el botón se hunde, la marca roja se enciende y llama Activar(true) en cada objetivo
///   (cualquier nodo que implemente IActivable, por ejemplo una antorcha).
/// - Si SeQuedaPresionada está activo (por defecto), se queda abajo para siempre. Si no, al salir Isaac
///   el botón sube y llama Activar(false).
///
/// Va en la raíz de scenes/props/placa_presion.tscn. Los objetivos se eligen en el Inspector (Objetivos).
/// </summary>
public partial class PressurePlate : Node3D
{
	/// <summary>Nodos que se encienden al pisar la placa. Deben implementar IActivable.</summary>
	[Export] public Godot.Collections.Array<NodePath> Objetivos { get; set; } = new();

	/// <summary>true: se activa una vez y se queda abajo. false: solo mientras Isaac está encima.</summary>
	[Export] public bool SeQuedaPresionada { get; set; } = true;

	/// <summary>Cuánto se hunde el botón (m). El modelo lo deja 5 cm arriba del piso.</summary>
	[Export] public float Hundimiento { get; set; } = 0.035f;

	[Signal] public delegate void CambioEstadoEventHandler(bool presionada);

	public bool Presionada { get; private set; }

	private const float SegundosBoton = 0.08f;

	private Node3D _boton;
	private MeshInstance3D _botonMalla;
	private int _superficieMarca = -1;     // la superficie con el material M_Rojo del botón
	private StandardMaterial3D _marcaEncendida;
	private float _botonArriba;
	private int _cuerposEncima;
	private Tween _tween;

	public override void _Ready()
	{
		_botonMalla = GetNode<MeshInstance3D>("Modelo/PlacaPresion/PlacaPresion_Boton");
		_boton = _botonMalla;
		_botonArriba = _boton.Position.Y;
		PrepararMarca();

		Area3D zona = GetNode<Area3D>("Zona");
		zona.BodyEntered += OnBodyEntered;
		zona.BodyExited += OnBodyExited;
	}

	/// <summary>Busca la superficie roja del botón y arma una copia que brilla, para cuando se active.</summary>
	private void PrepararMarca()
	{
		Mesh malla = _botonMalla.Mesh;
		for (int i = 0; i < malla.GetSurfaceCount(); i++)
		{
			if (malla.SurfaceGetMaterial(i) is StandardMaterial3D mat && mat.ResourceName == "M_Rojo")
			{
				_superficieMarca = i;
				_marcaEncendida = (StandardMaterial3D)mat.Duplicate();
				_marcaEncendida.EmissionEnabled = true;
				_marcaEncendida.Emission = new Color(1f, 0.45f, 0.15f);
				_marcaEncendida.EmissionEnergyMultiplier = 2.5f;
				return;
			}
		}
	}

	private void OnBodyEntered(Node3D cuerpo)
	{
		if (!cuerpo.IsInGroup("jugador"))
		{
			return;
		}
		_cuerposEncima++;
		if (!Presionada)
		{
			CambiarEstado(true);
		}
	}

	private void OnBodyExited(Node3D cuerpo)
	{
		if (!cuerpo.IsInGroup("jugador"))
		{
			return;
		}
		_cuerposEncima = Mathf.Max(0, _cuerposEncima - 1);
		if (!SeQuedaPresionada && _cuerposEncima == 0 && Presionada)
		{
			CambiarEstado(false);
		}
	}

	private void CambiarEstado(bool presionar)
	{
		Presionada = presionar;

		// Botón: baja o sube rápido, con un rebote corto al llegar abajo.
		_tween?.Kill();
		_tween = CreateTween();
		float destino = presionar ? _botonArriba - Hundimiento : _botonArriba;
		_tween.TweenProperty(_boton, "position:y", destino, SegundosBoton)
			.SetTrans(Tween.TransitionType.Quad).SetEase(Tween.EaseType.Out);

		if (_superficieMarca >= 0)
		{
			_botonMalla.SetSurfaceOverrideMaterial(_superficieMarca, presionar ? _marcaEncendida : null);
		}

		foreach (NodePath ruta in Objetivos)
		{
			if (GetNodeOrNull(ruta) is IActivable objetivo)
			{
				objetivo.Activar(presionar);
			}
			else
			{
				GD.PushWarning($"PressurePlate: '{ruta}' no existe o no es IActivable.");
			}
		}

		EmitSignal(SignalName.CambioEstado, presionar);
	}
}
