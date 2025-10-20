from flask import Flask, jsonify, request
from supabase import create_client, Client
from dotenv import load_dotenv
import os

import reports
import alerts
import caficultores
import risk

load_dotenv()

app = Flask(__name__)


NEXT_PUBLIC_SUPABASE_URL=os.getenv("NEXT_PUBLIC_SUPABASE_URL")
NEXT_PUBLIC_SUPABASE_ANON_KEY=os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
supabase: Client = create_client(NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY)

@app.route("/", methods=["GET"])
def index():
    who = request.args.get("who", "world")
    return jsonify({"message": f"it works, {who}!"})

@app.route("/reports", methods=["GET"])
def get_reports():
    return jsonify(reports.reports_json())

@app.route("/summary", methods=["GET"])
def get_summary():
    return jsonify(reports.summary_json())
    
# Detecciones (camara)

@app.route("/detections", methods=["POST"])
def detections():
    """
    Recibe un JSON con la detección de enfermedad:
    {
        "iduser": 23,
        "iddissease": 5,
        "date": "2025-10-15"
    }
    """
    data = request.get_json()
    idusuario = data.get("iduser")
    idenfermedad = data.get("iddissease")
    fecha = data.get("date")  # ya en "YYYY-MM-DD"

    # Guardar la detección
    supabase.table("deteccion").insert({
        "idusuario": idusuario,
        "idenfermedad": idenfermedad,
        "fecha": fecha,
    }).execute()

    # Buscar alertas configuradas para esta enfermedad
    alerta_resp = supabase.table("alertas").select("*").eq("idenfermedad", idenfermedad).execute()
    alertas = alerta_resp.data or []

    for alerta in alertas:
        # calcular fecha de alerta sumando dias
        from datetime import datetime, timedelta
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
        fecha_alerta = fecha_dt + timedelta(days=alerta.get("diasParaAlerta", 0))
        fecha_alerta_str = fecha_alerta.strftime("%Y-%m-%d")

        # Crear alerta para el usuario
        supabase.table("usuarioalerta").insert({
            "idusuario": idusuario,
            "idalerta": alerta["idalerta"],
            "fecha": fecha_alerta_str,
            "completado": False
        }).execute()

    return jsonify({"success": True, "message": "Detección registrada y alertas generadas"}), 201

# Alertas

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
def complete():
    data = request.get_json()
    id_alert = data.get("idalerta")
    is_completed = data.get("isCompleted")

    # Ejecutar RPC o Update directo
    response = supabase.table("usuarioalerta") \
        .update({"completado": is_completed}) \
        .eq("idalerta", id_alert) \
        .execute()

    if response.data:
        return jsonify({"success": True, "updated": response.data}), 200
    else:
        return jsonify({"success": False, "message": "No se encontró la alerta"}), 404

@app.route("/alerts/<idalerta>", methods=["DELETE"])
def delete(idalerta):
    response = supabase.table("usuarioalerta") \
        .delete() \
        .eq("idalerta", idalerta) \
        .execute()

    if response.data:
        return jsonify({"success": True, "deleted": response.data}), 200
    else:
        return jsonify({"success": False, "message": "No se encontró la alerta"}), 404

## Caficultores ##
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
    #print(f"Caficultor eliminado: id={id}")
    #return jsonify({'message': 'Caficultor eliminado exitosamente'}), 200
    return caficultores.delete_caficultor(supabase, id)

# Riesgo mensual
@app.route("/risk/<region_id>/<int:year>/<int:month>", methods=["GET"])
def risk_one(region_id, year, month):
    return jsonify(risk.risk_json(supabase, region_id, year, month))

@app.route("/risk_series/<region_id>/<int:year>", methods=["GET"])
def risk_series(region_id, year):
    return jsonify(risk.risk_series_json(supabase, region_id, year))


    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
