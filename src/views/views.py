from ..models import db, Solicitudes, Usuario
from utils import get_base_file_name, get_file_extension, map_db_request
import hashlib
import json
import os
from datetime import timedelta
from flask import request, current_app, send_file
from werkzeug.utils import secure_filename
from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from flask_restful import Api
from celery import Celery

celery_app = Celery('tasks', broker='redis://127.0.0.1:6379/0')


@celery_app.task(name='conversor.convert')
def enqueue_task(id):
    pass


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
        user = Usuario.query.filter(
            Usuario.user == request.json["user"], Usuario.password == encrypted_password).first()
        if user is None:
            return "Usuario o contraseña erroneos", 404
        else:
            access_token = create_access_token(identity=user.id)
            return {"mensaje": "Inicio de sesión exitoso", "token": access_token}


class VistaSolicitud(Resource):
    @jwt_required()
    def get(self, download_type, file_id):
        if file_id is None:
            return {'message': 'Debe enviar un id de solicitud para descargar el archivo'}, 400
        db_request = Solicitudes.query.filter(
            Solicitudes.id == file_id).first()
        if db_request is None:
            return {'message': 'Solicitud no encontrada'}, 404
        # Verifica que el archivo este disponible
        if db_request.status != 'available' and download_type == 'converted':
            return {'message': 'Su archivo aun no esta listo, por favor intente mas tarde'}, 400
        # Descarga el archivo (original/converted) del servidor
        if download_type == 'original':
            destination_path = f"{db_request.input_path}/{db_request.fileName}.{db_request.input_format}"
        elif download_type == 'converted':
            destination_path = f"{db_request.output_path}/{db_request.fileName}.{db_request.output_format}"
        else:
            return {'message': 'Debe escojer el origen del archivo (original/converted)'}, 400
        return send_file(destination_path, as_attachment=True)

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        output_format = request.form['output_format']
        file = request.files['file']
        if user_id is None:
            return {'message': 'Debe enviar un token valido para poder asociar la solicitud'}, 400
        if file is None:
            return {'message': 'Debe enviar un archivo para convertir'}, 400
        logged_user = Usuario.query.get(user_id)
        filename = secure_filename(file.filename)

        # Step 1: Create the Solicitudes entry without paths first
        new_request = Solicitudes(
            user_id=user_id,
            input_path="",  # temporary placeholder
            output_path="",  # temporary placeholder
            fileName=get_base_file_name(filename),
            status='uploaded',
            output_format=output_format,
            input_format=get_file_extension(filename)
        )
        db.session.add(new_request)
        db.session.commit()

        # Step 2: Now that we have the ID, construct the paths
        input_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], logged_user.user, 'input', str(new_request.id))
        output_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], logged_user.user, 'output', str(new_request.id))

        # Update the Solicitudes entry with the correct paths
        new_request.input_path = input_path
        new_request.output_path = output_path
        db.session.commit()

        # Step 3 and 4: Check directory existence and save file
        if not os.path.exists(input_path):
            os.makedirs(input_path)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        file.save(os.path.join(input_path, filename))

        # Proceed with the rest of your logic
        args = (new_request.id, )
        enqueue_task.apply_async(args)

        return {'message': f'Solicitud registrada, para consultar su archivo utilice el siguiente id: ({new_request.id})'}, 200

    @jwt_required()
    def delete(self, file_id):
        if file_id is None:
            return {'message': 'Debe enviar un id de solicitud para borrar'}, 400
        db_request = Solicitudes.query.filter(
            Solicitudes.id == file_id).first()
        if db_request is None:
            return {'message': 'Solicitud no encontrada'}, 404
        input_file_to_delete = f"{db_request.input_path}/{db_request.fileName}.{db_request.input_format}"
        if os.path.exists(input_file_to_delete):
            os.remove(input_file_to_delete)
        output_file_to_delete = f"{db_request.output_path}/{db_request.fileName}.{db_request.output_format}"
        if os.path.exists(output_file_to_delete):
            os.remove(output_file_to_delete)
        db.session.delete(db_request)
        db.session.commit()
        return {'message': 'Solicitud eliminada'}, 200


class VistaSolicitudes(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        db_request = Solicitudes.query.filter(
            Solicitudes.user_id == user_id).all()
        mapr_result = map(map_db_request, db_request)
        list_result = list(mapr_result)
        return list_result
