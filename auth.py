# auth.py (Versión Corregida y Robusta - SIN idtipousuario)

from supabase import Client
import traceback # Para logs más detallados

def login_user(supabase: Client, login_data: dict):
    """
    Verifica credenciales. Espera {'email': ..., 'password': ...}.
    Devuelve tupla: (response_dict, status_code)
    """
    # Lista de campos que Swift necesita OBLIGATORIAMENTE (SIN idtipousuario)
    required_swift_fields = ["idusuario", "nombre", "apellido", "correo", "idparcela"]

    try:
        email = login_data.get('email')
        password = login_data.get('password')

        if not email or not password:
            return {"success": False, "message": "Correo y contraseña son requeridos"}, 400

        email = email.strip().lower() # Limpia email

        print(f"Buscando usuario con correo: {email}")
        # Asegúrate que la tabla es 'usuarios' y la columna 'correo'
        # Selecciona todas las columnas '*'
        response = supabase.table("usuarios").select("*").eq("correo", email).limit(1).execute()

        # Verifica errores de Supabase
        if hasattr(response, 'error') and response.error:
             print(f"Error Supabase al buscar usuario: {response.error}")
             return {"success": False, "message": f"Error al buscar usuario: {response.error.message}"}, 500

        if not response.data:
            print(f"Usuario no encontrado: {email}")
            return {"success": False, "message": "Correo o contraseña incorrectos"}, 401

        user = response.data[0]
        password_from_db = user.get("contrasena") # Usa .get() por seguridad

        if password_from_db is None:
             print(f"Error: No se encontró la columna 'contrasena' para el usuario {email}")
             return {"success": False, "message": "Error interno del servidor (configuración)"}, 500

        # --- COMPARACIÓN DE CONTRASEÑA (Texto plano - INSEGURO) ---
        if password_from_db == password:
            user.pop("contrasena", None) # Quita la contraseña

            # --- VERIFICACIÓN Y FORMATEO DE DATOS PARA SWIFT ---
            final_user_data = {}
            missing_fields = []
            type_errors = []

            # Itera sobre los campos que Swift necesita
            for field in required_swift_fields:
                if field not in user:
                    missing_fields.append(field)
                    continue

                value = user[field]

                # Maneja NULLs para campos NO opcionales en Swift
                if value is None:
                     print(f"Error: Campo requerido '{field}' es NULL en la DB para usuario {email}")
                     missing_fields.append(f"{field} (es nulo)")
                     continue

                # ----- Conversión/Validación de Tipos -----
                # Convierte UUIDs a String
                if field in ["idusuario", "idparcela"]:
                    try:
                        final_user_data[field] = str(value) # Asegura que sea string
                    except Exception as e:
                        type_errors.append(f"Error convirtiendo '{field}' a String: {e}")
                # Otros campos (nombre, apellido, correo): asegura que sean string
                else:
                    try:
                        final_user_data[field] = str(value)
                    except Exception as e:
                        type_errors.append(f"Error convirtiendo '{field}' a String: {e}")

            # ----- Reportar Errores de Validación -----
            if missing_fields or type_errors:
                 error_msg = f"Error: Datos inconsistentes del usuario {email}. "
                 if missing_fields: error_msg += f"Faltan/Nulos: {', '.join(missing_fields)}. "
                 if type_errors: error_msg += f"Errores de tipo: {', '.join(type_errors)}."
                 print(error_msg)
                 return {"success": False, "message": "Error interno al procesar datos del usuario."}, 500

            # --- ÉXITO ---
            print(f"Login exitoso para: {final_user_data.get('nombre')}")
            return {
                "success": True,
                "message": "Inicio de sesión exitoso",
                "data": final_user_data
            }, 200
        else:
            # Contraseña incorrecta
            print(f"Contraseña incorrecta para: {email}")
            return {"success": False, "message": "Correo o contraseña incorrectos"}, 401

    # Captura cualquier otro error inesperado
    except Exception as e:
        print(f"🚨 Error inesperado en login_user: {str(e)}")
        print(traceback.format_exc())
        return {"success": False, "message": "Error interno del servidor durante el login."}, 500