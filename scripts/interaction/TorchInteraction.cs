using Godot;

/// <summary>
/// Antorcha que Isaac enciende y apaga con E. Es un IInteractable: el Interactor de Isaac muestra
/// "E · Encender" o "E · Apagar" cuando está cerca y, al presionar E, llama a Interact.
///
/// Va en la raíz de scenes/props/antorcha_interactiva.tscn (que hereda de antorcha.tscn). Usa sus nodos
/// "Luz" (OmniLight3D) y "Modelo/Antorcha/Antorcha_Llama" (la malla de la llama, que viene del .blend).
/// Al encender, la llama aparece y la luz sube de 0 a su brillo en EncendidoSegundos; al apagar, al revés.
/// </summary>
public partial class TorchInteraction : Node3D, IInteractable
{
	/// <summary>Si arranca encendida.</summary>
	[Export] public bool Encendida { get; set; }

	/// <summary>Distancia máxima (m, en el piso) entre Isaac y la antorcha para usarla.</summary>
	[Export] public float DistanciaInteraccion { get; set; } = 1.5f;

	/// <summary>Segundos que tarda la luz en subir o bajar.</summary>
	[Export] public float EncendidoSegundos { get; set; } = 0.3f;

	[Signal] public delegate void CambioEstadoEventHandler(bool encendida);

	private OmniLight3D _luz;
	private Node3D _llama;
	private float _brilloEncendida;  // el light_energy que trae la escena (1.8)
	private Tween _tween;

	public override void _Ready()
	{
		_luz = GetNode<OmniLight3D>("Luz");
		_llama = GetNode<Node3D>("Modelo/Antorcha/Antorcha_Llama");
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
		return Encendida ? "Apagar" : "Encender";
	}

	public void Interact(Node3D jugador)
	{
		Encendida = !Encendida;

		// Si se presiona E a medio fundido, se corta el anterior y se sigue desde el brillo actual.
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
