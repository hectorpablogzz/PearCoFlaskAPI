from flask import jsonify

def reports_json():
    alerts = [
        {
            "category": "Enfermedades",
            "title": "Solucionar plaga",
            "action": "Aplica el tratamiento necesario para combatir la broca del cafe",
            "date": "2025-09-30T08:00:00Z",
            "isCompleted": False
        },
        {
            "category": "Fertilización",
            "title": "Fertilizar",
            "action": "Revisar estado de fertilización de la parcela",
            "date": "2025-09-29T08:00:00Z",
            "isCompleted": False
        },
        {
            "category": "Clima",
            "title": "Clima extremadamente caluroso",
            "action": "Recuerda regar las plantas",
            "date": "2025-09-30T08:00:00Z",
            "isCompleted": False
        },
        {
            "category": "Clima",
            "title": "Clima propenso a enfermedades",
            "action": "Las condiciones actuales del clima pueden generar enfermedades, toma precauciones",
            "date": "2025-09-30T08:00:00Z",
            "isCompleted": False
        }
    ]
    return alerts
