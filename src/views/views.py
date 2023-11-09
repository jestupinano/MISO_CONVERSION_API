from ..models import db, Solicitudes, Usuario
from utils import get_base_file_name, get_file_extension, map_db_request
import hashlib
import json
import os
from google.cloud import storage
from datetime import datetime
from flask import request, current_app, send_file, make_response
from werkzeug.utils import secure_filename
from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from flask_restful import Api
from celery import Celery
from config import BROKER_HOST, BROKER_PORT


celery_app = Celery('tasks', broker=f'redis://{BROKER_HOST}:{BROKER_PORT}/0')
celery_app.broker_connection_retry_on_startup=True


@celery_app.task(name='conversor.convert')
def perform_task(id):
    pass

storage_client = storage.Client.from_service_account_json('cloud-configurarion.json')
bucket = storage_client.get_bucket('vid-before')

class VistaSignUp(Resource):
    def post(self):

        campos = {
            "user": request.json.get("user"),
            "email": request.json.get("email"),
            "password": request.json.get("password"),
        }

        for nombre_campo, valor in campos.items():
            if valor is None:
                return {'message': f"Campo {nombre_campo} requerido"}, 400

        user, email, password = campos.values()

        usuario_existente = Usuario.query.filter(
            Usuario.user == user or Usuario.email == email).first()
        if usuario_existente is None:
            encrypted_password = hashlib.md5(
                password.encode('utf-8')).hexdigest()
            new_user = Usuario(
                user=user, password=encrypted_password, email=email)
            db.session.add(new_user)
            db.session.commit()
            return {"mensaje": "Usuario creado exitosamente", "id": new_user.id}, 200
        else:
            return {"mensaje": "El usuario ya existe"}, 404


class VistaLogIn(Resource):
    def post(self):
        campos = {
            "user": request.json.get("user"),
            "password": request.json.get("password"),
        }

        for nombre_campo, valor in campos.items():
            if valor is None:
                return {'message': f"Campo {nombre_campo} requerido"}, 400

        user, password = campos.values()

        encrypted_password = hashlib.md5(
            password.encode('utf-8')).hexdigest()
        user = Usuario.query.filter(
            Usuario.user == user, Usuario.password == encrypted_password).first()
        if user is None:
            return {"mensaje": "Usuario o contraseña erroneos"}, 404
        else:
            access_token = create_access_token(identity=user.id)
            return {"mensaje": "Inicio de sesión exitoso", "token": access_token}


class VistaSolicitud(Resource):
    @jwt_required()
    def get(self, download_type, id_task):
        if id_task is None:
            return {'message': 'Debe enviar un id de solicitud para descargar el archivo'}, 400
        db_request = Solicitudes.query.filter(
            Solicitudes.id == id_task).first()
        user_id = get_jwt_identity()
        if db_request is None:
            return {'message': 'Solicitud no encontrada'}, 404
        if user_id != db_request.user_id:
            return {'message': 'El recurso solicitado no le pertenece'}, 404
        # Verifica que el archivo este disponible
        if db_request.status != 'available' and download_type == 'converted':
            return {'message': 'Su archivo aun no esta listo, por favor intente mas tarde'}, 400
        # Descarga el archivo (original/converted) del servidor
        if download_type == 'original':
            destination_path = f"{db_request.input_path}/{db_request.fileName}.{db_request.input_format}"
        elif download_type == 'converted':
            destination_path = f"{db_request.output_path}/{db_request.fileName}.{db_request.output_format}"
        else:
            return {'message': 'Debe escoger el origen del archivo (original/converted)'}, 400
        return send_file(destination_path, as_attachment=True)

    @jwt_required()
    def delete(self, id_task):
        if id_task is None:
            return {'message': 'Debe enviar un id de solicitud para borrar'}, 400
        db_request = Solicitudes.query.filter(
            Solicitudes.id == id_task).first()
        user_id = get_jwt_identity()
        if db_request is None:
            return {'message': 'Solicitud no encontrada'}, 404
        if user_id != db_request.user_id:
            return {'message': 'El recurso solicitado no le pertenece'}, 404
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

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        if user_id is None:
            return {'message': 'Debe enviar un token valido para poder asociar la solicitud'}, 400
        print("request: ", request)
        print("request.files: ", request.files)
        print("request.files.file: ", request.files.get('file'))
        print("request.form.output_format: ",
              request.form.get('output_format'))
        file = request.files.get('file')
        if file is None:
            return {'message': 'Debe enviar un archivo para convertir'}, 400

        output_format = request.form.get('output_format')
        if not output_format:
            return {'message': 'Debe enviar el formato de salida deseado'}, 400

        logged_user = Usuario.query.get(user_id)
        filename = secure_filename(file.filename)
        input_format = get_file_extension(filename)

        # Step 0: validate formats
        valid_formats = ('mp4', 'webm', 'avi', 'mpg', 'wmv')
        if input_format not in valid_formats:
            return {'message': 'Formato de archivo de entrada invalido'}, 400
        if output_format not in valid_formats:
            return {'message': 'Formato de archivo de salida invalido'}, 400
        if input_format == output_format:
            return {'message': 'Los formatos de archivo no pueden ser iguales'}, 400

        # Step 1: with timestamp, construct the paths
        now = datetime.now()
        current_time = now.strftime("%Y%m%d%H%M%S%f")[:-3]
        input_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], logged_user.user, 'input', str(current_time))
        output_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], logged_user.user, 'output', str(current_time))

        # Step 2: Check directory existence and save file
        current_app.logger.info(os.path.join(input_path, filename))
        cargarArchivo(file,os.path.join(input_path, filename))

        # Step 3: Create the Solicitudes entry without paths first
        new_request = Solicitudes(
            user_id=user_id,
            input_path=input_path,
            output_path=output_path,
            fileName=get_base_file_name(filename),
            upload_date=datetime.now(),
            status='uploaded',
            output_format=output_format,
            input_format=input_format
        )
        db.session.add(new_request)
        db.session.commit()

        # Proceed with the queue
        args = (new_request.id, )
        print(args)
        perform_task.apply_async(args)

        return {'message': f'Solicitud registrada, para consultar su archivo utilice el siguiente id: ({new_request.id})'}, 200
    
def cargarArchivo(file, url):
    current_app.logger.info(url)
    current_app.logger.info("Cargando video")

    blob = bucket.blob(url)

    blob.upload_from_string(
        file.read(),
        content_type=file.content_type)
    return blob.public_url

def leer_archivo(dirreccion_archivo):
    current_app.logger.info(dirreccion_archivo)
    blob = bucket.get_blob(dirreccion_archivo)
    return blob.download_as_bytes()
