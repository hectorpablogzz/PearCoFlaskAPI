from flask import Flask, jsonify, request
from supabase import create_client, Client
from dotenv import load_dotenv
from uuid import uuid4
import os
from datetime import datetime, timedelta
import traceback # Para logs de error más detallados

# Asegúrate que estos archivos existan y no tengan errores de sintaxis
import reports
import alerts
import caficultores
import risk
import auth
import parcelas

load_dotenv()
app = Flask(__name__)

# Configuración de Supabase
NEXT_PUBLIC_SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
NEXT_PUBLIC_SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

# Validación simple de variables de entorno al inicio
if not NEXT_PUBLIC_SUPABASE_URL or not NEXT_PUBLIC_SUPABASE_ANON_KEY:
    print("🚨 ERROR: Las variables de entorno de Supabase (URL/KEY) no están configuradas.")
    # Considera salir o manejar este error de forma más robusta si es crítico
    supabase = None # O asigna un cliente dummy/inválido
else:
    try:
        supabase: Client = create_client(NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY)
    except Exception as e:
        print(f"🚨 ERROR al inicializar el cliente de Supabase: {e}")
        supabase = None # O maneja el error

BUCKET_NAME = os.getenv("SUPABASE_BUCKET", "CoffeeDiagnosisPhotos")

# --- Ruta Base (Opcional, para verificar si la API está viva) ---
@app.route("/", methods=["GET"])
def index():
    # Verifica si el cliente de Supabase se inicializó correctamente
    if supabase is None:
        return jsonify({"message": "Error: Supabase client not initialized. Check environment variables."}), 500
    return jsonify({"message": "PearCo Flask API is running!"})

# --- Login ---
@app.route("/login", methods=["POST"])
def login():
    if supabase is None: return jsonify({"success": False, "message": "Error interno del servidor (Supabase)"}), 500
    # Llama a la función de auth.py
    # Asegúrate que auth.py devuelva TUPLA (response_dict, status_code)
    try:
        response, status_code = auth.login_user(supabase, request.json)
        return jsonify(response), status_code
    except Exception as e:
        print(f"🚨 Error en la ruta /login llamando a auth.login_user: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": "Error interno del servidor durante el login."}), 500


# --- Reports (Sin cambios, asumiendo que reports.py existe y funciona) ---
@app.route("/reports", methods=["GET"])
def get_reports():
    try:
        return jsonify(reports.reports_json())
    except Exception as e:
        print(f"🚨 Error en /reports: {e}")
        return jsonify({"error": "Error al obtener reportes"}), 500

@app.route("/summary", methods=["GET"])
def get_summary():
    try:
        return jsonify(reports.summary_json())
    except Exception as e:
        print(f"🚨 Error en /summary: {e}")
        return jsonify({"error": "Error al obtener resumen"}), 500

# --- Alertas (Sin cambios funcionales, añadido chequeo de Supabase) ---
@app.route("/alerts", methods=["GET"])
def get_alerts():
    if supabase is None: return jsonify({"error": "Error interno del servidor (Supabase)"}), 500
    user_id = request.args.get("idusuario") # Asume columna 'idusuario'
    if not user_id: return jsonify({"error": "Parámetro 'idusuario' requerido"}), 400

    try:
        # Asegúrate que la función RPC 'get_alerts' existe en tu Supabase
        response = supabase.rpc("get_alerts", {"userid": user_id}).execute()
        out = []
        if response.data:
            for item in response.data:
                # Usa .get() con default por si falta alguna clave en la respuesta RPC
                out.append({
                    "idalert": item.get("idalerta"),
                    "category": item.get("categoria"),
                    "title": item.get("titulo"),
                    "action": item.get("accion"),
                    "date": item.get("fecha"),
                    "type": item.get("tipo"),
                    "isCompleted": bool(item.get("completado", False))
                })
        return jsonify(out)
    except Exception as e:
        print(f"🚨 Error en GET /alerts: {e}")
        print(traceback.format_exc())
        return jsonify({"error": "Error al obtener alertas"}), 500


@app.route("/alerts/complete", methods=["POST"])
def complete_alert():
    if supabase is None: return jsonify({"success": False, "message": "Error interno (Supabase)"}), 500
    data = request.get_json()
    id_alert = data.get("idalerta")
    is_completed = data.get("isCompleted")
    if id_alert is None or is_completed is None:
        return jsonify({"success": False, "message": "'idalerta' y 'isCompleted' son requeridos"}), 400

    try:
        # Asegúrate que la tabla 'usuarioalerta' y columna 'idalerta' existen
        response = supabase.table("usuarioalerta").update({"completado": is_completed}).eq("idalerta", id_alert).execute()
        # Supabase devuelve datos en 'data' incluso si no se actualizó nada (si el filtro coincidió)
        # Una mejor verificación podría ser si response.error existe
        if hasattr(response, 'error') and response.error:
             print(f"Error Supabase en POST /alerts/complete: {response.error}")
             return jsonify({"success": False, "message": f"Error al actualizar alerta: {response.error.message}"}), 500
        # Opcional: verificar si realmente se actualizó algo (más complejo, requiere select previo)
        return jsonify({"success": True, "message": "Alerta actualizada (o ya estaba en ese estado)"}), 200

    except Exception as e:
        print(f"🚨 Error en POST /alerts/complete: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": "Error interno al completar alerta"}), 500


@app.route("/alerts/<idalerta>", methods=["DELETE"])
def delete_alert(idalerta):
    if supabase is None: return jsonify({"success": False, "message": "Error interno (Supabase)"}), 500
    try:
        response = supabase.table("usuarioalerta").delete().eq("idalerta", idalerta).execute()
        if hasattr(response, 'error') and response.error:
             print(f"Error Supabase en DELETE /alerts/{idalerta}: {response.error}")
             return jsonify({"success": False, "message": f"Error al eliminar alerta: {response.error.message}"}), 500
        # Verificar si algo fue eliminado (response.data usualmente contiene los datos eliminados)
        if response.data:
            return jsonify({"success": True, "message": "Alerta eliminada"}), 200
        else:
            return jsonify({"success": False, "message": "No se encontró la alerta para eliminar"}), 404
    except Exception as e:
        print(f"🚨 Error en DELETE /alerts/{idalerta}: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": "Error interno al eliminar alerta"}), 500


# --- Caficultores (Sin cambios, asumiendo que caficultores.py existe y funciona) ---
@app.route("/caficultores", methods=["GET"])
def caficultores_get():
    if supabase is None: return jsonify({"error":"Error interno"}), 500
    try: return jsonify(caficultores.caficultores_json(supabase))
    except Exception as e: print(f"🚨 Error: {e}"); return jsonify({"error":"Error"}),500

@app.route("/caficultores", methods=["POST"])
def caficultores_post():
    if supabase is None: return jsonify({"error":"Error interno"}), 500
    new_caficultor = request.get_json();
    if not new_caficultor: return jsonify({"message": "No JSON"}), 400
    try: return caficultores.add_caficultor(supabase, new_caficultor)
    except Exception as e: print(f"🚨 Error: {e}"); return jsonify({"error":"Error"}),500

@app.route("/caficultores/<id>", methods=["PUT"])
def caficultores_put(id):
    if supabase is None: return jsonify({"error":"Error interno"}), 500
    data = request.get_json();
    if not data: return jsonify({"message": "No JSON"}), 400
    try: return caficultores.edit_caficultor(supabase, id, data)
    except Exception as e: print(f"🚨 Error: {e}"); return jsonify({"error":"Error"}),500

@app.route("/caficultores/<id>", methods=["DELETE"])
def caficultores_delete(id):
    if supabase is None: return jsonify({"error":"Error interno"}), 500
    try: return caficultores.delete_caficultor(supabase, id)
    except Exception as e: print(f"🚨 Error: {e}"); return jsonify({"error":"Error"}),500

# --- Parcelas CRUD (CORREGIDO para usar Strings en rutas) ---
@app.route("/parcelas", methods=["GET"])
def get_parcelas():
    if supabase is None: return jsonify({"success": False, "error": "Error interno (Supabase)"}), 500
    # Llama a la función de parcelas.py
    # Asegúrate que parcelas.py devuelva TUPLA (response_dict, status_code)
    try:
        response, status_code = parcelas.obtener_parcelas(supabase)
        return jsonify(response), status_code
    except Exception as e:
        print(f"🚨 Error en GET /parcelas: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": "Error interno al obtener parcelas."}), 500

# CORREGIDO: quitado <int:>
@app.route("/parcelas/<idParcela>", methods=["GET"])
def get_parcela(idParcela):
    if supabase is None: return jsonify({"success": False, "error": "Error interno (Supabase)"}), 500
    try:
        response, status_code = parcelas.obtener_parcela(supabase, idParcela) # Pasa el ID como string
        return jsonify(response), status_code
    except Exception as e:
        print(f"🚨 Error en GET /parcelas/{idParcela}: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": "Error interno al obtener parcela."}), 500

@app.route("/parcelas", methods=["POST"])
def post_parcela():
    if supabase is None: return jsonify({"success": False, "error": "Error interno (Supabase)"}), 500
    data = request.get_json()
    if not data: return jsonify({"success": False, "error": "Datos JSON requeridos"}), 400
    try:
        response, status_code = parcelas.crear_parcela(supabase, data)
        return jsonify(response), status_code
    except Exception as e:
        print(f"🚨 Error en POST /parcelas: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": "Error interno al crear parcela."}), 500

# CORREGIDO: quitado <int:>
@app.route("/parcelas/<idParcela>", methods=["PUT"])
def put_parcela(idParcela):
    if supabase is None: return jsonify({"success": False, "error": "Error interno (Supabase)"}), 500
    data = request.get_json()
    if not data: return jsonify({"success": False, "error": "Datos JSON requeridos"}), 400
    try:
        response, status_code = parcelas.modificar_parcela(supabase, idParcela, data) # Pasa ID como string
        return jsonify(response), status_code
    except Exception as e:
        print(f"🚨 Error en PUT /parcelas/{idParcela}: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": "Error interno al modificar parcela."}), 500

# CORREGIDO: quitado <int:>
@app.route("/parcelas/<idParcela>", methods=["DELETE"])
def delete_parcela(idParcela):
    if supabase is None: return jsonify({"success": False, "error": "Error interno (Supabase)"}), 500
    try:
        response, status_code = parcelas.eliminar_parcela(supabase, idParcela) # Pasa ID como string
        return jsonify(response), status_code
    except Exception as e:
        print(f"🚨 Error en DELETE /parcelas/{idParcela}: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": "Error interno al eliminar parcela."}), 500

# --- Riesgo (Sin cambios, asumiendo que risk.py existe y funciona) ---
@app.route("/risk/<region_id>/<int:year>/<int:month>", methods=["GET"])
def risk_one(region_id, year, month):
     if supabase is None: return jsonify({"error":"Error interno"}), 500
     try: return jsonify(risk.risk_json(supabase, region_id, year, month))
     except Exception as e: print(f"🚨 Error: {e}"); return jsonify({"error":"Error"}),500

@app.route("/risk_series/<region_id>/<int:year>", methods=["GET"])
def risk_series(region_id, year):
     if supabase is None: return jsonify({"error":"Error interno"}), 500
     try: return jsonify(risk.risk_series_json(supabase, region_id, year))
     except Exception as e: print(f"🚨 Error: {e}"); return jsonify({"error":"Error"}),500

# --- Subir Imágenes y Diagnósticos  ---
def _upload_bytes_to_storage(file_bytes: bytes, dest_path: str, content_type: str):
    """Sube bytes al bucket y devuelve URL pública. Lanza excepción en error."""
    if supabase is None: raise Exception("Supabase client not initialized")
    try:
        supabase.storage.from_(BUCKET_NAME).upload(
            file=file_bytes, path=dest_path,
            file_options={"contentType": content_type, "cacheControl": "3600", "upsert": False}
        )
        public_url_data = supabase.storage.from_(BUCKET_NAME).get_public_url(dest_path)
        # Maneja respuesta de get_public_url (puede ser string o dict en algunas versiones)
        if isinstance(public_url_data, dict):
            return public_url_data.get('publicUrl', str(public_url_data))
        return public_url_data
    except Exception as e:
        print(f"Error Supabase Storage Upload: {e}")
        raise e # Re-lanza para que la ruta lo capture

# ===== 1) POST /upload_image =====
@app.route("/upload_image", methods=["POST"])
def upload_image():
    """Recibe una imagen (multipart/form-data) y la sube al Storage."""
    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "empty filename"}), 400

    user_id = request.form.get("user_id", "anonymous")
    ext = (f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "jpg")
    dest_path = f"{user_id}/{uuid4()}.{ext}"
    content_type = f.mimetype or "image/jpeg"

    try:
        url = _upload_bytes_to_storage(f.read(), dest_path, content_type)
        return jsonify({"image_url": url, "path": dest_path}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== 2) POST /diagnostic =====
@app.route("/diagnostic", methods=["POST"])
def create_diagnostic():
    """
    Crea un registro en diagnostico_foto y genera las alertas.
    Puede recibir JSON o multipart/form-data.
    """
    id_usuario = request.form.get("idUsuario") or (request.json or {}).get("idUsuario")
    diagnostico = request.form.get("diagnostico") or (request.json or {}).get("diagnostico")
    imagen_url = request.form.get("imagen_url") or (request.json or {}).get("imagen_url")

    if not id_usuario or not diagnostico:
        return jsonify({"error": "idUsuario y diagnostico son requeridos"}), 400

    if 'file' in request.files and request.files['file'].filename:
        f = request.files['file']
        ext = (f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else 'jpg')
        dest_path = f"{id_usuario}/{uuid4()}.{ext}"
        content_type = f.mimetype or "image/jpeg"

        try:
            imagen_url = _upload_bytes_to_storage(f.read(), dest_path, content_type)
        except Exception as e:
            return jsonify({"error": f"Fallo al subir la imagen: {e}"}), 500

    if not imagen_url:
        return jsonify({"error": "Se requiere imagen_url si no se proporciona un archivo"}), 400

    # Guardar el diagnóstico
    try:
        insert_resp = supabase.table("diagnostico_foto").insert({
            "imagen_url": imagen_url,
            "idusuario": id_usuario,      # <- antes: "idUsuario"
            "diagnostico": diagnostico
        }).execute()
        
        datos_diagnostico = getattr(insert_resp, "data", [{}])[0]

    except Exception as e:
        return jsonify({"error": f"Error al guardar el diagnóstico: {str(e)}"}), 500

    # Generar alertas asociadas
    try:
        alerta_resp = supabase.table("alertas").select("*").eq("enfermedad", diagnostico).execute()
        alertas_configuradas = alerta_resp.data or []

        if not alertas_configuradas:
            return jsonify({
                "message": "Diagnóstico creado",
                "diagnosis_details": datos_diagnostico
            }), 201

        fecha_deteccion = datetime.now()
        alertas_generadas_count = 0

        for alerta in alertas_configuradas:
            dias_para_alerta = alerta.get("diasParaAlerta", 0)
            fecha_alerta = fecha_deteccion + timedelta(days=dias_para_alerta)
            fecha_alerta_str = fecha_alerta.strftime("%Y-%m-%d")

            supabase.table("usuarioalerta").insert({
                "idusuario": id_usuario,
                "idalerta": alerta["idalerta"],
                "fecha": fecha_alerta_str,
                "completado": False
            }).execute()

            alertas_generadas_count += 1

    except Exception as e:
        return jsonify({
            "message": "Diagnóstico creado, sin alertas nuevas para generar.",
            "error_alertas": str(e),
            "diagnosis_details": datos_diagnostico
        }), 207  # 207 Multi-Status

    return jsonify({
        "message": "Diagnóstico creado. Se han generado nuevas alertas.",
        "diagnosis_details": datos_diagnostico,
        "alerts_generated": alertas_generadas_count
    }), 201

# CORREGIDO: Casing idusuario y Select
@app.route("/diagnoses", methods=["GET"])
def list_diagnoses():
    if supabase is None: return jsonify({"error": "Error interno (Supabase)"}), 500
    # Usa consistentemente 'idusuario'
    id_usuario_key = "idusuario"
    id_usuario = request.args.get(id_usuario_key)
    limit = int(request.args.get("limit", "50"))
    offset = int(request.args.get("offset", "0"))
    try:
        # Asegúrate que la relación FK esté bien definida en Supabase
        # diagnostico_foto.diagnostico -> diagnostico.enfermedad
        # Y que las columnas en diagnostico existan
        select_query = (
            "iddiagnostico, imagen_url, fecha, idusuario, diagnostico, " # Columnas de diagnostico_foto
            "diagnostico!inner(descripcion, causas, prevencion, tratamiento)" # JOIN a tabla diagnostico
        )
        q = supabase.table("diagnostico_foto").select(select_query).order("fecha", desc=True)

        if id_usuario:
            q = q.eq(id_usuario_key, id_usuario) # Filtra por usuario

        q = q.range(offset, offset + limit - 1)
        resp = q.execute()

        if hasattr(resp, 'error') and resp.error:
             print(f"Error Supabase en GET /diagnoses: {resp.error}")
             return jsonify({"error": f"Error al listar diagnósticos: {resp.error.message}"}), 500

        data = resp.data or [] # Devuelve lista vacía si no hay datos
        return jsonify(data), 200
    except Exception as e:
        print(f"🚨 Error en GET /diagnoses: {e}")
        print(traceback.format_exc())
        return jsonify({"error": f"Error interno al listar diagnósticos: {str(e)}"}), 500

# --- Inicio de la Aplicación (Importante para Render) ---
if __name__ == "__main__":
    # Esto es principalmente para desarrollo local
    print("Iniciando servidor Flask para desarrollo local...")
    # Render usará el 'Start Command' (ej: gunicorn), no este bloque
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5050)), debug=True) # debug=True ayuda en local
