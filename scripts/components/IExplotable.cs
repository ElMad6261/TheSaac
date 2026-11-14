using Godot;

/// <summary>
/// Algo que reacciona a una explosión sin tener vida: una roca que se rompe, y más adelante una puerta
/// secreta o un cofre de piedra.
///
/// Quien lo implemente debe ser un Node3D y meterse en el grupo "explotables" (en _Ready): así lo encuentra
/// Explosion.cs. Lo que tiene vida (Isaac, enemigos) no usa esta interfaz: lleva un HealthComponent.
/// </summary>
public interface IExplotable
{
	/// <summary>Lo llama la explosión cuando el objeto queda dentro de su radio. origen = centro de la explosión.</summary>
	void RecibirExplosion(Vector3 origen);
}
