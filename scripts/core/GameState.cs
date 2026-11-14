using Godot;

/// <summary>
/// Estado de la partida que debe sobrevivir al cambio de escena: en qué piso va Isaac y con qué semilla se armó.
/// Es un autoload: Godot lo crea al arrancar (Project Settings → Globals → Autoload → GameState).
///
/// Para qué sirve la semilla guardada aquí: si el nivel se recarga (por ejemplo, al reintentar), FloorLoader
/// vuelve a armar el mismo piso. Para una partida nueva se llama NewRun() y el siguiente piso sale distinto.
/// Más adelante aquí van las estadísticas del jugador, para que pasen de Basement 1 a Basement 2.
/// </summary>
public partial class GameState : Node
{
	/// <summary>La única instancia, para usarla desde cualquier script: GameState.Instance.</summary>
	public static GameState Instance { get; private set; }

	/// <summary>Piso en el que está Isaac (data/floors/basement_1.tres, basement_2.tres...). Null si todavía no empieza ninguno.</summary>
	public FloorConfig CurrentFloor { get; private set; }

	/// <summary>Semilla con la que se armó el piso actual. 0 = todavía no hay (el próximo piso se arma al azar).</summary>
	public int Seed { get; private set; }

	/// <summary>Bombas con las que Isaac empieza cada partida.</summary>
	public const int BombasIniciales = 1;

	/// <summary>Tope de bombas que puede cargar (el contador del HUD tiene dos cifras).</summary>
	public const int BombasMaximas = 99;

	/// <summary>Bombas que lleva Isaac. Se guardan aquí para que pasen de un piso al siguiente.</summary>
	public int Bombas { get; private set; } = BombasIniciales;

	public override void _EnterTree()
	{
		Instance = this;
	}

	/// <summary>Lo llama FloorLoader al armar un piso: guarda cuál es y con qué semilla.</summary>
	public void StartFloor(FloorConfig floor, int seed)
	{
		CurrentFloor = floor;
		Seed = seed;
	}

	/// <summary>Empieza una partida nueva: olvida el piso y la semilla, así el próximo mapa sale distinto.</summary>
	public void NewRun()
	{
		CurrentFloor = null;
		Seed = 0;
		ReiniciarBombas();
	}

	/// <summary>Suma bombas (al recoger una del piso) y avisa con GameEvents.BombsChanged.</summary>
	public void AgregarBombas(int cantidad)
	{
		PonerBombas(Bombas + cantidad);
	}

	/// <summary>Gasta una bomba. Devuelve false, sin gastar nada, si Isaac no tiene ninguna.</summary>
	public bool GastarBomba()
	{
		if (Bombas <= 0)
		{
			return false;
		}

		PonerBombas(Bombas - 1);
		return true;
	}

	/// <summary>Vuelve a las bombas del inicio (partida nueva, o reintento después de morir).</summary>
	public void ReiniciarBombas()
	{
		PonerBombas(BombasIniciales);
	}

	// Único lugar donde cambia el número: así la señal sale siempre que cambia.
	private void PonerBombas(int cantidad)
	{
		Bombas = Mathf.Clamp(cantidad, 0, BombasMaximas);
		GameEvents.Instance?.EmitSignal(GameEvents.SignalName.BombsChanged, Bombas);
	}
}
