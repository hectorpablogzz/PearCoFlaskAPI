from supabase import Client

def login_user(supabase: Client, login_data: dict):
    """
    Verifica las credenciales de un usuario contra la base de datos.
    Espera un dict con 'email' y 'password'.
    """
    try:
        email = login_data.get('email')
        password = login_data.get('password')

        if not email or not password:
            return {"success": False, "message": "Correo y contraseña son requeridos"}, 400

        # 1. Buscar al usuario por su correo
        # Asumimos que la tabla se llama 'usuarios' según tu AuthViewModel
        response = supabase.table("usuarios").select("*").eq("correo", email.lower()).execute()

        if not response.data:
            # 2. Usuario no encontrado
            return {"success": False, "message": "Correo o contraseña incorrectos"}, 401
        
        # 3. Usuario encontrado, verificar contraseña
        user = response.data[0]
        
        # --- ¡¡¡ADVERTENCIA DE SEGURIDAD MUY IMPORTANTE!!! ---
        # Estás comparando contraseñas en TEXTO PLANO. 
        # NUNCA hagas esto en una aplicación real.
        # Tu base de datos debería guardar un "hash" de la contraseña (usando bcrypt).
        # Por ahora, para que funcione con tu base de datos actual:
        
        if user['contraseña'] == password:
            # 4. Contraseña correcta
            
            # No envíes la contraseña de vuelta al cliente
            user.pop('contraseña', None) 
            
            # Enviamos 'data' para que coincida con el AuthViewModel
            return {"success": True, "message": "Inicio de sesión exitoso", "data": user}, 200
        else:
            # 5. Contraseña incorrecta
            return {"success": False, "message": "Correo o contraseña incorrectos"}, 401

    except Exception as e:
        return {"success": False, "message": f"Error del servidor: {str(e)}"}, 500