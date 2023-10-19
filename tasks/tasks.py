from src.models import db, Solicitudes
import os
from src import app
from celery import Celery
from celery.signals import task_postrun
from datetime import datetime
import subprocess


celery_app = Celery('tasks', broker='redis://127.0.0.1:6379/0')


@celery_app.task(name='conversor.convert')
def dequeue_task(id):
    # 1. Query record in database
    record = Solicitudes.query.get(id)
    # 2. Rester start_processing_time and update status
    record.start_process_date = datetime.now()
    record.status = "in_process"
    db.session.commit()
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
    db.session.commit()


@task_postrun.connect()
def close_session(*args, **kwargs):
    db.session.remove()
