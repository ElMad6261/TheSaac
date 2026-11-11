/// <summary>
/// Algo que otro objeto puede encender o apagar a distancia: una placa de presión enciende una antorcha,
/// y más adelante un interruptor podría desbloquear una puerta.
/// Quien activa (por ejemplo PressurePlate) guarda las rutas de sus objetivos y les llama Activar.
/// </summary>
public interface IActivable
{
	/// <summary>true = encender / activar; false = apagar / desactivar.</summary>
	void Activar(bool activo);
}
