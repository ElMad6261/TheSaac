using Godot;

/// <summary>
/// HUD de Isaac: los corazones y el contador de bombas, arriba a la izquierda.
/// Va en la raíz de scenes/ui/hud.tscn (un CanvasLayer), que está dentro de jugador.tscn.
/// - Corazones: lee la vida del nodo "Vida" de Isaac (HealthComponent) y escucha su señal VidaCambio.
///   Cada corazón son dos medios: lleno, medio o vacío.
/// - Bombas: lee GameState.Bombas y escucha GameEvents.BombsChanged.
/// El arte (assets/ui/, de tools/godot/generar_arte_bomba.py) se escala por un entero con filtro Nearest,
/// igual que el globo del aviso de interacción.
/// </summary>
public partial class Hud : CanvasLayer
{
	[Export] public Texture2D CorazonLleno { get; set; }
	[Export] public Texture2D CorazonMedio { get; set; }
	[Export] public Texture2D CorazonVacio { get; set; }

	private HBoxContainer _corazones;
	private Label _bombas;

	public override void _Ready()
	{
		_corazones = GetNode<HBoxContainer>("Raiz/Columna/Corazones");
		_bombas = GetNode<Label>("Raiz/Columna/Bombas/Texto");

		HealthComponent vida = GetParent().GetNodeOrNull<HealthComponent>("Vida");
		if (vida != null)
		{
			vida.VidaCambio += MostrarVida;
			// La vida se fija en el _Ready de HealthComponent, que puede correr después de este: se lee un fotograma más tarde.
			Callable.From(() => MostrarVida(vida.Vida, vida.VidaMaxima)).CallDeferred();
		}

		GameEvents.Instance.BombsChanged += MostrarBombas;
		MostrarBombas(GameState.Instance.Bombas);
	}

	public override void _ExitTree()
	{
		// GameEvents vive toda la partida y este HUD no: al salir (por ejemplo, al recargar el nivel) hay que soltarse.
		// (Al cerrar el juego GameEvents puede haberse borrado antes: por eso se comprueba.)
		if (IsInstanceValid(GameEvents.Instance))
		{
			GameEvents.Instance.BombsChanged -= MostrarBombas;
		}
	}

	/// <summary>Dibuja un corazón por cada dos medios de vida máxima: lleno, medio o vacío según la vida actual.</summary>
	private void MostrarVida(int vida, int vidaMaxima)
	{
		foreach (Node viejo in _corazones.GetChildren())
		{
			viejo.QueueFree();
		}

		for (int medios = 0; medios < vidaMaxima; medios += 2)
		{
			int quedan = vida - medios;   // medios corazones que le tocan a este corazón
			_corazones.AddChild(new TextureRect
			{
				Texture = quedan >= 2 ? CorazonLleno : (quedan == 1 ? CorazonMedio : CorazonVacio),
				MouseFilter = Control.MouseFilterEnum.Ignore,
			});
		}
	}

	private void MostrarBombas(int bombas)
	{
		_bombas.Text = bombas.ToString("00");   // siempre dos cifras: 01, 02... como en Isaac
	}
}
