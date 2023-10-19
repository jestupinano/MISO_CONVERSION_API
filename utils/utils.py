import os
# from moviepy.editor import *


def split_file_path(file_path):
    return os.path.splitext(file_path)


def get_file_extension(file_path):
    _, file_extension = split_file_path(file_path)
    return file_extension[1:]


def get_base_file_name(file_path):
    file_name, _ = split_file_path(file_path)
    return os.path.basename(file_name)


# def convert_video(input_file_path, output_format, output_folder):

#     valid_formats = ('mp4', 'webm', 'avi', 'mpg', 'wmv')
#     input_extension = get_file_extension(input_file_path)
#     input_base_file_name = get_base_file_name(input_file_path)

#     if input_extension in valid_formats and output_format in valid_formats and input_extension != output_format:
#         clip = VideoFileClip(input_file_path)
#         output_file_path = os.path.join(
#             output_folder, input_base_file_name + f".{output_format}")
#         clip.write_videofile(output_file_path)


# if __name__ == "__main__":
#     # Directories
#     INPUT_FOLDER = os.path.join(".", "input")
#     OUTPUT_FOLDER = os.path.join(".", "output")

#     # If output folder does not exist, make it
#     if not os.path.exists(OUTPUT_FOLDER):
#         os.makedirs(OUTPUT_FOLDER)

#     file_name = "test.mp4"
#     input_file_path = os.path.join(INPUT_FOLDER, file_name)

#     convert_video(input_file_path, 'webm', OUTPUT_FOLDER)
