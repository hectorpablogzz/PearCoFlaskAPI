from flask import Flask, jsonify, request

import reports

app = Flask(__name__)




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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
