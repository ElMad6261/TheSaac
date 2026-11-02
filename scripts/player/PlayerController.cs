using Godot;

/// <summary>
/// Isaac en vista 2.5D (cámara fija desde arriba, estilo The Binding of Isaac).
/// - WASD (acciones move_forward, move_back, move_left, move_right) mueve el CUERPO según la pantalla:
///   W = hacia arriba de la pantalla, S = hacia abajo, A = izquierda, D = derecha.
/// - Las FLECHAS (acciones look_forward, look_back, look_left, look_right) giran solo la CABEZA, aparte del cuerpo.
///   Sin flechas, la cabeza mira hacia donde camina el cuerpo. HeadScale ajusta su tamaño.
/// - Isaac gira suavemente hacia donde camina y reproduce "Caminar" (en movimiento) o "Quieto" (parado).
///   Las dos animaciones vienen de assets/blend/isaac.blend (se generan con tools/blender/animar_isaac.py).
/// - El ratón no se usa: la cámara es de la sala (RoomCamera), no del jugador.
///
/// Escena: scenes/player/jugador.tscn = CharacterBody3D (este script) + Colision (cápsula) + Modelo → Isaac.
/// Capas: el cuerpo está en la capa 2 (Jugador) y choca solo con la capa 1 (Mundo).
/// </summary>
public partial class PlayerController : CharacterBody3D
{
	// Valores que se ajustan desde el Inspector, sin tocar el código.

	/// <summary>Velocidad al caminar, en metros por segundo.</summary>
	[Export] public float Speed { get; set; } = 4.0f;

	/// <summary>Cuánto sube la velocidad por segundo al arrancar (m/s²). Más alto = arranca más seco.</summary>
	[Export] public float Acceleration { get; set; } = 25.0f;

	/// <summary>Cuánto baja la velocidad por segundo al soltar las teclas (m/s²). Más alto = frena más seco.</summary>
	[Export] public float Deceleration { get; set; } = 35.0f;

	/// <summary>Qué tan rápido gira Isaac hacia donde camina. Más alto = gira más rápido.</summary>
	[Export] public float TurnSpeed { get; set; } = 12.0f;

	/// <summary>Ciclos de caminata por segundo al ir a velocidad máxima (un ciclo = dos pasos).</summary>
	[Export] public float WalkAnimSpeed { get; set; } = 3.0f;

	/// <summary>Qué tan rápido gira la cabeza hacia donde apuntan las flechas. Más alto = gira más rápido.</summary>
	[Export] public float HeadTurnSpeed { get; set; } = 14.0f;

	/// <summary>
	/// Tamaño de la cabeza respecto al modelo original (1 = tamaño de Blender, sin cambios).
	/// Por debajo de ~0.85 la cara se deforma (los ojos quedan enormes para la cabeza).
	/// </summary>
	[Export(PropertyHint.Range, "0.8,1.1,0.01")] public float HeadScale { get; set; } = 0.9f;

	// Segundos que dura el fundido al cambiar entre "Quieto" y "Caminar".
	private const double AnimationBlend = 0.15;

	private Node3D _model;
	private AnimationPlayer _animation;  // reproduce "Caminar" y "Quieto" (vienen dentro del modelo de Isaac)
	private Skeleton3D _skeleton;        // esqueleto del modelo: de aquí se gira la cabeza
	private int _headBone = -1;          // índice del hueso "Head" (-1 = no se encontró)
	private Quaternion _headRest;        // rotación del hueso Head en reposo (mirando al frente)
	private float _headYaw;              // giro actual de la cabeza respecto al cuerpo, en radianes

	public override void _Ready()
	{
		_model = GetNode<Node3D>("Modelo");

		// El modelo importado de Blender trae su AnimationPlayer y su Skeleton3D. Se buscan por nombre
		// (en vez de una ruta fija) para que no se rompa si en Blender cambia la jerarquía.
		// El tercer argumento en false hace falta porque son hijos de una escena instanciada.
		_animation = _model.FindChild("AnimationPlayer", true, false) as AnimationPlayer;
		_skeleton = _model.FindChild("Skeleton3D", true, false) as Skeleton3D;

		if (_skeleton != null)
		{
			_headBone = _skeleton.FindBone("Head");
			if (_headBone >= 0)
			{
				_headRest = _skeleton.GetBoneRest(_headBone).Basis.GetRotationQuaternion();
			}
		}

		if (_animation == null || _headBone < 0)
		{
			GD.PushWarning("PlayerController: el modelo no trae AnimationPlayer o el hueso Head; sin animación o sin giro de cabeza.");
		}
	}

	public override void _PhysicsProcess(double delta)
	{
		float dt = (float)delta;
		Vector3 velocity = Velocity;

		// Gravedad: solo mientras está en el aire. GetGravity() devuelve la del proyecto
		// (o la de un Area3D que la cambie, si algún día se usa una).
		if (!IsOnFloor())
		{
			velocity += GetGravity() * dt;
		}

		// Teclas -> vector 2D: X = izquierda/derecha, Y = arriba/abajo de la pantalla.
		// GetVector ya limita el largo a 1, así que en diagonal no se camina más rápido.
		Vector2 moveInput = Input.GetVector("move_left", "move_right", "move_forward", "move_back");

		// De pantalla a mundo: con la cámara mirando al norte (lo normal), W = -Z.
		Vector3 direction = ScreenToWorld(moveInput);

		// La velocidad horizontal se acerca poco a poco a la deseada: sin tirones al arrancar ni al frenar.
		// La vertical (Y) no se toca aquí: es de la gravedad.
		Vector3 horizontal = new Vector3(velocity.X, 0, velocity.Z);
		float change = (moveInput == Vector2.Zero ? Deceleration : Acceleration) * dt;
		horizontal = horizontal.MoveToward(direction * Speed, change);
		velocity.X = horizontal.X;
		velocity.Z = horizontal.Z;

		// Isaac gira hacia donde camina. Su modelo mira hacia +Z, por eso el ángulo es Atan2(x, z).
		// 1 - e^(-k·dt) da un giro suave que se ve igual a cualquier cantidad de cuadros por segundo.
		if (direction.LengthSquared() > 0.0001f)
		{
			float targetAngle = Mathf.Atan2(direction.X, direction.Z);
			float weight = 1.0f - Mathf.Exp(-TurnSpeed * dt);
			_model.Rotation = new Vector3(0, Mathf.LerpAngle(_model.Rotation.Y, targetAngle, weight), 0);
		}

		Velocity = velocity;
		// Mueve el cuerpo y lo hace deslizar contra muros y obstáculos en vez de quedarse pegado.
		MoveAndSlide();
	}

	// La animación y la cabeza son solo visuales: van en _Process (cada cuadro dibujado), no en la física.
	public override void _Process(double delta)
	{
		UpdateAnimation();
		UpdateHead((float)delta);
	}

	// Pasa un vector de pantalla (X = derecha, Y = abajo) a una dirección del mundo.
	// "Arriba de la pantalla" depende de hacia dónde mira la cámara: se gira el vector con el giro
	// horizontal de la cámara activa.
	private Vector3 ScreenToWorld(Vector2 screen)
	{
		Camera3D camera = GetViewport().GetCamera3D();
		float cameraYaw = camera != null ? camera.GlobalRotation.Y : 0.0f;
		return new Vector3(screen.X, 0, screen.Y).Rotated(Vector3.Up, cameraYaw);
	}

	// Cuerpo: "Quieto" parado, "Caminar" en movimiento, con la cadencia atada a la velocidad real.
	private void UpdateAnimation()
	{
		if (_animation == null)
		{
			return;
		}

		// Rapidez horizontal real (sin la caída). Casi cero = parado.
		float speed = new Vector2(Velocity.X, Velocity.Z).Length();
		bool walking = speed > 0.1f;
		string wanted = walking ? "Caminar" : "Quieto";

		// Play con fundido: al cambiar de animación las poses se mezclan en vez de saltar de una a otra.
		if (_animation.CurrentAnimation != wanted)
		{
			_animation.Play(wanted, AnimationBlend);
		}

		// Al caminar, el ciclo va más rápido cuanto más rápido va Isaac (WalkAnimSpeed ciclos/s a velocidad máxima).
		_animation.SpeedScale = walking ? WalkAnimSpeed * Mathf.Clamp(speed / Speed, 0.5f, 1.5f) : 1.0f;
	}

	// Cabeza: las flechas la giran respecto al cuerpo. El hueso Head no tiene animación,
	// así que lo único que lo mueve es este código.
	private void UpdateHead(float dt)
	{
		if (_headBone < 0)
		{
			return;
		}

		// Flechas -> hacia dónde mira la cabeza. Sin flechas, el giro objetivo es 0: la cabeza sigue al cuerpo.
		Vector2 lookInput = Input.GetVector("look_left", "look_right", "look_forward", "look_back");
		float targetYaw = 0.0f;
		if (lookInput != Vector2.Zero)
		{
			Vector3 lookDirection = ScreenToWorld(lookInput);
			// Ángulo del mundo hacia donde apuntan las flechas, menos el del cuerpo = giro de la cabeza
			// respecto al cuerpo. Wrap lo deja entre -180° y 180°: la cabeza gira por el lado corto.
			targetYaw = Mathf.Wrap(Mathf.Atan2(lookDirection.X, lookDirection.Z) - _model.Rotation.Y, -Mathf.Pi, Mathf.Pi);
		}

		// Mismo giro suave que el cuerpo, pero con su propia velocidad.
		float weight = 1.0f - Mathf.Exp(-HeadTurnSpeed * dt);
		_headYaw = Mathf.LerpAngle(_headYaw, targetYaw, weight);

		// El giro es alrededor del eje vertical del hueso (su eje Y local), partiendo de la pose de reposo.
		_skeleton.SetBonePoseRotation(_headBone, _headRest * new Quaternion(Vector3.Up, _headYaw));

		// Tamaño de la cabeza: escalar el hueso Head encoge la cabeza (y la cara, que va pegada a él)
		// desde la base del cuello, sin tocar el modelo de Blender.
		_skeleton.SetBonePoseScale(_headBone, Vector3.One * HeadScale);
	}
}
