import hashlib
import os
from datetime import timedelta
from flask import request, current_app, send_file
from werkzeug.utils import secure_filename
from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from flask_restful import Api

from utils.utils import get_base_file_name, get_file_extension

from .models import db, Solicitudes, Usuario

class VistaSignUp(Resource):
    def post(self):
        usuario = Usuario.query.filter(
            Usuario.user == request.json["user"] or Usuario.email == request.json["email"]).first()
        if usuario is None:
            encrypted_password = hashlib.md5(
                request.json["password"].encode('utf-8')).hexdigest()
            new_user = Usuario(
                user=request.json["user"], password=encrypted_password, email=request.json["email"])
            db.session.add(new_user)
            db.session.commit()
            return {"mensaje": "usuario creado exitosamente", "id": new_user.id}
        else:
            return "El usuario ya existe", 404

class VistaLogIn(Resource):
    def post(self):
        encrypted_password = hashlib.md5(
            request.json["password"].encode('utf-8')).hexdigest()
        user = Usuario.query.filter((Usuario.user == request.json["user"] or Usuario.email == request.json["user"]) and Usuario.password == encrypted_password).first()
        if user is None:
            return "El usuario no existe", 404
        else:
            access_token = create_access_token(identity=user.id)
            return {"mensaje": "Inicio de sesión exitoso", "token": access_token}
        
class VistaSolicitud(Resource):
    @jwt_required()
    def get(self, file_id):
        if file_id is None:
            return {'message': 'Debe enviar un id de archivo para descargar'}, 400
        db_request = Solicitudes.query.filter(Solicitudes.id == file_id).first()
        destination_path = f"{db_request.output_path}/{db_request.fileName}"
        return send_file(destination_path, as_attachment=True)

    @jwt_required()    
    def post(self):
        user_id = get_jwt_identity()
        output_format = request.form['output_format']
        file = request.files['file']
        if user_id is None:
            return {'message':'Debe enviar un token valido para poder asociar la solicitud'}, 400
        if file is None:
            return {'message':'Debe enviar un archivo para convertir'}, 400
        logged_user = Usuario.query.get(user_id)
        filename = secure_filename(file.filename)
        destination_path = f"{current_app.config['UPLOAD_FOLDER']}{logged_user.user}"

        if not os.path.exists(destination_path):
            os.makedirs(destination_path)
        file.save(os.path.join(destination_path, filename))
        
        input_format = get_file_extension(f"{destination_path}/{filename}")

        new_request = Solicitudes(
            user_id=user_id,
            input_path=destination_path,
            output_path=destination_path,
            fileName=get_base_file_name(filename),
            status='uploaded',
            output_format=output_format,
            input_format=input_format
        )
        db.session.add(new_request)
        db.session.commit()
        return {'message': f'Solicitud registrada, para consultar su archivo utilice el siguiente id: ({new_request.id})'}, 200
