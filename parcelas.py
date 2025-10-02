from flask import Flask, request, jsonify

app = Flask(__name__)

parcelas = []
ubicaciones = []
parcela_id_counter = 1
ubicacion_id_counter = 1


@app.route('/parcelas', methods=['POST'])
def crear_parcela():
    global parcela_id_counter, ubicacion_id_counter

    data = request.get_json()

    ubicacion = {
        "idUbicacion": ubicacion_id_counter,
        "estado": data["ubicacion"]["estado"],
        "municipio": data["ubicacion"]["municipio"],
        "latitud": data["ubicacion"]["latitud"],
        "longitud": data["ubicacion"]["longitud"]
    }
    ubicaciones.append(ubicacion)
    ubicacion_id_counter += 1

    parcela = {
        "idParcela": parcela_id_counter,
        "nombre": data["nombre"],
        "hectareas": data["hectareas"],
        "tipo": data["tipo"],
        "ubicacion": ubicacion
    }
    parcelas.append(parcela)
    parcela_id_counter += 1

    return jsonify(parcela), 201


@app.route('/parcelas/<int:idParcela>', methods=['PUT'])
def modificar_parcela(idParcela):
    data = request.get_json()

    parcela = next((p for p in parcelas if p["idParcela"] == idParcela), None)
    if not parcela:
        return jsonify({"error": "Parcela no encontrada"}), 404

    parcela["nombre"] = data.get("nombre", parcela["nombre"])
    parcela["hectareas"] = data.get("hectareas", parcela["hectareas"])
    parcela["tipo"] = data.get("tipo", parcela["tipo"])

    if "ubicacion" in data:
        ubicacion = parcela["ubicacion"]
        ubicacion["estado"] = data["ubicacion"].get("estado", ubicacion["estado"])
        ubicacion["municipio"] = data["ubicacion"].get("municipio", ubicacion["municipio"])
        ubicacion["latitud"] = data["ubicacion"].get("latitud", ubicacion["latitud"])
        ubicacion["longitud"] = data["ubicacion"].get("longitud", ubicacion["longitud"])

    return jsonify(parcela), 200


@app.route('/parcelas', methods=['GET'])
def obtener_parcelas():
    return jsonify(parcelas), 200


@app.route('/parcelas/<int:idParcela>', methods=['GET'])
def obtener_parcela(idParcela):
    parcela = next((p for p in parcelas if p["idParcela"] == idParcela), None)
    if not parcela:
        return jsonify({"error": "Parcela no encontrada"}), 404
    return jsonify(parcela), 200


@app.route('/parcelas/<int:idParcela>', methods=['DELETE'])
def eliminar_parcela(idParcela):
    global parcelas

    parcela = next((p for p in parcelas if p["idParcela"] == idParcela), None)
    if not parcela:
        return jsonify({"error": "Parcela no encontrada"}), 404

    parcelas = [p for p in parcelas if p["idParcela"] != idParcela]

    return jsonify({"mensaje": f"Parcela con id {idParcela} eliminada correctamente"}), 200


if __name__ == '__main__':
    app.run(debug=True)
