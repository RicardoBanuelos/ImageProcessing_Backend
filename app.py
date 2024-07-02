import os
import cv2 
import uuid
import base64

from utils import validate_file_type, read_image, encodeToBase64

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import uvicorn

UPLOAD_DIRECTORY = "./uploads"
PROCESSED_DIRECTORY = "./processed_images"

app = FastAPI()

# Add CORSMiddleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

os.makedirs(PROCESSED_DIRECTORY, exist_ok=True)
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

@app.get("/")
async def root():
    return {"message" : "Hello World"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
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
        return HTTPException(status_code=500, detail=e)
    
@app.get("/resize")
async def resize(width: str, height: str, filename: str):

    if(not width.isdigit() or not height.isdigit()):
        return HTTPException(status_code=400, detail="Invalid dimensions.")    
    
    new_width = int(width)
    new_height = int(height)

    if(new_width == 0 or new_height == 0):
        return HTTPException(status_code=400, detail="Invalid dimensions.")

    image_path = os.path.join(UPLOAD_DIRECTORY, filename)
    image = read_image(image_path)

    resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

    temp_resized_image_path  = os.path.join(PROCESSED_DIRECTORY, filename)
    cv2.imwrite(temp_resized_image_path , resized_image)

    encoded_string = encodeToBase64(temp_resized_image_path)

    os.remove(temp_resized_image_path)
    os.remove(os.path.join(UPLOAD_DIRECTORY, filename))
    
    return {"image" : "data:image/[type];base64," + encoded_string}

@app.get("/blur")
async def blur(kernel_width: str, kernel_height: str, filename: str):
    if(not kernel_width.isdigit() or not kernel_height.isdigit()):
        return HTTPException(status_code=400, detail="Invalid dimensions.")    
    
    k_width = int(kernel_width)
    k_height = int(kernel_height)

    image_path = os.path.join(UPLOAD_DIRECTORY, filename)
    image = read_image(image_path)

    blurred_image = cv2.blur(image, (k_width, k_height))
    temp_blurred_image_path  = os.path.join(PROCESSED_DIRECTORY, filename)
    cv2.imwrite(temp_blurred_image_path , blurred_image)

    encoded_string = encodeToBase64(temp_blurred_image_path)

    os.remove(temp_blurred_image_path)
    os.remove(os.path.join(UPLOAD_DIRECTORY, filename))

    return {"image" : "data:image/[type];base64," + encoded_string}

@app.get("/gaussian_blur")
async def gaussian_blur(kernel_width: str, kernel_height: str, sigmaX: str, filename: str):
    if(not kernel_width.isdigit() or not kernel_height.isdigit() or not sigmaX.isdigit()):
        return HTTPException(status_code=400, detail="Invalid dimensions.")    
    
    k_width = int(kernel_width)
    k_height = int(kernel_height)
    sigma = int(sigmaX)

    image_path = os.path.join(UPLOAD_DIRECTORY, filename)
    image = read_image(image_path)

    blurred_image = cv2.GaussianBlur(image, (k_width, k_height), sigma)
    temp_blurred_image_path  = os.path.join(PROCESSED_DIRECTORY, filename)
    cv2.imwrite(temp_blurred_image_path , blurred_image)

    encoded_string = encodeToBase64(temp_blurred_image_path)

    os.remove(temp_blurred_image_path)
    os.remove(os.path.join(UPLOAD_DIRECTORY, filename))

    return {"image" : "data:image/[type];base64," + encoded_string}

@app.get("/median_blur")
async def median_blur(percentage: str, filename: str):
    if(not percentage.isdigit()):
        return HTTPException(status_code=400, detail="Invalid dimensions.")    
    
    p = int(percentage)

    image_path = os.path.join(UPLOAD_DIRECTORY, filename)
    image = read_image(image_path)

    blurred_image = cv2.medianBlur(image, p)
    temp_blurred_image_path  = os.path.join(PROCESSED_DIRECTORY, filename)
    cv2.imwrite(temp_blurred_image_path , blurred_image)

    encoded_string = encodeToBase64(temp_blurred_image_path)

    os.remove(temp_blurred_image_path)
    os.remove(os.path.join(UPLOAD_DIRECTORY, filename))

    return {"image" : "data:image/[type];base64," + encoded_string}

@app.get("/grayscale")
async def grayscale_image(filename: str):
    image_path = os.path.join(UPLOAD_DIRECTORY, filename)
    image = read_image(image_path)

    grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    temp_greyscale_image_path  = os.path.join(PROCESSED_DIRECTORY, filename)
    cv2.imwrite(temp_greyscale_image_path , grayscale_image)

    encoded_string = encodeToBase64(temp_greyscale_image_path)

    os.remove(temp_greyscale_image_path)
    os.remove(os.path.join(UPLOAD_DIRECTORY, filename))

    return {"image" : "data:image/[type];base64," + encoded_string}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)