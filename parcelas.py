from flask import jsonify
from supabase import Client

def crear_parcela(supabase: Client, data: dict):
    # Validación básica
    ubic = data.get("ubicacion") or {}
    missing_parcela = [f for f in ("nombre", "hectareas", "tipo") if f not in data]
    missing_ubic = [f for f in ("estado", "municipio", "latitud", "longitud") if f not in ubic]
    if missing_parcela or missing_ubic:
        return jsonify({
            "success": False,
            "error": "Datos incompletos",
            "missing": {
                "parcela": missing_parcela,
                "ubicacion": missing_ubic
            }
        }), 400

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
    ubicacion_creada = ubic_resp.data[0]

    # Insertar parcela
    parcela_payload = {
        "nombre": data.get("nombre"),
        "hectareas": data.get("hectareas"),
        "tipo": data.get("tipo"),
        "idUbicacion": ubicacion_creada["idUbicacion"]
    }
    parcela_resp = supabase.table("parcela").insert(parcela_payload).execute()
    if not parcela_resp.data:
        return jsonify({"success": False, "error": "No se pudo crear la parcela"}), 500

    parcela_creada = parcela_resp.data[0]
    parcela_creada["ubicacion"] = ubicacion_creada

    return jsonify({"success": True, "data": parcela_creada}), 201


def obtener_parcelas(supabase: Client):
    response = supabase.table("parcela").select("*, ubicacion(*)").execute()
    return jsonify({"success": True, "data": response.data}), 200


def obtener_parcela(supabase: Client, idParcela: int):
    response = supabase.table("parcela").select("*, ubicacion(*)").eq("idParcela", idParcela).execute()
    if not response.data:
        return jsonify({"success": False, "error": "Parcela no encontrada"}), 404
    return jsonify({"success": True, "data": response.data[0]}), 200


def modificar_parcela(supabase: Client, idParcela: int, data: dict):
    # Actualizar ubicación si viene
    if "ubicacion" in data:
        parcela_resp = supabase.table("parcela").select("*").eq("idParcela", idParcela).execute()
        if not parcela_resp.data:
            return jsonify({"success": False, "error": "Parcela no encontrada"}), 404
        idUbicacion = parcela_resp.data[0]["idUbicacion"]
        supabase.table("ubicacion").update(data["ubicacion"]).eq("idUbicacion", idUbicacion).execute()

    # Actualizar parcela
    parcela_payload = {k: data[k] for k in ("nombre", "hectareas", "tipo") if k in data}
    if parcela_payload:
        supabase.table("parcela").update(parcela_payload).eq("idParcela", idParcela).execute()

    return obtener_parcela(supabase, idParcela)


def eliminar_parcela(supabase: Client, idParcela: int):
    parcela_resp = supabase.table("parcela").select("*").eq("idParcela", idParcela).execute()
    if not parcela_resp.data:
        return jsonify({"success": False, "error": "Parcela no encontrada"}), 404

    idUbicacion = parcela_resp.data[0]["idUbicacion"]
    supabase.table("parcela").delete().eq("idParcela", idParcela).execute()
    supabase.table("ubicacion").delete().eq("idUbicacion", idUbicacion).execute()

    return jsonify({"success": True, "data": f"Parcela con id {idParcela} eliminada correctamente"}), 200
