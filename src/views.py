import os
from datetime import timedelta
from flask import request, current_app, send_file
from werkzeug.utils import secure_filename
from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from flask_restful import Api

from .models import db, Solicitudes

class VistaSolicitud(Resource):
    def get(self, file_id):
        if file_id is None:
            return {'message': 'Debe enviar un id de archivo para descargar'}, 400
        db_request = Solicitudes.query.filter(Solicitudes.id == file_id).first()
        directorio_destino = f"{db_request.output_path}/{db_request.fileName}"
        return send_file(directorio_destino, as_attachment=True)
        
    def post(self):
        usuario = request.form['user']
        archivo = request.files['file']
        if usuario is None:
            return {'message':'Debe enviar un usuario al cual asociar la solicitud'}, 400
        if archivo is None:
            return {'message':'Debe enviar un archivo para convertir'}, 400
        
        filename = secure_filename(archivo.filename)
        directorio_destino = f"{current_app.config['UPLOAD_FOLDER']}{usuario}"
        if not os.path.exists(directorio_destino):
            os.makedirs(directorio_destino)
        archivo.save(os.path.join(directorio_destino, filename))

        new_request = Solicitudes(
            user=usuario,
            input_path=directorio_destino,
            output_path=directorio_destino,
            fileName=filename,
            status='sendToServer'
        )
        db.session.add(new_request)
        db.session.commit()
        return {'message': f'Solicitud registrada, para consultar su archivo utilice el siguiente id: ({new_request.id})'}, 200
