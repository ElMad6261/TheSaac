using Godot;

/// <summary>
/// Va en Isaac (scenes/player/jugador.tscn → Interactor). Cada fotograma busca, entre los nodos del grupo
/// "interactuables", el más cercano que esté dentro de su zona y tenga algo que hacer (IInteractable).
/// - Si hay uno, muestra el aviso "E · Abrir" (el texto lo da el objeto) en la parte de abajo de la pantalla.
/// - Al presionar E (acción "interact"), lo usa.
/// Así la puerta y la antorcha no leen el teclado: solo dicen qué texto mostrar y qué hacer.
/// </summary>
public partial class Interactor : Node
{
	private Node3D _jugador;
	private Control _aviso;        // el recuadro del aviso (Aviso/Recuadro)
	private Label _textoAviso;     // su texto (Aviso/Recuadro/Texto)
	private IInteractable _actual; // lo que se usaría si Isaac presiona E ahora

	public override void _Ready()
	{
		_jugador = GetParent<Node3D>();
		_aviso = GetNode<Control>("Aviso/Recuadro");
		_textoAviso = GetNode<Label>("Aviso/Recuadro/Texto");
		_aviso.Visible = false;
	}

	public override void _Process(double delta)
	{
		_actual = null;
		string texto = null;
		float masCerca = float.PositiveInfinity;

		foreach (Node nodo in GetTree().GetNodesInGroup("interactuables"))
		{
			if (nodo is not IInteractable objeto)
			{
				continue;
			}

			float distancia = objeto.DistanciaAlJugador(_jugador);
			if (distancia > objeto.DistanciaInteraccion || distancia >= masCerca)
			{
				continue;
			}

			string accion = objeto.TextoAccion(_jugador);
			if (string.IsNullOrEmpty(accion))
			{
				continue;
			}

			_actual = objeto;
			texto = accion;
			masCerca = distancia;
		}

		_aviso.Visible = _actual != null;
		if (_actual != null)
		{
			_textoAviso.Text = "E · " + texto;
		}
	}

	public override void _UnhandledInput(InputEvent evento)
	{
		if (_actual == null || !evento.IsActionPressed("interact") || evento.IsEcho())
		{
			return;
		}

		_actual.Interact(_jugador);
		GetViewport().SetInputAsHandled();
	}
}
