import os
from src import app
from moviepy.editor import *
from celery import Celery
from celery.signals import task_postrun
from datetime import datetime

from src.models import db, Solicitudes

celery_app = Celery('tasks', broker='redis://127.0.0.1:6379/0')

def convert_video(input_file_path, output_file_path):

    clip = VideoFileClip(input_file_path)
    clip.write_videofile(output_file_path)


@celery_app.task(name='conversor.convert')
def convert(id):
    print(id)
    # 1. Query record in database
    record = Solicitudes.query.get(id)
    # 2. Register start_processing_time and update status
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
    convert_video(full_input_path, full_output_path)
    # 6. Update status and register end_processing_time
    record.end_process_date = datetime.now()
    record.status = "available"
    db.session.commit()


@task_postrun.connect()
def close_session(*args, **kwargs):
    db.session.remove()
