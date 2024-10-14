import os
import cv2 
import uuid

import pytesseract

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

@app.get("/extract_text")
async def extract_text(filename: str):
    image_path = os.path.join(UPLOAD_DIRECTORY, filename)
    image = read_image(image_path)

    gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    thresh = cv2.adaptiveThreshold(edges, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Filter contours
    min_area = 100
    max_area = 5000  # Maximum area for text regions
    aspect_ratio_min = 0.5  # Minimum aspect ratio (width / height)
    contour_count_threshold = 5
    
    filtered_contours = []
    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        
        # Check area and aspect ratio
        if min_area < area < max_area and w/h > aspect_ratio_min:
            # Calculate aspect ratio
            aspect_ratio = float(w) / h
            
            # Check contour count
            contour_count = len(cv2.approxPolyDP(contour, 3.0, True))
            if contour_count >= contour_count_threshold:
                filtered_contours.append((contour, area, aspect_ratio))
    
    # Draw bounding rectangles around detected text
    image_copy = image.copy()
    for contour, _, _ in filtered_contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(image_copy, (x, y), (x+w, y+h), (0, 255, 0), 2)

    # Perform OCR on the entire image
    text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')

    os.remove(os.path.join(UPLOAD_DIRECTORY, filename))

    return {"text" : text}

@app.get("/detect_faces")
async def detect_faces(filename: str):
    image_path = os.path.join(UPLOAD_DIRECTORY, filename)
    image = read_image(image_path)

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    face_classifier = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    face = face_classifier.detectMultiScale(
        gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
    )

    for (x, y, w, h) in face:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 4)

    detected_faces_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    detected_faces_image_path  = os.path.join(PROCESSED_DIRECTORY, filename)
    cv2.imwrite(detected_faces_image_path , detected_faces_image)

    return {"Message" : "Success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)