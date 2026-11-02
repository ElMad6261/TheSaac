using Godot;

/// <summary>Tipos de sala que conoce el generador de pisos.</summary>
public enum RoomType
{
	Normal,
	Start,
	Treasure,
	Boss,
}

/// <summary>
/// Una sala disponible para un piso: de qué tipo es y de qué escena sale.
/// Agregar una sala nueva = crear un .tres de este tipo en data/rooms/ y ponerlo en la lista de un FloorConfig;
/// no hace falta tocar código.
/// </summary>
[GlobalClass]
public partial class RoomData : Resource
{
	/// <summary>Para qué sirve esta sala: el generador usa la de tipo Start una vez, la Boss una vez, etc.</summary>
	[Export] public RoomType Type { get; set; } = RoomType.Normal;

	/// <summary>Escena de la sala (raíz con Room.cs). Las puertas las pone el generador, no la escena.</summary>
	[Export] public PackedScene Scene { get; set; }
}
