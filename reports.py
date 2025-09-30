from flask import jsonify

def reports_json():
    reports = [
        {
            "title": "Septiembre 2025",
            "message": "Este mes hubo un aumento drástico en el riesgo del desarrollo de plagas y enfermedades debido al alto volumen de lluvia. El riesgo de roya subió a 95% y el riesgo de broca a 75%.",
            "data": [
                {"year": 2025, "month": "Apr", "temperature": 21.133, "rain": 50, "royaRisk": 35, "brocaRisk": 40, "ojoRisk": 77, "antracRisk": 45},
                {"year": 2025, "month": "May", "temperature": 23.538, "rain": 78.8, "royaRisk": 50, "brocaRisk": 60, "ojoRisk": 36, "antracRisk": 91},
                {"year": 2025, "month": "Jun", "temperature": 22.883, "rain": 179.8, "royaRisk": 90, "brocaRisk": 70, "ojoRisk": 24, "antracRisk": 21},
                {"year": 2025, "month": "Jul", "temperature": 21.451, "rain": 64.56, "royaRisk": 45, "brocaRisk": 50, "ojoRisk": 40, "antracRisk": 21},
                {"year": 2025, "month": "Aug", "temperature": 22.564, "rain": 63.2, "royaRisk": 55, "brocaRisk": 55, "ojoRisk": 100, "antracRisk": 19},
                {"year": 2025, "month": "Sep", "temperature": 22.45, "rain": 208.5, "royaRisk": 95, "brocaRisk": 75, "ojoRisk": 58, "antracRisk": 59}
            ]
        },
        {
            "title": "Agosto 2025",
            "message": "Este mes hubo un ligero aumento en el riesgo del desarrollo de plagas y enfermedades debido al aumento de temperatura. El riesgo de roya subió a 55% y el riesgo de broca a 55%.",
            "data": [
                {"year": 2025, "month": "Mar", "temperature": 19.072, "rain": 25.4, "royaRisk": 15, "brocaRisk": 20, "ojoRisk": 51, "antracRisk": 70},
                {"year": 2025, "month": "Apr", "temperature": 21.133, "rain": 50, "royaRisk": 35, "brocaRisk": 40, "ojoRisk": 43, "antracRisk": 56},
                {"year": 2025, "month": "May", "temperature": 23.538, "rain": 78.8, "royaRisk": 50, "brocaRisk": 60, "ojoRisk": 52, "antracRisk": 83},
                {"year": 2025, "month": "Jun", "temperature": 22.883, "rain": 179.8, "royaRisk": 90, "brocaRisk": 70, "ojoRisk": 57, "antracRisk": 64},
                {"year": 2025, "month": "Jul", "temperature": 21.451, "rain": 64.56, "royaRisk": 45, "brocaRisk": 50, "ojoRisk": 47, "antracRisk": 43},
                {"year": 2025, "month": "Aug", "temperature": 22.564, "rain": 63.2, "royaRisk": 55, "brocaRisk": 55, "ojoRisk": 60, "antracRisk": 81}
            ]
        },
        {
            "title": "Julio 2025",
            "message": "Este mes hubo una reducción drástica en el riesgo del desarrollo de plagas y enermedades debido a la reducción en el volumen de lluvia. El riesgo de roya bajó a 45% y el riesgo de broca a 50%.",
            "data": [
                {"year": 2025, "month": "Feb", "temperature": 18.107, "rain": 57.4, "royaRisk": 20, "brocaRisk": 30, "ojoRisk": 81, "antracRisk": 60},
                {"year": 2025, "month": "Mar", "temperature": 19.072, "rain": 25.4, "royaRisk": 15, "brocaRisk": 20, "ojoRisk": 50, "antracRisk": 1},
                {"year": 2025, "month": "Apr", "temperature": 21.133, "rain": 50, "royaRisk": 35, "brocaRisk": 40, "ojoRisk": 26, "antracRisk": 32},
                {"year": 2025, "month": "May", "temperature": 23.538, "rain": 78.8, "royaRisk": 50, "brocaRisk": 60, "ojoRisk": 53, "antracRisk": 100},
                {"year": 2025, "month": "Jun", "temperature": 22.883, "rain": 179.8, "royaRisk": 90, "brocaRisk": 70, "ojoRisk": 22, "antracRisk": 53},
                {"year": 2025, "month": "Jul", "temperature": 21.451, "rain": 64.56, "royaRisk": 45, "brocaRisk": 50, "ojoRisk": 64, "antracRisk": 25}
            ]
        },
        {
            "title": "Junio 2025",
            "message": "Este mes hubo un aumento drástico en el riesgo del desarrollo de plagas y enfermedades debido al alto volumen de lluvia. El riesgo de roya subió a 90% y el riesgo de broca a 70%.",
            "data": [
                {"year": 2025, "month": "Jan", "temperature": 16.338, "rain": 33.8, "royaRisk": 10, "brocaRisk": 15, "ojoRisk": 51, "antracRisk": 52},
                {"year": 2025, "month": "Feb", "temperature": 18.107, "rain": 57.4, "royaRisk": 20, "brocaRisk": 30, "ojoRisk": 27, "antracRisk": 85},
                {"year": 2025, "month": "Mar", "temperature": 19.072, "rain": 25.4, "royaRisk": 15, "brocaRisk": 20, "ojoRisk": 52, "antracRisk": 28},
                {"year": 2025, "month": "Apr", "temperature": 21.133, "rain": 50, "royaRisk": 35, "brocaRisk": 40, "ojoRisk": 16, "antracRisk": 77},
                {"year": 2025, "month": "May", "temperature": 23.538, "rain": 78.8, "royaRisk": 50, "brocaRisk": 60, "ojoRisk": 9, "antracRisk": 88},
                {"year": 2025, "month": "Jun", "temperature": 22.883, "rain": 179.8, "royaRisk": 90, "brocaRisk": 70, "ojoRisk": 77, "antracRisk": 63}
            ]
        }
    ]

    return reports

def summary_json():
    summary = {
        "royaRisk": 35, "brocaRisk": 40, "ojoRisk": 77, "antracRisk": 45
    }

    return summary