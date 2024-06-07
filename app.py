import os
import cv2 
import uuid
import base64

from utils import validate_file_type

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import uvicorn

UPLOAD_DIRECTORY = "./uploads"
RESIZED_DIRECTORY = "./resized_images"

app = FastAPI()

# Add CORSMiddleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

@app.get("/")
async def root():
    return {"message" : "Hello World"}

@app.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    validate_file_type(file.file)
    try:
        _, file_extension = os.path.splitext(file.filename)
        unique_name = uuid.uuid4()

        file.filename = str(unique_name) + file_extension

        file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
        with open(file_path, "wb") as buffer:
            contents = await file.read()
            buffer.write(contents)

        return {"unique_name" : file.filename}
    
    except Exception as e:
        return {"error" : str(e)}
    
@app.get("/resize_image")
async def resize_image(width: str, height: str, filename: str):

    if(not width.isdigit() or not height.isdigit()):
        return {"error" : "invalid width or height"}    
    
    new_width = int(width)
    new_height = int(height)

    if(new_width == 0 or new_height == 0):
        return {"error" : "invalid dimensions"}

    image_path = os.path.join(UPLOAD_DIRECTORY, filename)
    image = cv2.imread(cv2.samples.findFile(image_path))

    if(image is None):
        return {"error" : "failed to open image for resizing"}

    resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

    temp_resized_image_path  = os.path.join(RESIZED_DIRECTORY, filename)
    cv2.imwrite(temp_resized_image_path , resized_image)

    with open(temp_resized_image_path , 'rb') as image_file:
        img_data = image_file.read()

    encoded_string = base64.b64encode(img_data).decode('utf-8')

    os.remove(temp_resized_image_path)
    os.remove(os.path.join(UPLOAD_DIRECTORY, filename))
    
    return {"image" : "data:image/[type];base64," + encoded_string}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)