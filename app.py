from flask import Flask, jsonify, request
from supabase import create_client, Client
from dotenv import load_dotenv
import os

import reports
import alerts
import caficultores

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

# Alertas
# @app.route("/alerts2", methods=["GET"])
# def get_alerts():
#     return jsonify(alerts.alerts_json())
    
@app.route("/alerts", methods=["GET"])
def get_alerts():
    response = supabase.table("alertas").select("*").execute()
    return jsonify(response.data)
    
## Caficultores ##
@app.route("/caficultores", methods=["GET"])
def get_caficultores():
    response = (
        supabase.table("caficultores")
        .select("*")
        .execute()
    )
    print(response)
    return response.data
    #return jsonify(caficultores.caficultores_json(supabase))

@app.route("/caficultores", methods=["POST"])
def add_caficultor():
    new_caficultor = request.get_json()
    print("Caficultor agregado")
    print(new_caficultor)

    return jsonify({'message': 'Caficultor agregado exitosamente'}), 200

@app.route("/caficultores/<id>", methods=["PUT"])
def update_caficultor(id):
    data = request.get_json(silent=True) or {}
    print(f"Caficultor actualizado: id={id}")
    print(data)
    return jsonify({'message': 'Caficultor actualizado exitosamente'}), 200


@app.route("/caficultores/<id>", methods=["DELETE"])
def delete_caficultor(id):
    print(f"Caficultor eliminado: id={id}")
    return jsonify({'message': 'Caficultor eliminado exitosamente'}), 200



    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
