using Godot;

/// <summary>
/// Antorcha que se enciende y se apaga. Sirve para la de muro (antorcha_interactiva.tscn) y la de pie
/// (antorcha_pie.tscn); solo cambia RutaLlama.
/// - Es un IInteractable: si UsableConE está activo, el Interactor de Isaac muestra "E · Encender" o
///   "E · Apagar" cuando está cerca y, al presionar E, llama a Interact.
/// - Es un IActivable: una placa de presión (u otro objeto) la enciende o apaga con Activar.
///
/// Usa sus nodos "Luz" (OmniLight3D) y la malla de la llama (RutaLlama, viene del .blend).
/// Al encender, la llama aparece y la luz sube de 0 a su brillo en EncendidoSegundos; al apagar, al revés.
/// </summary>
public partial class TorchInteraction : Node3D, IInteractable, IActivable
{
	/// <summary>Si arranca encendida.</summary>
	[Export] public bool Encendida { get; set; }

	/// <summary>Si Isaac la puede encender y apagar con E. Si no, solo la controla otro objeto (Activar).</summary>
	[Export] public bool UsableConE { get; set; } = true;

	/// <summary>Distancia máxima (m, en el piso) entre Isaac y la antorcha para usarla.</summary>
	[Export] public float DistanciaInteraccion { get; set; } = 1.5f;

	/// <summary>Segundos que tarda la luz en subir o bajar.</summary>
	[Export] public float EncendidoSegundos { get; set; } = 0.3f;

	/// <summary>Ruta a la malla de la llama dentro del modelo importado.</summary>
	[Export] public NodePath RutaLlama { get; set; } = "Modelo/Antorcha/Antorcha_Llama";

	[Signal] public delegate void CambioEstadoEventHandler(bool encendida);

	private OmniLight3D _luz;
	private Node3D _llama;
	private float _brilloEncendida;  // el light_energy que trae la escena
	private Tween _tween;

	public override void _Ready()
	{
		_luz = GetNode<OmniLight3D>("Luz");
		_llama = GetNode<Node3D>(RutaLlama);
		_brilloEncendida = _luz.LightEnergy;

		// Estado inicial, sin animación.
		_llama.Visible = Encendida;
		_luz.LightEnergy = Encendida ? _brilloEncendida : 0f;
		_luz.Visible = Encendida;

		AddToGroup("interactuables");
	}

	public float DistanciaAlJugador(Node3D jugador)
	{
		Vector3 delta = jugador.GlobalPosition - GlobalPosition;
		delta.Y = 0f;
		return delta.Length();
	}

	public string TextoAccion(Node3D jugador)
	{
		if (!UsableConE)
		{
			return null;
		}
		return Encendida ? "Apagar" : "Encender";
	}

	/// <summary>E: cambia de encendida a apagada o al revés.</summary>
	public void Interact(Node3D jugador)
	{
		CambiarEstado(!Encendida);
	}

	/// <summary>La llama otro objeto (por ejemplo, una placa de presión).</summary>
	public void Activar(bool activo)
	{
		if (activo != Encendida)
		{
			CambiarEstado(activo);
		}
	}

	private void CambiarEstado(bool encender)
	{
		Encendida = encender;

		// Si cambia a medio fundido, se corta el anterior y se sigue desde el brillo actual.
		_tween?.Kill();
		_tween = CreateTween();

		if (Encendida)
		{
			_llama.Visible = true;
			_luz.Visible = true;
			_tween.TweenProperty(_luz, "light_energy", _brilloEncendida, EncendidoSegundos);
		}
		else
		{
			_llama.Visible = false;
			_tween.TweenProperty(_luz, "light_energy", 0f, EncendidoSegundos);
			// Apagada del todo, la luz se esconde para que no cueste nada al render.
			_tween.TweenCallback(Callable.From(() => _luz.Visible = false));
		}

		EmitSignal(SignalName.CambioEstado, Encendida);
	}
}
