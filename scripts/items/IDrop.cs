/// <summary>
/// Un recogible que puede aparecer como premio cuando se despeja una sala (hoy la bomba; después llaves,
/// monedas o corazones). Room.cs lo crea y le llama CaerDesdeArriba: en vez de aparecer de golpe en el piso,
/// cae desde arriba una sola vez y se queda quieto.
/// </summary>
public interface IDrop
{
	/// <summary>Hace que el recogible caiga desde arriba hasta su sitio. Se llama después de agregarlo a la sala.</summary>
	void CaerDesdeArriba();
}
