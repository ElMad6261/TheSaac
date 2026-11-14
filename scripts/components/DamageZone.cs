using Godot;

/// <summary>
/// Zona que quita vida a quien esté dentro: los pinchos del piso, y después fuego o charcos.
/// Va en un Area3D que mira la capa 2 (Jugador). No tiene colisión sólida: Isaac la pisa y se lastima.
///
/// Cada fotograma de física revisa los cuerpos que tiene dentro y le pide a su HealthComponent que quite vida.
/// No hace falta contar el tiempo aquí: el HealthComponent ignora los golpes mientras su dueño es invulnerable,
/// así que quedarse parado encima quita vida una vez por cada periodo de invulnerabilidad.
/// </summary>
public partial class DamageZone : Area3D
{
	/// <summary>Vida que quita, en medios corazones (2 = un corazón entero).</summary>
	[Export] public int VidaQueQuita { get; set; } = 2;

	public override void _PhysicsProcess(double delta)
	{
		foreach (Node3D cuerpo in GetOverlappingBodies())
		{
			HealthComponent.De(cuerpo)?.QuitarVida(VidaQueQuita);
		}
	}
}
