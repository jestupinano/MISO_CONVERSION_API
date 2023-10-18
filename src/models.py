import enum
from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields, Schema
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

db = SQLAlchemy()

class Solicitudes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    input_path = db.Column(db.String(500))
    output_path = db.Column(db.String(500))
    input_format = db.Column(db.String(5))
    output_format = db.Column(db.String(5))
    fileName = db.Column(db.String(500))
    upload_date = db.Column(db.DateTime)
    start_process_date = db.Column(db.DateTime)
    end_process_date = db.Column(db.DateTime)
    status = db.Column(db.String(50))

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(128))
    email = db.Column(db.String(128))

class SolicitudesSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Solicitudes
        load_instance = True

    id = fields.String()
