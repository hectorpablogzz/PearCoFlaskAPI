# auth.py (Versión Corregida y Robusta)

from supabase import Client
import traceback # Para logs más detallados

def login_user(supabase: Client, login_data: dict):
    """
    Verifica credenciales. Espera {'email': ..., 'password': ...}.
    Devuelve tupla: (response_dict, status_code)
    """
    # Lista de campos que tu 'struct User' en Swift necesita OBLIGATORIAMENTE
    required_swift_fields = ["idusuario", "nombre", "apellido", "correo", "idparcela", "idtipousuario"]

    try:
        # Obtiene datos del JSON enviado por Swift
        email = login_data.get('email')
        password = login_data.get('password')

        # Validación básica de entrada
        if not email or not password:
            return {"success": False, "message": "Correo y contraseña son requeridos"}, 400

        email = email.strip().lower() # Limpia y convierte a minúsculas

        print(f"Buscando usuario con correo: {email}")
        # Busca en la tabla 'usuarios' (asegúrate que el nombre sea correcto)
        # Selecciona todas las columnas '*' (verifica que incluya 'idtipousuario')
        response = supabase.table("usuarios").select("*").eq("correo", email).limit(1).execute()

        # Verifica si hubo un error directo de Supabase
        if hasattr(response, 'error') and response.error:
             print(f"Error Supabase al buscar usuario: {response.error}")
             return {"success": False, "message": f"Error al buscar usuario: {response.error.message}"}, 500

        # Verifica si se encontró el usuario
        if not response.data:
            print(f"Usuario no encontrado: {email}")
            return {"success": False, "message": "Correo o contraseña incorrectos"}, 401

        # Obtiene los datos del usuario encontrado
        user = response.data[0]
        # Obtiene la contraseña almacenada (asegúrate que la columna sea 'contrasena')
        password_from_db = user.get("contrasena")

        # Verifica si la contraseña existe en los datos
        if password_from_db is None:
             print(f"Error: No se encontró la columna 'contrasena' para el usuario {email}")
             return {"success": False, "message": "Error interno del servidor (configuración)"}, 500

        # --- COMPARACIÓN DE CONTRASEÑA (Texto plano - INSEGURO) ---
        # ¡¡¡Considera usar hashing para contraseñas en producción!!!
        if password_from_db == password:
            # Contraseña correcta, elimina la contraseña del diccionario antes de enviarlo
            user.pop("contrasena", None)

            # --- VERIFICACIÓN Y FORMATEO DE DATOS ANTES DE ENVIAR A SWIFT ---
            final_user_data = {}
            missing_fields = []
            type_errors = []

            # Itera sobre los campos que Swift necesita
            for field in required_swift_fields:
                # ¿Está el campo en los datos de Supabase?
                if field not in user:
                    missing_fields.append(field)
                    continue # Pasa al siguiente campo

                value = user[field]

                # ¿Es el valor nulo (None) cuando Swift espera un valor?
                if value is None:
                     # Si algún campo SÍ puede ser nulo en Swift, necesitas manejarlo aquí.
                     # Por ahora, asumimos que todos los 'required_swift_fields' NO pueden ser nulos.
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
                # Valida/Convierte 'idtipousuario' a Int
                elif field == "idtipousuario":
                    if not isinstance(value, int):
                         type_errors.append(f"Campo '{field}' no es Integer (es {type(value)})")
                         try:
                             final_user_data[field] = int(value) # Intenta convertir a int
                         except (ValueError, TypeError):
                             pass # Falla si no se puede convertir, se reportará en type_errors
                    else:
                         final_user_data[field] = value # Ya es int
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
                 # Devuelve error 500 porque Swift no podrá decodificar esto
                 return {"success": False, "message": "Error interno al procesar datos del usuario."}, 500

            # --- ÉXITO ---
            print(f"Login exitoso para: {final_user_data.get('nombre')}")
            # Devuelve el diccionario validado y formateado dentro de 'data'
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
        print(traceback.format_exc()) # Imprime el traceback completo en los logs del servidor
        return {"success": False, "message": "Error interno del servidor durante el login."}, 500