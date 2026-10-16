using System;
using System.Collections.Generic;
using Godot;

/// <summary>
/// Datos de un piso (Basement 1, Basement 2...). Se guarda como .tres en data/floors/ y lo lee FloorGenerator.
/// </summary>
[GlobalClass]
public partial class FloorConfig : Resource
{
	/// <summary>Nombre del piso, solo para mostrarlo.</summary>
	[Export] public string FloorName { get; set; } = "Basement 1";

	/// <summary>Cuántas salas tiene el piso (contando inicio, tesoro y jefe).</summary>
	[Export(PropertyHint.Range, "3,20,1")] public int RoomCount { get; set; } = 7;

	/// <summary>Tamaño de la cuadrícula donde crece el mapa, en celdas (columnas, filas). La sala inicial va al centro.</summary>
	[Export] public Vector2I GridSize { get; set; } = new Vector2I(9, 8);

	/// <summary>Probabilidad de que se abra una sala vecina cuando el generador lo intenta (0.5 = una tirada al 50 %).</summary>
	[Export(PropertyHint.Range, "0.1,1,0.05")] public float SpawnChance { get; set; } = 0.5f;

	/// <summary>Separación entre salas en el nivel, en metros (X, Z). Es la regla del proyecto: 12 m en X y 8 m en Z.</summary>
	[Export] public Vector2 CellSize { get; set; } = new Vector2(12, 8);

	/// <summary>Salas que puede usar este piso (varias normales, una de inicio, una de tesoro, una de jefe...).</summary>
	[Export] public Godot.Collections.Array<RoomData> Rooms { get; set; } = new Godot.Collections.Array<RoomData>();

	/// <summary>Elige al azar una sala del tipo pedido. Devuelve null si el piso no tiene ninguna de ese tipo.</summary>
	public RoomData PickRoom(RoomType type, Random rng)
	{
		List<RoomData> options = new List<RoomData>();
		foreach (RoomData room in Rooms)
		{
			if (room != null && room.Type == type)
			{
				options.Add(room);
			}
		}

		return options.Count == 0 ? null : options[rng.Next(options.Count)];
	}
}
