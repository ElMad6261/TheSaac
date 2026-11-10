using Godot;
using System;

/// <summary>
/// Lógica de la puerta: abre o cierra la hoja sobre su bisagra, usando las animaciones que ya trae la escena
/// (Abrir, Cerrar, Bloqueada y, en la del tesoro, Desbloquear).
///
/// Es un IInteractable: no lee el teclado. El Interactor de Isaac la elige cuando está cerca, muestra
/// "E · Abrir" o "E · Cerrar" (TextoAccion) y, al presionar E, llama a Interact.
///
/// Va en la raíz de puerta.tscn, puerta_jefe.tscn y puerta_tesoro.tscn. Necesita sus hijos directos
/// "AnimationPlayer" y "Hoja" (la hoja tiene el origen en la bisagra y mide 1.2 m).
/// </summary>
public partial class DoorInteraction : Node3D, IInteractable
{
	/// <summary>Distancia horizontal máxima (m) entre Isaac y el centro del vano para que E funcione.
	/// Desde la sala de la puerta basta con acercarse a la pared; desde la sala vecina hay que meterse en su vano.</summary>
	[Export] public float DistanciaInteraccion { get; set; } = 1.6f;

	/// <summary>Radio de Isaac (cápsula de 0.35 m) más un poco de holgura. Se suma al largo de la hoja
	/// para saber si al cerrar lo golpearía.</summary>
	[Export] public float MargenBarrido { get; set; } = 0.4f;

	/// <summary>Sala con enemigos: E reproduce "Bloqueada" en vez de abrir. La sala lo pone en false al despejarse.</summary>
	[Export] public bool Bloqueada { get; set; }

	/// <summary>Puerta del tesoro: la primera vez necesita llave (ver IntentarGastarLlave).</summary>
	[Export] public bool RequiereLlave { get; set; }

	/// <summary>Lo conecta quien maneje las llaves (más adelante, GameState): devuelve true si Isaac tenía
	/// una llave y la gastó. Mientras nadie lo conecte, la puerta del tesoro se queda bloqueada.</summary>
	public Func<bool> IntentarGastarLlave { get; set; }

	[Signal] public delegate void PuertaAbiertaEventHandler();
	[Signal] public delegate void PuertaCerradaEventHandler();

	/// <summary>True cuando la hoja terminó de abrir; vuelve a false cuando termina de cerrar.</summary>
	public bool Abierta { get; private set; }

	// La hoja mide 1.2 m y su origen es la bisagra. Cerrada, su centro está a la mitad: 0.6 m en X.
	private const float AnchoHoja = 1.2f;
	private static readonly Vector3 CentroHojaLocal = new Vector3(AnchoHoja / 2f, 0f, 0f);

	private AnimationPlayer _anim;
	private Node3D _hoja;
	private bool _llaveUsada;

	public override void _Ready()
	{
		_anim = GetNode<AnimationPlayer>("AnimationPlayer");
		_hoja = GetNode<Node3D>("Hoja");
		_anim.AnimationFinished += OnAnimacionTerminada;
		AddToGroup("interactuables");
	}

	/// <summary>Qué dice el aviso. Null (sin aviso) mientras la hoja se mueve, o si está abierta
	/// e Isaac está donde la hoja lo golpearía al cerrar.</summary>
	public string TextoAccion(Node3D jugador)
	{
		if (_anim.IsPlaying())
		{
			return null;
		}

		if (Abierta)
		{
			return JugadorEnBarridoDeLaHoja(jugador) ? null : "Cerrar";
		}

		// Bloqueada o sin llave también dice "Abrir": al intentarlo, la hoja tiembla (animación Bloqueada).
		return "Abrir";
	}

	/// <summary>Lo llama el Interactor de Isaac al presionar E.</summary>
	public void Interact(Node3D jugador)
	{
		// Mientras una animación corre, E no hace nada (no se corta a medias).
		if (_anim.IsPlaying())
		{
			return;
		}

		if (Abierta)
		{
			if (!JugadorEnBarridoDeLaHoja(jugador))
			{
				Cerrar();
			}
			return;
		}

		if (Bloqueada)
		{
			_anim.Play("Bloqueada");
			return;
		}

		if (RequiereLlave && !_llaveUsada)
		{
			bool gastoLlave = IntentarGastarLlave != null && IntentarGastarLlave();
			if (gastoLlave)
			{
				_llaveUsada = true;
				_anim.Play("Desbloquear"); // ya incluye la apertura
			}
			else
			{
				_anim.Play("Bloqueada");
			}
			return;
		}

		Abrir();
	}

	/// <summary>Abre la puerta. También lo puede llamar la sala (por ejemplo, al despejarse).</summary>
	public void Abrir()
	{
		if (!Abierta && !_anim.IsPlaying())
		{
			_anim.Play("Abrir");
		}
	}

	/// <summary>Cierra la puerta (no revisa dónde está Isaac: eso lo hace Interactuar).</summary>
	public void Cerrar()
	{
		if (Abierta && !_anim.IsPlaying())
		{
			_anim.Play("Cerrar");
		}
	}

	private void OnAnimacionTerminada(StringName nombre)
	{
		string animacion = nombre;
		if (animacion == "Abrir" || animacion == "Desbloquear")
		{
			Abierta = true;
			EmitSignal(SignalName.PuertaAbierta);
		}
		else if (animacion == "Cerrar")
		{
			Abierta = false;
			EmitSignal(SignalName.PuertaCerrada);
		}
	}

	/// <summary>Distancia en el piso (sin contar la altura) entre Isaac y el centro del vano.</summary>
	public float DistanciaAlJugador(Node3D jugador)
	{
		Vector3 centro = ToGlobal(_hoja.Position + CentroHojaLocal);
		Vector3 delta = jugador.GlobalPosition - centro;
		delta.Y = 0f;
		return delta.Length();
	}

	/// <summary>True si al cerrar la hoja golpearía a Isaac. La hoja abierta apunta hacia -Z (local de la puerta)
	/// y al cerrar barre un cuarto de círculo de 1.2 m alrededor de la bisagra, de ese lado.
	/// Isaac estorba si está de ese lado (o parado en el vano) y a menos de 1.2 m + su radio de la bisagra.</summary>
	private bool JugadorEnBarridoDeLaHoja(Node3D jugador)
	{
		Vector3 desdeBisagra = ToLocal(jugador.GlobalPosition) - _hoja.Position;
		desdeBisagra.Y = 0f;
		bool delLadoDelGiro = desdeBisagra.Z < MargenBarrido;
		bool alAlcanceDeLaHoja = desdeBisagra.Length() < AnchoHoja + MargenBarrido;
		return delLadoDelGiro && alAlcanceDeLaHoja;
	}
}
