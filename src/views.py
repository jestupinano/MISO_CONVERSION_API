from datetime import timedelta
from flask import request, current_app, send_from_directory
from werkzeug.utils import secure_filename
from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from flask_restful import Api

from .models import db, Solicitudes

class VistaSolicitud(Resource):
    def post(self):
        request.get_json(force=True)
        usuario = request.json['usuario']
        if usuario is None:
            return {'message':'Debe enviar un usuario al cual asociar la solicitud'}, 400
        db.session.add(Solicitudes(
            user=usuario,
            input_path='test',
            output_path='test',
            status='test'
        ))
        db.session.commit()
        return {'message':'Solicitud registrada'}, 200
