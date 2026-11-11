using Godot;

/// <summary>
/// Va en Isaac (scenes/player/jugador.tscn → Interactor). Cada fotograma busca, entre los nodos del grupo
/// "interactuables", el más cercano que esté dentro de su zona y tenga algo que hacer (IInteractable).
/// - Si hay uno, muestra el globo "E ABRIR" (el texto lo da el objeto) encima del objeto, en su PuntoAviso.
///   El globo es el hijo "Aviso" (scenes/ui/aviso_interaccion.tscn, script InteractionPrompt).
/// - Al presionar E (acción "interact"), lo usa.
/// Así la puerta y la antorcha no leen el teclado: solo dicen qué texto mostrar y qué hacer.
/// </summary>
public partial class Interactor : Node
{
	private Node3D _jugador;
	private InteractionPrompt _aviso;
	private IInteractable _actual; // lo que se usaría si Isaac presiona E ahora

	public override void _Ready()
	{
		_jugador = GetParent<Node3D>();
		_aviso = GetNode<InteractionPrompt>("Aviso");
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

		if (_actual != null)
		{
			_aviso.Mostrar(texto, _actual.PuntoAviso);
		}
		else
		{
			_aviso.Ocultar();
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
