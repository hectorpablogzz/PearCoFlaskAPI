from flask import Flask, jsonify, request
from supabase import create_client, Client
from dotenv import load_dotenv
from uuid import uuid4
from flask_cors import CORS
import os

import reports
import alerts
import caficultores
import risk
import auth
import parcelas  

CORS(app)

load_dotenv()

app = Flask(__name__)

NEXT_PUBLIC_SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
NEXT_PUBLIC_SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
supabase: Client = create_client(NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY)
BUCKET_NAME = os.getenv("SUPABASE_BUCKET", "CoffeeDiagnosisPhotos")



@app.route("/", methods=["GET"])
def index():
    who = request.args.get("who", "world")
    return jsonify({"message": f"it works, {who}!"})



@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    return auth.login_user(supabase, data)



@app.route("/reports", methods=["GET"])
def get_reports():
    return jsonify(reports.reports_json())

@app.route("/summary", methods=["GET"])
def get_summary():
    return jsonify(reports.summary_json())



@app.route("/detections", methods=["POST"])
def detections():
    data = request.get_json()
    idusuario = data.get("iduser")
    idenfermedad = data.get("iddissease")
    fecha = data.get("date")
    
    supabase.table("deteccion").insert({
        "idusuario": idusuario,
        "idenfermedad": idenfermedad,
        "fecha": fecha,
    }).execute()

    alerta_resp = supabase.table("alertas").select("*").eq("idenfermedad", idenfermedad).execute()
    alertas = alerta_resp.data or []

    from datetime import datetime, timedelta
    for alerta in alertas:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
        fecha_alerta = fecha_dt + timedelta(days=alerta.get("diasParaAlerta", 0))
        fecha_alerta_str = fecha_alerta.strftime("%Y-%m-%d")
        supabase.table("usuarioalerta").insert({
            "idusuario": idusuario,
            "idalerta": alerta["idalerta"],
            "fecha": fecha_alerta_str,
            "completado": False
        }).execute()

    return jsonify({"success": True, "message": "Detección registrada y alertas generadas"}), 201


# Alerts
@app.route("/alerts", methods=["GET"])
def get_alerts():
    user_id = request.args.get("idusuario")
    response = supabase.rpc("get_alerts", {"userid": user_id}).execute()
    out = []
    for item in response.data:
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


@app.route("/alerts/complete", methods=["POST"])
def complete_alert():
    data = request.get_json()
    id_alert = data.get("idalerta")
    is_completed = data.get("isCompleted")
    response = supabase.table("usuarioalerta").update({"completado": is_completed}).eq("idalerta", id_alert).execute()
    if response.data:
        return jsonify({"success": True, "updated": response.data}), 200
    else:
        return jsonify({"success": False, "message": "No se encontró la alerta"}), 404


@app.route("/alerts/<idalerta>", methods=["DELETE"])
def delete_alert(idalerta):
    response = supabase.table("usuarioalerta").delete().eq("idalerta", idalerta).execute()
    if response.data:
        return jsonify({"success": True, "deleted": response.data}), 200
    else:
        return jsonify({"success": False, "message": "No se encontró la alerta"}), 404


# Caficultores
@app.route("/caficultores", methods=["GET"])
def caficultores_get():
    return jsonify(caficultores.caficultores_json(supabase))

@app.route("/caficultores", methods=["POST"])
def caficultores_post():
    new_caficultor = request.get_json()
    if not new_caficultor:
        return jsonify({"message": "No JSON data received"}), 400
    return caficultores.add_caficultor(supabase, new_caficultor)

@app.route("/caficultores/<id>", methods=["PUT"])
def caficultores_put(id):
    data = request.get_json()
    if not data:
        return jsonify({"message": "No JSON data received"}), 400
    return caficultores.edit_caficultor(supabase, id, data)

@app.route("/caficultores/<id>", methods=["DELETE"])
def caficultores_delete(id):
    return caficultores.delete_caficultor(supabase, id)


# Parcelas CRUD
@app.route("/parcelas", methods=["GET"])
def get_parcelas():
    return parcelas.obtener_parcelas(supabase)

@app.route("/parcelas/<int:idParcela>", methods=["GET"])
def get_parcela(idParcela):
    return parcelas.obtener_parcela(supabase, idParcela)

@app.route("/parcelas", methods=["POST"])
def post_parcela():
    data = request.get_json()
    return parcelas.crear_parcela(supabase, data)

@app.route("/parcelas/<int:idParcela>", methods=["PUT"])
def put_parcela(idParcela):
    data = request.get_json()
    return parcelas.modificar_parcela(supabase, idParcela, data)

@app.route("/parcelas/<int:idParcela>", methods=["DELETE"])
def delete_parcela(idParcela):
    return parcelas.eliminar_parcela(supabase, idParcela)


# Riesgo mensual
@app.route("/risk/<region_id>/<int:year>/<int:month>", methods=["GET"])
def risk_one(region_id, year, month):
    return jsonify(risk.risk_json(supabase, region_id, year, month))

@app.route("/risk_series/<region_id>/<int:year>", methods=["GET"])
def risk_series(region_id, year):
    return jsonify(risk.risk_series_json(supabase, region_id, year))


# Subir imágenes y diagnósticos
def _upload_bytes_to_storage(file_bytes: bytes, dest_path: str, content_type: str):
    storage_resp = supabase.storage.from_(BUCKET_NAME).upload(
        file=file_bytes,
        path=dest_path,
        file_options={"contentType": content_type, "cacheControl": "3600", "upsert": False},
    )
    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(dest_path)
    if isinstance(public_url, dict) and 'publicUrl' in public_url:
        return public_url['publicUrl']
    return public_url

@app.route("/upload_image", methods=["POST"])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "file is required"}), 400
    f = request.files['file']
    if f.filename == "":
        return jsonify({"error": "empty filename"}), 400

    user_id = request.form.get("user_id", "anonymous")
    ext = (f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else 'jpg')
    dest_path = f"{user_id}/{uuid4()}.{ext}"
    content_type = f.mimetype or "image/jpeg"

    try:
        file_bytes = f.read()
        url = _upload_bytes_to_storage(file_bytes, dest_path, content_type)
        return jsonify({"image_url": url, "path": dest_path}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Crear diágnostico
@app.route("/diagnoses", methods=["POST"])
def create_diagnosis():
    """Crea un registro en diagnostico_foto. 
       Puede recibir JSON o multipart/form-data."""
    id_usuario = request.form.get("idUsuario") or (request.json or {}).get("idUsuario")
    diagnostico = request.form.get("diagnostico") or (request.json or {}).get("diagnostico")  # Nombre del diagnóstico
    imagen_url = request.form.get("imagen_url") or (request.json or {}).get("imagen_url")

    if not id_usuario or not diagnostico:
        return jsonify({"error": "idUsuario and diagnostico are required"}), 400

    # Si viene un archivo, se sube y se usa su URL
    if 'file' in request.files and request.files['file'].filename:
        f = request.files['file']
        ext = (f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else 'jpg')
        dest_path = f"{id_usuario}/{uuid4()}.{ext}"
        content_type = f.mimetype or "image/jpeg"
        try:
            imagen_url = _upload_bytes_to_storage(f.read(), dest_path, content_type)
        except Exception as e:
            return jsonify({"error": f"upload failed: {e}"}), 500

    if not imagen_url:
        return jsonify({"error": "imagen_url is required when file is not provided"}), 400

    try:
        insert_resp = supabase.table("diagnostico_foto").insert({
            "imagen_url": imagen_url,
            "idUsuario": id_usuario,
            "diagnostico": diagnostico  # Guardamos el nombre del diagnóstico
        }).execute()
        data = getattr(insert_resp, "data", None) or insert_resp
        return jsonify({"message": "created", "rows": data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Obtener diágnostico de un usuario
@app.route("/diagnoses", methods=["GET"])
def list_diagnoses():
    """Lista diagnósticos filtrados por idUsuario (usuario) con detalles del diagnóstico."""
    id_usuario = request.args.get("idUsuario")
    limit = int(request.args.get("limit", "50"))
    offset = int(request.args.get("offset", "0"))
    try:
        # Hacer un JOIN entre diagnostico_foto y diagnostico para obtener detalles completos
        q = supabase.table("diagnostico_foto") \
            .select("*, diagnostico(descripcion, causas, prevencion, tratamiento)") \
            .order("fecha", desc=True)
        if id_usuario:
            q = q.eq("idUsuario", id_usuario)
        q = q.range(offset, offset + limit - 1)
        resp = q.execute()
        data = getattr(resp, "data", None) or resp
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
