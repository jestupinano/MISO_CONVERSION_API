import os
from datetime import timedelta
from flask import request, current_app, send_file
from werkzeug.utils import secure_filename
from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from flask_restful import Api

from .models import db, Solicitudes

class VistaSignUp(Resource):

    def post(self):
        usuario = Usuario.query.filter(
            Usuario.usuario == request.json["usuario"]).first()
        if usuario is None:
            contrasena_encriptada = hashlib.md5(
                request.json["contrasena"].encode('utf-8')).hexdigest()
            nuevo_usuario = Administrador(
                usuario=request.json["usuario"], contrasena=contrasena_encriptada)
            db.session.add(nuevo_usuario)
            db.session.commit()
            token_de_acceso = create_access_token(identity=nuevo_usuario.id)
            return {"mensaje": "usuario creado exitosamente", "id": nuevo_usuario.id}
        else:
            return "El usuario ya existe", 404

    def put(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        usuario.contrasena = request.json.get("contrasena", usuario.contrasena)
        db.session.commit()
        return usuario_schema.dump(usuario)

    def delete(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        db.session.delete(usuario)
        db.session.commit()
        return '', 204

class VistaSolicitud(Resource):
    def get(self, file_id):
        if file_id is None:
            return {'message': 'Debe enviar un id de archivo para descargar'}, 400
        db_request = Solicitudes.query.filter(Solicitudes.id == file_id).first()
        destination_path = f"{db_request.output_path}/{db_request.fileName}"
        return send_file(destination_path, as_attachment=True)
        
    def post(self):
        usuario = request.form['user']
        file = request.files['file']
        if usuario is None:
            return {'message':'Debe enviar un usuario al cual asociar la solicitud'}, 400
        if file is None:
            return {'message':'Debe enviar un archivo para convertir'}, 400
        
        filename = secure_filename(file.filename)
        destination_path = f"{current_app.config['UPLOAD_FOLDER']}{usuario}"
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)
        file.save(os.path.join(destination_path, filename))

        new_request = Solicitudes(
            user=usuario,
            input_path=destination_path,
            output_path=destination_path,
            fileName=filename,
            status='sendToServer'
        )
        db.session.add(new_request)
        db.session.commit()
        return {'message': f'Solicitud registrada, para consultar su archivo utilice el siguiente id: ({new_request.id})'}, 200
