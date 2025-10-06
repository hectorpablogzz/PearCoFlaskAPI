from flask import jsonify

def caficultores_json():
    caficultores = [
    {
        "name": "Juan",
        "lastname": "Pérez",
        "birthDate": "1985-06-15T00:00:00Z",
        "gender": "M",
        "telephone": "5551234567",
        "email": "juan.perez@example.com",
        "address": "Calle Reforma 123, Ciudad de México"
    },
    {
        "name": "María",
        "lastname": "Gómez",
        "birthDate": "1992-09-28T00:00:00Z",
        "gender": "F",
        "telephone": "5549876543",
        "email": "maria.gomez@example.com",
        "address": "Av. Juárez 45, Puebla"
    },
    {
        "name": "Alex",
        "lastname": "Ramírez",
        "birthDate": "2000-03-10T00:00:00Z",
        "gender": "X",
        "telephone": "5587654321",
        "email": "alex.ramirez@example.com",
        "address": "Boulevard Hidalgo 987, Guadalajara"
    }
    ]
    return caficultores