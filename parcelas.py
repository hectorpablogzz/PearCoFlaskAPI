from flask import jsonify
from supabase import Client
import traceback # For detailed error logging

# --- Crear Parcela ---
def crear_parcela(supabase: Client, data: dict):
    ubic = data.get("ubicacion") or {}
    # Validate required fields
    missing_parcela = [f for f in ("nombre", "hectareas", "tipo") if f not in data]
    missing_ubic = [f for f in ("estado", "municipio", "latitud", "longitud") if f not in ubic]
    if missing_parcela or missing_ubic:
        print(f"Validation failed - Missing fields: Parcela={missing_parcela}, Ubicacion={missing_ubic}")
        # Return tuple
        return (jsonify({
            "success": False,
            "error": "Datos incompletos",
            "missing": {"parcela": missing_parcela, "ubicacion": missing_ubic}
        }), 400)

    id_ubicacion_creada = None # Initialize in case of early failure
    try:
        # 1. Insertar ubicación ('ubicacion' table)
        ubicacion_payload = {
            "estado": ubic.get("estado"),
            "municipio": ubic.get("municipio"),
            "latitud": ubic.get("latitud"),
            "longitud": ubic.get("longitud")
        }
        print(f"Inserting ubicacion: {ubicacion_payload}")
        ubic_resp = supabase.table("ubicacion").insert(ubicacion_payload).execute()

        # Check for Supabase errors after insertion
        if hasattr(ubic_resp, 'error') and ubic_resp.error:
             print(f"Error Supabase inserting ubicacion: {ubic_resp.error}")
             # Return tuple
             return (jsonify({"success": False, "error": f"No se pudo crear la ubicación: {ubic_resp.error.message}"}), 500)
        if not ubic_resp.data:
             print(f"Error inserting ubicacion: No data returned. Response: {ubic_resp}")
             # Return tuple
             return (jsonify({"success": False, "error": "No se pudo crear la ubicación (respuesta inesperada)"}), 500)

        # Get the ID (use lowercase key 'idubicacion')
        ubicacion_creada = ubic_resp.data[0]
        id_ubicacion_creada = ubicacion_creada.get("idubicacion")
        if not id_ubicacion_creada:
             print("Error: 'idubicacion' key missing in response from ubicacion insert.")
             # Return tuple
             return (jsonify({"success": False, "error": "Error interno al obtener ID de ubicación"}), 500)
        print(f"Ubicacion created successfully: {id_ubicacion_creada}")

        # 2. Insertar parcela ('parcela' table, use lowercase 'idubicacion')
        parcela_payload = {
            "nombre": data.get("nombre"),
            "hectareas": data.get("hectareas"),
            "tipo": data.get("tipo"),
            "idubicacion": id_ubicacion_creada # Foreign key
        }
        print(f"Inserting parcela: {parcela_payload}")
        parcela_resp = supabase.table("parcela").insert(parcela_payload).execute()

        # Check for Supabase errors after insertion
        if hasattr(parcela_resp, 'error') and parcela_resp.error:
            print(f"Error Supabase inserting parcela: {parcela_resp.error}. Rolling back ubicacion.")
            # Attempt rollback
            try: supabase.table("ubicacion").delete().eq("idubicacion", id_ubicacion_creada).execute()
            except Exception as rb_e: print(f"Error during rollback: {rb_e}")
            # Return tuple
            return (jsonify({"success": False, "error": f"No se pudo crear la parcela: {parcela_resp.error.message}"}), 500)
        if not parcela_resp.data:
             print(f"Error inserting parcela: No data returned. Rolling back ubicacion. Response: {parcela_resp}")
             # Attempt rollback
             try: supabase.table("ubicacion").delete().eq("idubicacion", id_ubicacion_creada).execute()
             except Exception as rb_e: print(f"Error during rollback: {rb_e}")
             # Return tuple
             return (jsonify({"success": False, "error": "No se pudo crear la parcela (respuesta inesperada)"}), 500)

        # Success: Combine data for response
        parcela_creada = parcela_resp.data[0]
        parcela_creada["ubicacion"] = ubicacion_creada # Embed location details

        print(f"Parcela created successfully: {parcela_creada.get('idparcela')}")
        # Return tuple
        return (jsonify({"success": True, "data": parcela_creada}), 201)

    except Exception as e:
        print(f"🚨 Unexpected error in crear_parcela: {str(e)}")
        print(traceback.format_exc()) # Print full traceback for debugging
        # Attempt rollback if ubicacion was created
        if id_ubicacion_creada:
             try:
                 print(f"Attempting rollback for ubicacion {id_ubicacion_creada} due to unexpected error.")
                 supabase.table("ubicacion").delete().eq("idubicacion", id_ubicacion_creada).execute()
             except Exception as rollback_e:
                 print(f"Error during unexpected error rollback: {rollback_e}")
        # Return tuple
        return (jsonify({"success": False, "error": "Error interno del servidor al crear parcela."}), 500)

# --- Obtener Todas las Parcelas ---
def obtener_parcelas(supabase: Client):
    try:
        print("Fetching all parcelas with ubicacion...")
        # Select parcela and join related ubicacion data ('ubicacion(*)')
        response = supabase.table("parcela").select("*, ubicacion(*)").execute()

        # Check for Supabase errors
        if hasattr(response, 'error') and response.error:
             print(f"Error Supabase fetching parcelas: {response.error}")
             # Return tuple
             return (jsonify({"success": False, "error": f"Error al obtener parcelas: {response.error.message}"}), 500)

        # response.data will be an empty list if no parcelas exist, which is valid
        data = response.data or []
        print(f"Fetched {len(data)} parcelas.")
        # Return tuple
        return (jsonify({"success": True, "data": data}), 200) # Return empty list if none found

    except Exception as e:
        print(f"🚨 Unexpected error in obtener_parcelas: {str(e)}")
        print(traceback.format_exc())
        # Return tuple
        return (jsonify({"success": False, "error": "Error interno del servidor al obtener parcelas."}), 500)

# --- Obtener Una Parcela por ID ---
def obtener_parcela(supabase: Client, idParcela: str):
    try:
        # Use lowercase 'idparcela' for query
        print(f"Fetching parcela with id: {idParcela}")
        response = supabase.table("parcela").select("*, ubicacion(*)").eq("idparcela", idParcela).limit(1).execute() # limit(1)

        # Check for Supabase errors
        if hasattr(response, 'error') and response.error:
             print(f"Error Supabase fetching parcela {idParcela}: {response.error}")
             # Return tuple
             return (jsonify({"success": False, "error": f"Error al obtener parcela: {response.error.message}"}), 500)

        if not response.data:
            print(f"Parcela not found: {idParcela}")
            # Return tuple
            return (jsonify({"success": False, "error": "Parcela no encontrada"}), 404)

        print(f"Parcela {idParcela} found.")
        # Return tuple
        return (jsonify({"success": True, "data": response.data[0]}), 200)

    except Exception as e:
        print(f"🚨 Unexpected error in obtener_parcela for ID {idParcela}: {str(e)}")
        print(traceback.format_exc())
        # Return tuple
        return (jsonify({"success": False, "error": "Error interno del servidor al obtener parcela."}), 500)

# --- Modificar Parcela ---
def modificar_parcela(supabase: Client, idParcela: str, data: dict):
    current_idUbicacion = None # Keep track for logging/potential errors
    try:
        print(f"Attempting to modify parcela: {idParcela} with data: {data}")

        # 1. Update related location if 'ubicacion' data is present
        if "ubicacion" in data and isinstance(data["ubicacion"], dict):
            # First, get the current idubicacion linked to the parcela
            parcela_resp = supabase.table("parcela").select("idubicacion").eq("idparcela", idParcela).limit(1).execute()

            if hasattr(parcela_resp, 'error') and parcela_resp.error:
                 print(f"Error fetching idubicacion for parcela {idParcela}: {parcela_resp.error}")
                 return (jsonify({"success": False, "error": f"Error al buscar parcela para actualizar ubicación: {parcela_resp.error.message}"}), 500)
            if not parcela_resp.data:
                print(f"Parcela {idParcela} not found when trying to update ubicacion.")
                return (jsonify({"success": False, "error": "Parcela no encontrada para actualizar ubicación"}), 404)

            current_idUbicacion = parcela_resp.data[0].get("idubicacion")
            if not current_idUbicacion:
                 print(f"Error: Parcela {idParcela} has no linked idubicacion.")
                 return (jsonify({"success": False, "error": "Error interno: Parcela sin ubicación asociada"}), 500)

            # Prepare ubicacion payload (only include fields present in input)
            ubicacion_payload = {k: data["ubicacion"][k] for k in ("estado", "municipio", "latitud", "longitud") if k in data["ubicacion"]}
            if ubicacion_payload:
                print(f"Updating ubicacion {current_idUbicacion} with payload: {ubicacion_payload}")
                update_ubic_resp = supabase.table("ubicacion").update(ubicacion_payload).eq("idubicacion", current_idUbicacion).execute()
                # Check for errors during ubicacion update
                if hasattr(update_ubic_resp, 'error') and update_ubic_resp.error:
                     print(f"Error Supabase updating ubicacion {current_idUbicacion}: {update_ubic_resp.error}")
                     # Decide if this should stop the whole update
                     return (jsonify({"success": False, "error": f"Error al actualizar ubicación: {update_ubic_resp.error.message}"}), 500)
            else:
                 print("No fields provided to update for ubicacion.")

        # 2. Update parcela fields if present
        parcela_payload = {k: data[k] for k in ("nombre", "hectareas", "tipo") if k in data}
        if parcela_payload:
            print(f"Updating parcela {idParcela} with payload: {parcela_payload}")
            update_parc_resp = supabase.table("parcela").update(parcela_payload).eq("idparcela", idParcela).execute()
            # Check for errors during parcela update
            if hasattr(update_parc_resp, 'error') and update_parc_resp.error:
                 print(f"Error Supabase updating parcela {idParcela}: {update_parc_resp.error}")
                 return (jsonify({"success": False, "error": f"Error al actualizar parcela: {update_parc_resp.error.message}"}), 500)
        else:
             print("No fields provided to update for parcela.")


        print(f"Modification process complete for {idParcela}. Fetching updated data...")
        # Fetch and return the updated parcela (obtener_parcela already returns a tuple)
        return obtener_parcela(supabase, idParcela)

    except Exception as e:
        print(f"🚨 Unexpected error in modificar_parcela for ID {idParcela}: {str(e)}")
        print(traceback.format_exc())
        return (jsonify({"success": False, "error": "Error interno del servidor al modificar parcela."}), 500)

# --- Eliminar Parcela ---
def eliminar_parcela(supabase: Client, idParcela: str):
    idUbicacion = None # Keep track for logging
    try:
        print(f"Attempting to delete parcela: {idParcela}")
        # 1. Find the linked idubicacion first
        parcela_resp = supabase.table("parcela").select("idubicacion").eq("idparcela", idParcela).limit(1).execute()

        # Check errors finding the parcela
        if hasattr(parcela_resp, 'error') and parcela_resp.error:
            print(f"Error finding parcela {idParcela} for deletion: {parcela_resp.error}")
            return (jsonify({"success": False, "error": f"Error al buscar parcela para eliminar: {parcela_resp.error.message}"}), 500)
        if not parcela_resp.data:
            print(f"Parcela {idParcela} not found for deletion.")
            return (jsonify({"success": False, "error": "Parcela no encontrada"}), 404)

        idUbicacion = parcela_resp.data[0].get("idubicacion")

        # 2. Delete parcela record (use lowercase 'idparcela')
        print(f"Deleting parcela record {idParcela}...")
        delete_parcela_resp = supabase.table("parcela").delete().eq("idparcela", idParcela).execute()

        # Check errors during parcela deletion
        if hasattr(delete_parcela_resp, 'error') and delete_parcela_resp.error:
             error_msg = delete_parcela_resp.error.message
             # Check for foreign key violation specifically
             if "violates foreign key constraint" in error_msg.lower():
                 print(f"Error deleting parcela {idParcela}: Foreign key violation.")
                 # Return 409 Conflict
                 return (jsonify({"success": False, "error": "No se puede eliminar la parcela porque está asignada a un usuario."}), 409)
             else:
                 print(f"Error Supabase deleting parcela {idParcela}: {delete_parcela_resp.error}")
                 return (jsonify({"success": False, "error": f"Error al eliminar parcela: {error_msg}"}), 500)
        # Check if data was returned (Supabase delete returns deleted rows)
        if not delete_parcela_resp.data:
             print(f"Warning: Delete command for parcela {idParcela} executed without error, but no data returned (might already be deleted?).")
             # Consider returning 404 here, or continue to delete ubicacion if idUbicacion exists

        # 3. If parcela deletion was successful (or seemed to be) and idUbicacion exists, delete ubicacion
        if idUbicacion:
            print(f"Deleting associated ubicacion record {idUbicacion}...")
            delete_ubicacion_resp = supabase.table("ubicacion").delete().eq("idubicacion", idUbicacion).execute()
            # Check for errors during ubicacion deletion (log but don't fail the whole operation)
            if hasattr(delete_ubicacion_resp, 'error') and delete_ubicacion_resp.error:
                 print(f"Warning: Parcela {idParcela} deleted, but error deleting associated ubicacion {idUbicacion}: {delete_ubicacion_resp.error}")
            elif not delete_ubicacion_resp.data:
                 print(f"Warning: Delete command for ubicacion {idUbicacion} executed without error, but no data returned (might already be deleted?).")
            else:
                 print(f"Associated ubicacion {idUbicacion} deleted successfully.")
        else:
            print(f"Parcela {idParcela} deleted, no associated ubicacion found or ID was null.")

        print(f"Parcela {idParcela} deletion process completed.")
        # Return tuple
        return (jsonify({"success": True, "data": f"Parcela con id {idParcela} eliminada correctamente"}), 200)

    except Exception as e:
        print(f"🚨 Unexpected error in eliminar_parcela for ID {idParcela}: {str(e)}")
        print(traceback.format_exc())
        # Return tuple
        return (jsonify({"success": False, "error": "Error interno del servidor al eliminar parcela."}), 500)