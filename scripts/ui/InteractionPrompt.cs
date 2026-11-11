using Godot;

/// <summary>
/// Globo pixelado "E ABRIR" que aparece encima del objeto que Isaac puede usar.
/// Va en la raíz de scenes/ui/aviso_interaccion.tscn (un CanvasLayer); lo maneja el Interactor de Isaac
/// con Mostrar(texto, punto) y Ocultar().
///
/// Cómo se dibuja:
/// - Todo el arte (assets/ui/, lo genera tools/godot/generar_ui_pixel.py) se escala por un entero (Escala)
///   con filtro Nearest, para que cada píxel del arte sea un cuadro nítido.
/// - "Globo" es un Control cuyo origen es la punta de la colita: cada fotograma se pone en el punto de la
///   pantalla donde cae PuntoAviso del objeto (Camera3D.UnprojectPosition), así sigue al objeto y a la cámara.
/// Animación, a pasos como en los juegos de 8 bits:
/// - Al aparecer o al cambiar de texto, hace "pop" (crece de golpe con un pequeño rebote).
/// - Flota: sube y baja 1 píxel cada SegundosSalto.
/// - La tecla E se hunde un instante cada SegundosTecla.
/// </summary>
public partial class InteractionPrompt : CanvasLayer
{
	/// <summary>Cuántos píxeles de pantalla mide cada píxel del arte (resolución base 1152 x 648).</summary>
	[Export] public int Escala { get; set; } = 3;

	/// <summary>Cada cuánto el globo sube o baja 1 píxel.</summary>
	[Export] public float SegundosSalto { get; set; } = 0.35f;

	/// <summary>Cada cuánto se presiona la tecla E (queda hundida 0.15 s).</summary>
	[Export] public float SegundosTecla { get; set; } = 0.6f;

	[Export] public Texture2D TeclaNormal { get; set; }
	[Export] public Texture2D TeclaPulsada { get; set; }

	private const float TeclaHundidaSegundos = 0.15f;
	private const float MargenPantalla = 4f;   // píxeles de pantalla que el globo deja libres en los bordes

	private Control _globo;     // origen = punta de la colita
	private Control _caja;      // el recuadro con la tecla y el texto
	private TextureRect _cola;
	private TextureRect _tecla;
	private Label _texto;

	private bool _mostrando;
	private string _textoActual;
	private Vector3 _punto;
	private double _reloj;
	private Tween _pop;

	public override void _Ready()
	{
		_globo = GetNode<Control>("Globo");
		_caja = GetNode<Control>("Globo/Caja");
		_cola = GetNode<TextureRect>("Globo/Cola");
		_tecla = GetNode<TextureRect>("Globo/Caja/Fila/Tecla");
		_texto = GetNode<Label>("Globo/Caja/Fila/Texto");
		_globo.Visible = false;
	}

	/// <summary>Muestra el globo apuntando a puntoMundo. Se puede llamar cada fotograma.</summary>
	public void Mostrar(string texto, Vector3 puntoMundo)
	{
		_punto = puntoMundo;
		texto = texto.ToUpperInvariant();   // la fuente pixelada solo tiene mayúsculas
		if (!_mostrando || texto != _textoActual)
		{
			_textoActual = texto;
			_texto.Text = texto;
			_reloj = 0;
			HacerPop();
		}
		_mostrando = true;
	}

	public void Ocultar()
	{
		_mostrando = false;
		_textoActual = null;
		_globo.Visible = false;
	}

	public override void _Process(double delta)
	{
		if (!_mostrando)
		{
			return;
		}

		Camera3D camara = GetViewport().GetCamera3D();
		if (camara == null || camara.IsPositionBehind(_punto))
		{
			_globo.Visible = false;
			return;
		}
		_globo.Visible = true;
		_reloj += delta;

		// Flotar y presionar la tecla, a pasos (sin suavizado, como sprites de 8 bits).
		int salto = (int)(_reloj / SegundosSalto) % 2 == 0 ? 0 : -1;
		bool pulsada = _reloj % SegundosTecla < TeclaHundidaSegundos;
		_tecla.Texture = pulsada ? TeclaPulsada : TeclaNormal;

		// Todo en píxeles del arte (el Globo ya está escalado): la colita abajo al centro, la caja encima.
		// La primera fila de la colita se monta sobre la línea de abajo de la caja y la "abre".
		Vector2 tamCaja = _caja.GetCombinedMinimumSize();
		Vector2 tamCola = _cola.GetCombinedMinimumSize();
		_caja.Size = tamCaja;
		_cola.Position = new Vector2(-Mathf.Floor(tamCola.X / 2f), -tamCola.Y + salto);
		_caja.Position = new Vector2(-Mathf.Floor(tamCaja.X / 2f), -tamCola.Y - tamCaja.Y + 1 + salto);

		_globo.Position = DentroDePantalla(camara.UnprojectPosition(_punto), tamCaja, tamCola).Round();
	}

	/// <summary>Corre el globo lo justo para que la caja no se salga de la pantalla (por ejemplo, una puerta
	/// pegada al borde de arriba). La colita sigue apuntando al objeto mientras se pueda.</summary>
	private Vector2 DentroDePantalla(Vector2 punta, Vector2 tamCaja, Vector2 tamCola)
	{
		Vector2 pantalla = _globo.GetViewportRect().Size;
		float medioAncho = Mathf.Floor(tamCaja.X / 2f) * Escala;
		float alto = (tamCaja.Y + tamCola.Y) * Escala;
		punta.X = Mathf.Clamp(punta.X, medioAncho + MargenPantalla, pantalla.X - medioAncho - MargenPantalla);
		punta.Y = Mathf.Clamp(punta.Y, alto + MargenPantalla, pantalla.Y - MargenPantalla);
		return punta;
	}

	/// <summary>Aparece de golpe: crece desde chico, se pasa un poco y vuelve a su tamaño.</summary>
	private void HacerPop()
	{
		_pop?.Kill();
		_globo.Scale = Vector2.One * Escala * 0.4f;
		_pop = CreateTween();
		_pop.TweenProperty(_globo, "scale", Vector2.One * Escala, 0.18f)
			.SetTrans(Tween.TransitionType.Back).SetEase(Tween.EaseType.Out);
	}
}
