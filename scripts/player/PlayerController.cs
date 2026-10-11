using Godot;

/// <summary>
/// Isaac en vista 2.5D (cámara fija desde arriba, estilo The Binding of Isaac).
/// - WASD (acciones move_forward, move_back, move_left, move_right) mueve según la pantalla:
///   W = hacia arriba de la pantalla, S = hacia abajo, A = izquierda, D = derecha.
/// - Isaac gira suavemente hacia donde camina.
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

	private Node3D _model;

	public override void _Ready()
	{
		_model = GetNode<Node3D>("Modelo");
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

		// "Arriba de la pantalla" depende de hacia dónde mira la cámara: se gira la entrada con el giro
		// horizontal de la cámara activa. Con la cámara mirando al norte (lo normal), W = -Z.
		Camera3D camera = GetViewport().GetCamera3D();
		float cameraYaw = camera != null ? camera.GlobalRotation.Y : 0.0f;
		Vector3 direction = new Vector3(moveInput.X, 0, moveInput.Y).Rotated(Vector3.Up, cameraYaw);

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
}
