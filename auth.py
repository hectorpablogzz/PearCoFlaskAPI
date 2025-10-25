from flask import Flask, jsonify, request
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

        # Buscar al usuario por su correo (campo 'correo' en tu tabla)
        response = supabase.table("usuarios").select("*").eq("correo", email.lower()).execute()

        if not response.data:
            return {"success": False, "message": "Correo o contraseña incorrectos"}, 401
        
        user = response.data[0]

        # Comparar con el campo correcto 'contrasena'
        if user["contrasena"] == password:
            user.pop("contrasena", None)  # No enviamos la contraseña de vuelta
            return {
                "success": True,
                "message": "Inicio de sesión exitoso",
                "data": user
            }, 200
        else:
            return {"success": False, "message": "Correo o contraseña incorrectos"}, 401

    except Exception as e:
        return {"success": False, "message": f"Error del servidor: {str(e)}"}, 500
