from fastapi import FastAPI, File, UploadFile
import os

app = FastAPI()

UPLOAD_DIRECTORY = "./uploads"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

@app.get("/")
async def root():
    return {"message" : "Hello World"}

@app.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
        with open(file_path, "wb") as buffer:
            contents = await file.read()
            buffer.write(contents)

            return {"message" : f"Successfully uploaded {file.filename}"}
    except Exception as e:
        return {"error" : str(e)}