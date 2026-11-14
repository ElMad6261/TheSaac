using Godot;

/// <summary>
/// Roca que se rompe con una bomba (las lágrimas no la rompen: por eso no lleva HealthComponent).
/// Va en la raíz de scenes/props/roca.tscn y de la roca graybox.
///
/// Al recibir una explosión desaparece con su colisión. Si tiene un hijo "Escombros" (CPUParticles3D de
/// un solo disparo), lo deja en la sala soltando pedazos y ese nodo se borra solo al terminar.
/// </summary>
public partial class Rock : Node3D, IExplotable
{
	private bool _rota;

	public override void _Ready()
	{
		AddToGroup("explotables");
	}

	public void RecibirExplosion(Vector3 origen)
	{
		if (_rota)
		{
			return;
		}
		_rota = true;

		// Los escombros se pasan al padre (la sala) antes de borrar la roca; si no, se borrarían con ella.
		CpuParticles3D escombros = GetNodeOrNull<CpuParticles3D>("Escombros");
		if (escombros != null)
		{
			escombros.Reparent(GetParent());
			escombros.Emitting = true;
			escombros.Finished += escombros.QueueFree;
		}

		QueueFree();
	}
}
