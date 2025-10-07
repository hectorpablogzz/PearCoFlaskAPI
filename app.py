from flask import Flask, jsonify, request
from supabase import create_client, Client

import reports
import alerts
import caficultores

app = Flask(__name__)


NEXT_PUBLIC_SUPABASE_URL="https://punmnfgtbcknqxgyajkk.supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB1bm1uZmd0YmNrbnF4Z3lhamtrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk2NzkxOTIsImV4cCI6MjA3NTI1NTE5Mn0.Qx7Cbb3-4Ijy-HwgZv-O5Kj0W7RA716lzHSJ4EBcppc"

supabase: Client = create_client(supabase_url=NEXT_PUBLIC_SUPABASE_URL, supabase_key=NEXT_PUBLIC_SUPABASE_ANON_KEY)

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
    return jsonify(caficultores.caficultores_json())

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
