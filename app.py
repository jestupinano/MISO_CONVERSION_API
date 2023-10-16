from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from flask_jwt_extended import JWTManager
from datetime import timedelta
from src.models import db
from src.views import VistaSolicitud

app = Flask(__name__)
app.config.from_pyfile('config.py')

app_context = app.app_context()
app_context.push()

db.init_app(app)
db.create_all()

cors = CORS(app)

api = Api(app)
api.add_resource(VistaSolicitud, '/convertir/')

jwt = JWTManager(app)
