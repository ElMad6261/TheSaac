using Godot;

/// <summary>
/// Algo que Isaac puede usar con E: puerta, antorcha, y más adelante interruptor, pedestal o cofre.
///
/// Quien lo implemente debe ser un Node3D y meterse en el grupo "interactuables" (en _Ready), porque así
/// lo encuentra el Interactor de Isaac. El Interactor elige el más cercano que esté en zona, muestra el globo
/// "E " + TextoAccion encima de PuntoAviso y, al presionar E, llama a Interact.
/// </summary>
public interface IInteractable
{
	/// <summary>Distancia máxima (m, medida en el piso) a la que Isaac puede usarlo.</summary>
	float DistanciaInteraccion { get; }

	/// <summary>Distancia en el piso (sin contar la altura) entre Isaac y el punto donde se usa.</summary>
	float DistanciaAlJugador(Node3D jugador);

	/// <summary>Texto del aviso, por ejemplo "Abrir". Null si ahora mismo no se puede usar
	/// (por ejemplo, mientras una animación corre): entonces no se muestra aviso.</summary>
	string TextoAccion(Node3D jugador);

	/// <summary>Punto del mundo (global) al que apunta la colita del globo del aviso: encima del objeto.</summary>
	Vector3 PuntoAviso { get; }

	/// <summary>Lo que pasa al presionar E.</summary>
	void Interact(Node3D jugador);
}
