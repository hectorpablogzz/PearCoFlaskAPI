# auth.py (CORRECTED - Returns Dictionary)

from supabase import Client
import traceback

def login_user(supabase: Client, login_data: dict):
    """
    Verifica credenciales. Espera {'email': ..., 'password': ...}.
    Devuelve tupla: (python_dict, status_code) <--- CHANGE HERE
    """
    required_swift_fields = ["idusuario", "nombre", "apellido", "correo", "idparcela"] # No idtipousuario

    try:
        email = login_data.get('email')
        password = login_data.get('password')

        if not email or not password:
            # Return dict, not jsonify
            return {"success": False, "message": "Correo y contraseña son requeridos"}, 400

        email = email.strip().lower()
        print(f"Buscando usuario con correo: {email}")
        response = supabase.table("usuarios").select("*").eq("correo", email).limit(1).execute()

        if hasattr(response, 'error') and response.error:
             print(f"Error Supabase al buscar usuario: {response.error}")
             # Return dict
             return {"success": False, "message": f"Error al buscar usuario: {response.error.message}"}, 500
        if not response.data:
            print(f"Usuario no encontrado: {email}")
             # Return dict
            return {"success": False, "message": "Correo o contraseña incorrectos"}, 401

        user = response.data[0]
        password_from_db = user.get("contrasena")

        if password_from_db is None:
             print(f"Error: No se encontró 'contrasena' para {email}")
             # Return dict
             return {"success": False, "message": "Error interno (configuración)"}, 500

        if password_from_db == password:
            user.pop("contrasena", None)
            final_user_data = {}
            missing_fields = []
            type_errors = []

            for field in required_swift_fields:
                if field not in user:
                    missing_fields.append(field); continue
                value = user[field]
                if value is None:
                     missing_fields.append(f"{field} (es nulo)"); continue

                if field in ["idusuario", "idparcela"]:
                    try: final_user_data[field] = str(value)
                    except Exception as e: type_errors.append(f"'{field}' -> String: {e}")
                else: # nombre, apellido, correo
                    try: final_user_data[field] = str(value)
                    except Exception as e: type_errors.append(f"'{field}' -> String: {e}")

            if missing_fields or type_errors:
                 error_msg = f"Error datos {email}. "
                 if missing_fields: error_msg += f"Faltan/Nulos: {', '.join(missing_fields)}. "
                 if type_errors: error_msg += f"Tipos: {', '.join(type_errors)}."
                 print(error_msg)
                 # Return dict
                 return {"success": False, "message": "Error interno procesando datos."}, 500

            print(f"Login exitoso para: {final_user_data.get('nombre')}")
            # Return dict
            return {
                "success": True,
                "message": "Inicio de sesión exitoso",
                "data": final_user_data
            }, 200
        else:
            print(f"Contraseña incorrecta para: {email}")
             # Return dict
            return {"success": False, "message": "Correo o contraseña incorrectos"}, 401

    except Exception as e:
        print(f"🚨 Error inesperado en login_user: {str(e)}")
        print(traceback.format_exc())
         # Return dict
        return {"success": False, "message": "Error interno del servidor."}, 500