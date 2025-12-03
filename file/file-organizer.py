import os
import shutil
import tkinter 


source_dir = "C:\\Users\\pinmi\\Downloads"
img_dir = "C:\\Users\\pinmi\\Downloads\\images"
video_dir = "C:\\Users\\pinmi\\Downloads\\videos"
audio_dir = "C:\\Users\\pinmi\\Downloads\\audio"
docs_dir = "C:\\Users\\pinmi\\Downloads\\docs"
zip_dir = "C:\\Users\\pinmi\\Downloads\\zip"
unity_dir = "C:\\Users\\pinmi\\Downloads\\unity"
apps_dir = "C:\\Users\\pinmi\\Downloads\\apps"
icons_dir = "C:\\Users\\pinmi\\Downloads\\icons"
code_dir = "C:\\Users\\pinmi\\Downloads\\code"

directories = [
    img_dir,
    video_dir,
    audio_dir,
    docs_dir,
    zip_dir,
    unity_dir,
    apps_dir,
    icons_dir,
    code_dir,
]
for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)

file_types = [
    ".jpg",
    ".png",
    ".jpeg",
    ".gif",
    ".mp4",
    ".mp3",
    ".pdf",
    ".zip",
    ".unitypackage",
    ".webp",
    ".exe",
    ".msi",
    ".rar",
    ".7z",
    ".svg",
    ".txt",
    ".doc",
    ".tsx",
    "ts",
    ".js",
    ".json",
    ".html",
    ".css",
    ".py",
    ".c",
    ".cs",
]

file_list = os.listdir(source_dir)

var filesMoved = 0 
for file in file_list:
    for file_type in file_types:
        if file.endswith(file_type):
            if (
                file_type == ".jpg"
                or file_type == ".png"
                or file_type == ".jpeg"
                or file_type == ".gif"
                or file_type == ".webp"
            ):
                shutil.move(os.path.join(source_dir, file), img_dir)
            elif file_type == ".mp4" or file_type == ".mp3":
                shutil.move(os.path.join(source_dir, file), video_dir)
            elif file_type == ".pdf" or file_type == ".doc" or file_type == ".txt":
                shutil.move(os.path.join(source_dir, file), docs_dir)
            elif file_type == ".zip" or file_type == ".rar" or file_type == ".7z":
                shutil.move(os.path.join(source_dir, file), zip_dir)
            elif file_type == ".unitypackage":
                shutil.move(os.path.join(source_dir, file), unity_dir)
            elif file_type == ".exe" or file_type == ".msi":
                shutil.move(os.path.join(source_dir, file), apps_dir)
            elif file_type == ".svg":
                shutil.move(os.path.join(source_dir, file), icons_dir)
            elif (
                file_type == ".js"
                or file_type == ".json"
                or file_type == ".html"
                or file_type == ".tsx"
                or file_type == ".tsx"
                or file_type == ".cs"
                or file_type == ".c"
                or file_type == ".py"
                or file_type == ".css"
                or file_type == ".ts"
            ):
                shutil.move(os.path.join(source_dir, file), code_dir)

            filesMoved += 1

            else:
                continue
            break
