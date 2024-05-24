from fastapi import HTTPException, status
from typing import IO
import filetype

def validate_file_type(file: IO):
    accepted_mime_types = ["image/png", "image/jpeg", "image/jpg"]
    file_info = filetype.guess(file)
    if file_info is None:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unable to determine file type")
    detected_mime_type = file_info.mime
    if detected_mime_type not in accepted_mime_types:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file type")