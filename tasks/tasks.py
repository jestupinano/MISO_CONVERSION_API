import os
from celery import Celery
from celery.signals import task_postrun
from datetime import datetime
import subprocess

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

OUR_HOST = os.getenv("DB_HOST", "localhost")
OUR_DB = os.getenv("DB_DB", "conversiones")
OUR_PORT = os.getenv("DB_PORT", "5432")
OUR_USER = os.getenv("DB_USER", "miso")
OUR_PW = os.getenv("DB_PW", "miso")
OUR_SECRET = os.getenv("SECRET", "conversiones")
OUR_JWTSECRET = os.getenv("JWTSECRET", "conversiones")

SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(
    OUR_USER, OUR_PW, OUR_HOST, OUR_PORT, OUR_DB)

# Create Engine
engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)

# Session factory
Session = sessionmaker(bind=engine)


class Usuario(Base):
    __tablename__ = 'usuario'

    id = Column(Integer, primary_key=True)
    user = Column(String(128))
    email = Column(String(128))
    password = Column(String(128))

    # Relationship for back-reference from Solicitudes
    solicitudes = relationship("Solicitudes", back_populates="usuario")


class Solicitudes(Base):
    __tablename__ = 'solicitudes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('usuario.id'))
    input_path = Column(String(500))
    output_path = Column(String(500))
    input_format = Column(String(5))
    output_format = Column(String(5))
    fileName = Column(String(500))
    upload_date = Column(DateTime)
    start_process_date = Column(DateTime)
    end_process_date = Column(DateTime)
    status = Column(String(50))

    # Relationship for referencing Usuario
    usuario = relationship("Usuario", back_populates="solicitudes")


celery_app = Celery('tasks', broker='redis://127.0.0.1:6379/0')


@celery_app.task(name='conversor.convert')
def perform_task(id):
    # Establish a new session
    session = Session()

    try:
        # 1. Query record in database
        record = session.query(Solicitudes).get(id)

        # 2. Register start_processing_time and update status
        record.start_process_date = datetime.now()
        record.status = "in_process"
        session.commit()

        # 3. Get paths to files
        full_input_path = os.path.join(
            record.input_path, f"{record.fileName}.{record.input_format}")
        full_output_path = os.path.join(
            record.output_path, f"{record.fileName}.{record.output_format}")

        # 4. If output folder does not exist, make it
        if not os.path.exists(record.output_path):
            os.makedirs(record.output_path)

        # 5. Convert and save file
        cmd = ['ffmpeg', '-i', full_input_path, full_output_path]
        subprocess.run(cmd)

        record.end_process_date = datetime.now()
        record.status = "available"
        session.commit()

    except:
        session.rollback()  # rollback in case of errors
        raise
    finally:
        session.close()
