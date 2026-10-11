using Godot;

/// <summary>
/// Señales globales del juego. Es un autoload: Godot lo crea al arrancar
/// (Project Settings → Globals → Autoload → GameEvents).
/// Un sistema emite una señal y otros la escuchan sin conocerse entre sí. Ejemplo: la sala avisa que
/// Isaac entró y la cámara se mueve a ella, sin que la sala sepa que existe una cámara.
/// Las demás señales del plan (RoomCleared, PlayerDamaged, ItemPicked) se agregan cuando algo las use.
/// </summary>
public partial class GameEvents : Node
{
	/// <summary>La única instancia, para usarla desde cualquier script: GameEvents.Instance.</summary>
	public static GameEvents Instance { get; private set; }

	/// <summary>El jugador entró a una sala.</summary>
	[Signal]
	public delegate void RoomEnteredEventHandler(Room room);

	public override void _EnterTree()
	{
		Instance = this;
	}
}
