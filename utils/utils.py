import os
from google.cloud import storage


def split_file_path(file_path):
    return os.path.splitext(file_path)


def get_file_extension(file_path):
    _, file_extension = split_file_path(file_path)
    return file_extension[1:]


def get_base_file_name(file_path):
    file_name, _ = split_file_path(file_path)
    return os.path.basename(file_name)


def map_db_request(db_request):
    return {'task_id': db_request.id, 'status': db_request.status, 'fileName': db_request.fileName, 'original_extension': db_request.input_format, 'target_extension': db_request.output_format}


def get_blob_name_from_gs_uri(gs_uri):
    if gs_uri.startswith('gs://'):
        parts = gs_uri.split('/', 3)
        if len(parts) > 3:
            return parts[3]
    return None
