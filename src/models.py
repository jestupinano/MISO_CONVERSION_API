import enum
from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields, Schema
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

db = SQLAlchemy()

class Solicitudes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(128))
    input_path = db.Column(db.String(500))
    output_path = db.Column(db.String(500))
    status = db.Column(db.String(50))

class SolicitudesSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Solicitudes
        load_instance = True

    id = fields.String()
