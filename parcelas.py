# parcelas.py (CORRECTED - Returns Dictionary)

from flask import jsonify # Keep jsonify import here, might be needed if you add other non-route functions later
from supabase import Client
import traceback

# --- Crear Parcela ---
def crear_parcela(supabase: Client, data: dict):
    ubic = data.get("ubicacion") or {}
    missing_parcela = [f for f in ("nombre", "hectareas", "tipo") if f not in data]
    missing_ubic = [f for f in ("estado", "municipio", "latitud", "longitud") if f not in ubic]
    if missing_parcela or missing_ubic:
        print(f"Validation failed - Missing fields: Parcela={missing_parcela}, Ubicacion={missing_ubic}")
        # Return dict, not jsonify
        return ({
            "success": False, "error": "Datos incompletos",
            "missing": {"parcela": missing_parcela, "ubicacion": missing_ubic}
        }, 400)

    id_ubicacion_creada = None
    try:
        ubicacion_payload = {
            "estado": ubic.get("estado"), "municipio": ubic.get("municipio"),
            "latitud": ubic.get("latitud"), "longitud": ubic.get("longitud")
        }
        print(f"Inserting ubicacion: {ubicacion_payload}")
        ubic_resp = supabase.table("ubicacion").insert(ubicacion_payload).execute()

        if hasattr(ubic_resp, 'error') and ubic_resp.error:
             print(f"Error Supabase inserting ubicacion: {ubic_resp.error}")
             # Return dict
             return ({"success": False, "error": f"No se pudo crear ubicación: {ubic_resp.error.message}"}, 500)
        if not ubic_resp.data:
             print(f"Error inserting ubicacion: No data. Resp: {ubic_resp}")
             # Return dict
             return ({"success": False, "error": "No se pudo crear ubicación (inesperado)"}, 500)

        ubicacion_creada = ubic_resp.data[0]
        id_ubicacion_creada = ubicacion_creada.get("idubicacion")
        if not id_ubicacion_creada:
             print("Error: 'idubicacion' key missing.")
             # Return dict
             return ({"success": False, "error": "Error interno ID ubicación"}, 500)
        print(f"Ubicacion created: {id_ubicacion_creada}")

        parcela_payload = {
            "nombre": data.get("nombre"), "hectareas": data.get("hectareas"),
            "tipo": data.get("tipo"), "idubicacion": id_ubicacion_creada
        }
        print(f"Inserting parcela: {parcela_payload}")
        parcela_resp = supabase.table("parcela").insert(parcela_payload).execute()

        if hasattr(parcela_resp, 'error') and parcela_resp.error:
            print(f"Error Supabase inserting parcela: {parcela_resp.error}. Rolling back.")
            try: supabase.table("ubicacion").delete().eq("idubicacion", id_ubicacion_creada).execute()
            except Exception as rb_e: print(f"Rollback error: {rb_e}")
            # Return dict
            return ({"success": False, "error": f"No se pudo crear parcela: {parcela_resp.error.message}"}, 500)
        if not parcela_resp.data:
             print(f"Error inserting parcela: No data. Rolling back. Resp: {parcela_resp}")
             try: supabase.table("ubicacion").delete().eq("idubicacion", id_ubicacion_creada).execute()
             except Exception as rb_e: print(f"Rollback error: {rb_e}")
             # Return dict
             return ({"success": False, "error": "No se pudo crear parcela (inesperado)"}, 500)

        parcela_creada = parcela_resp.data[0]
        parcela_creada["ubicacion"] = ubicacion_creada
        print(f"Parcela created: {parcela_creada.get('idparcela')}")
        # Return dict
        return ({"success": True, "data": parcela_creada}, 201)

    except Exception as e:
        print(f"🚨 Unexpected error in crear_parcela: {str(e)}")
        print(traceback.format_exc())
        if id_ubicacion_creada:
             try:
                 print(f"Attempting rollback for ubicacion {id_ubicacion_creada}")
                 supabase.table("ubicacion").delete().eq("idubicacion", id_ubicacion_creada).execute()
             except Exception as rb_e: print(f"Rollback error: {rb_e}")
        # Return dict
        return ({"success": False, "error": "Error interno servidor."}, 500)

# --- Obtener Todas las Parcelas ---
def obtener_parcelas(supabase: Client):
    try:
        print("Fetching all parcelas with ubicacion...")
        response = supabase.table("parcela").select("*, ubicacion(*)").execute()

        if hasattr(response, 'error') and response.error:
             print(f"Error Supabase fetching parcelas: {response.error}")
             # Return dict
             return ({"success": False, "error": f"Error al obtener: {response.error.message}"}, 500)

        data = response.data or []
        print(f"Fetched {len(data)} parcelas.")
        # Return dict
        return ({"success": True, "data": data}, 200)

    except Exception as e:
        print(f"🚨 Unexpected error in obtener_parcelas: {str(e)}")
        print(traceback.format_exc())
        # Return dict
        return ({"success": False, "error": "Error interno servidor."}, 500)

# --- Obtener Una Parcela por ID ---
def obtener_parcela(supabase: Client, idParcela: str):
    try:
        print(f"Fetching parcela id: {idParcela}")
        response = supabase.table("parcela").select("*, ubicacion(*)").eq("idparcela", idParcela).limit(1).execute()

        if hasattr(response, 'error') and response.error:
             print(f"Error Supabase fetching parcela {idParcela}: {response.error}")
             # Return dict
             return ({"success": False, "error": f"Error al obtener: {response.error.message}"}, 500)
        if not response.data:
            print(f"Parcela not found: {idParcela}")
            # Return dict
            return ({"success": False, "error": "Parcela no encontrada"}, 404)

        print(f"Parcela {idParcela} found.")
        # Return dict
        return ({"success": True, "data": response.data[0]}, 200)

    except Exception as e:
        print(f"🚨 Unexpected error in obtener_parcela ID {idParcela}: {str(e)}")
        print(traceback.format_exc())
        # Return dict
        return ({"success": False, "error": "Error interno servidor."}, 500)

# --- Modificar Parcela ---
def modificar_parcela(supabase: Client, idParcela: str, data: dict):
    try:
        print(f"Modifying parcela: {idParcela} with data: {data}")
        if "ubicacion" in data and isinstance(data["ubicacion"], dict):
            parcela_resp = supabase.table("parcela").select("idubicacion").eq("idparcela", idParcela).limit(1).execute()

            if hasattr(parcela_resp, 'error') and parcela_resp.error:
                 print(f"Error finding idubicacion for {idParcela}: {parcela_resp.error}")
                 return ({"success": False, "error": f"Error buscar parcela: {parcela_resp.error.message}"}, 500)
            if not parcela_resp.data:
                print(f"Parcela {idParcela} not found for ubicacion update.")
                return ({"success": False, "error": "Parcela no encontrada"}, 404)

            current_idUbicacion = parcela_resp.data[0].get("idubicacion")
            if not current_idUbicacion:
                 print(f"Error: Parcela {idParcela} has no idubicacion.")
                 return ({"success": False, "error": "Parcela sin ubicación asociada"}, 500)

            ubicacion_payload = {k: data["ubicacion"][k] for k in ("estado", "municipio", "latitud", "longitud") if k in data["ubicacion"]}
            if ubicacion_payload:
                print(f"Updating ubicacion {current_idUbicacion}: {ubicacion_payload}")
                upd_ubic_resp = supabase.table("ubicacion").update(ubicacion_payload).eq("idubicacion", current_idUbicacion).execute()
                if hasattr(upd_ubic_resp, 'error') and upd_ubic_resp.error:
                     print(f"Error updating ubicacion {current_idUbicacion}: {upd_ubic_resp.error}")
                     return ({"success": False, "error": f"Error actualizar ubicación: {upd_ubic_resp.error.message}"}, 500)
            else: print("No fields to update for ubicacion.")

        parcela_payload = {k: data[k] for k in ("nombre", "hectareas", "tipo") if k in data}
        if parcela_payload:
            print(f"Updating parcela {idParcela}: {parcela_payload}")
            upd_parc_resp = supabase.table("parcela").update(parcela_payload).eq("idparcela", idParcela).execute()
            if hasattr(upd_parc_resp, 'error') and upd_parc_resp.error:
                 print(f"Error updating parcela {idParcela}: {upd_parc_resp.error}")
                 return ({"success": False, "error": f"Error actualizar parcela: {upd_parc_resp.error.message}"}, 500)
        else: print("No fields to update for parcela.")

        print(f"Modification complete for {idParcela}. Fetching...")
        # Return tuple from obtener_parcela
        return obtener_parcela(supabase, idParcela)

    except Exception as e:
        print(f"🚨 Unexpected error in modificar_parcela ID {idParcela}: {str(e)}")
        print(traceback.format_exc())
        # Return dict
        return ({"success": False, "error": "Error interno servidor."}, 500)

# --- Eliminar Parcela ---
def eliminar_parcela(supabase: Client, idParcela: str):
    idUbicacion = None
    try:
        print(f"Deleting parcela: {idParcela}")
        parcela_resp = supabase.table("parcela").select("idubicacion").eq("idparcela", idParcela).limit(1).execute()

        if hasattr(parcela_resp, 'error') and parcela_resp.error:
            print(f"Error finding {idParcela} for deletion: {parcela_resp.error}")
            return ({"success": False, "error": f"Error buscar parcela: {parcela_resp.error.message}"}, 500)
        if not parcela_resp.data:
            print(f"Parcela {idParcela} not found for deletion.")
            return ({"success": False, "error": "Parcela no encontrada"}, 404)

        idUbicacion = parcela_resp.data[0].get("idubicacion")

        print(f"Deleting parcela record {idParcela}...")
        del_parc_resp = supabase.table("parcela").delete().eq("idparcela", idParcela).execute()

        if hasattr(del_parc_resp, 'error') and del_parc_resp.error:
             error_msg = del_parc_resp.error.message
             if "violates foreign key constraint" in error_msg.lower():
                 print(f"FK violation deleting {idParcela}.")
                 return ({"success": False, "error": "Parcela asignada a un usuario."}, 409)
             else:
                 print(f"Error deleting parcela {idParcela}: {del_parc_resp.error}")
                 return ({"success": False, "error": f"Error eliminar parcela: {error_msg}"}, 500)
        if not del_parc_resp.data: print(f"Warning: No data returned deleting parcela {idParcela}.")

        if idUbicacion:
            print(f"Deleting ubicacion {idUbicacion}...")
            del_ubic_resp = supabase.table("ubicacion").delete().eq("idubicacion", idUbicacion).execute()
            if hasattr(del_ubic_resp, 'error') and del_ubic_resp.error:
                 print(f"Warning: Error deleting ubicacion {idUbicacion}: {del_ubic_resp.error}")
            elif not del_ubic_resp.data: print(f"Warning: No data returned deleting ubicacion {idUbicacion}.")
            else: print(f"Ubicacion {idUbicacion} deleted.")
        else: print(f"No associated ubicacion for {idParcela}.")

        print(f"Parcela {idParcela} deletion complete.")
        # Return dict
        return ({"success": True, "data": f"Parcela {idParcela} eliminada"}, 200)

    except Exception as e:
        print(f"🚨 Unexpected error in eliminar_parcela ID {idParcela}: {str(e)}")
        print(traceback.format_exc())
        # Return dict
        return ({"success": False, "error": "Error interno servidor."}, 500)