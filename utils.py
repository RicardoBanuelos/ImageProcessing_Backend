from fastapi import HTTPException, status
from typing import IO
import filetype

import cv2
import base64

def validate_file_type(file: IO):
    accepted_mime_types = ["image/png", "image/jpeg", "image/jpg"]
    file_info = filetype.guess(file)
    if file_info is None:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unable to determine file type")
    detected_mime_type = file_info.mime
    if detected_mime_type not in accepted_mime_types:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file type")
    
def read_image(image_path: str):
    image = cv2.imread(cv2.samples.findFile(image_path))

    if(image is None):
        return HTTPException(status_code=500, detail="Failed reading image.")
    
    return image

def encodeToBase64(image_path: str):
    with open(image_path , 'rb') as image_file:
        img_data = image_file.read()

    return base64.b64encode(img_data).decode('utf-8')