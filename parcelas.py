from flask import jsonify
from supabase import Client

def crear_parcela(supabase: Client, data: dict):
    ubic = data.get("ubicacion") or {}
    missing_parcela = [f for f in ("nombre", "hectareas", "tipo") if f not in data]
    missing_ubic = [f for f in ("estado", "municipio", "latitud", "longitud") if f not in ubic]
    if missing_parcela or missing_ubic:
        return jsonify({
            "success": False,
            "error": "Datos incompletos",
            "missing": {"parcela": missing_parcela, "ubicacion": missing_ubic}
        }), 400

    try:
        # Insertar ubicación
        ubicacion_payload = {
            "estado": ubic.get("estado"),
            "municipio": ubic.get("municipio"),
            "latitud": ubic.get("latitud"),
            "longitud": ubic.get("longitud")
        }
        ubic_resp = supabase.table("ubicacion").insert(ubicacion_payload).execute()
        if not ubic_resp.data:
            return jsonify({"success": False, "error": "No se pudo crear la ubicación"}), 500
        
        # Accedemos a la clave 'idubicacion' (minúscula)
        ubicacion_creada = ubic_resp.data[0]
        id_ubicacion_creada = ubicacion_creada["idubicacion"]

        # Insertar parcela
        parcela_payload = {
            "nombre": data.get("nombre"),
            "hectareas": data.get("hectareas"),
            "tipo": data.get("tipo"),
            "idubicacion": id_ubicacion_creada
        }
        parcela_resp = supabase.table("parcela").insert(parcela_payload).execute()
        if not parcela_resp.data:
            # Si falla, eliminar la ubicación huérfana
            supabase.table("ubicacion").delete().eq("idubicacion", id_ubicacion_creada).execute()
            return jsonify({"success": False, "error": "No se pudo crear la parcela"}), 500

        parcela_creada = parcela_resp.data[0]
        parcela_creada["ubicacion"] = ubicacion_creada  # Adjuntamos el objeto ubicación completo

        return jsonify({"success": True, "data": parcela_creada}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def obtener_parcelas(supabase: Client):
    try:
        response = supabase.table("parcela").select("*, ubicacion(*)").execute()
        return jsonify({"success": True, "data": response.data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def obtener_parcela(supabase: Client, idParcela: str):
    try:
        # Usamos 'idparcela' (minúscula) para la consulta
        response = supabase.table("parcela").select("*, ubicacion(*)").eq("idparcela", idParcela).execute()
        if not response.data:
            return jsonify({"success": False, "error": "Parcela no encontrada"}), 404
        return jsonify({"success": True, "data": response.data[0]}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def modificar_parcela(supabase: Client, idParcela: str, data: dict):
    try:
        # Actualizar ubicación si viene
        if "ubicacion" in data:
            parcela_resp = supabase.table("parcela").select("idubicacion").eq("idparcela", idParcela).execute()
            if not parcela_resp.data:
                return jsonify({"success": False, "error": "Parcela no encontrada"}), 404
            idUbicacion = parcela_resp.data[0]["idubicacion"]
            supabase.table("ubicacion").update(data["ubicacion"]).eq("idubicacion", idUbicacion).execute()

        # Actualizar parcela
        parcela_payload = {k: data[k] for k in ("nombre", "hectareas", "tipo") if k in data}
        if parcela_payload:
            supabase.table("parcela").update(parcela_payload).eq("idparcela", idParcela).execute()

        return obtener_parcela(supabase, idParcela)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def eliminar_parcela(supabase: Client, idParcela: str):
    try:
        parcela_resp = supabase.table("parcela").select("idubicacion").eq("idparcela", idParcela).execute()
        if not parcela_resp.data:
            return jsonify({"success": False, "error": "Parcela no encontrada"}), 404

        idUbicacion = parcela_resp.data[0]["idubicacion"]
        # Eliminar en orden (primero la parcela, luego la ubicación)
        supabase.table("parcela").delete().eq("idparcela", idParcela).execute()
        supabase.table("ubicacion").delete().eq("idubicacion", idUbicacion).execute()

        return jsonify({"success": True, "data": f"Parcela con id {idParcela} eliminada correctamente"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al eliminar: {str(e)}"}), 500
