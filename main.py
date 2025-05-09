from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
import easyocr
import base64
from PIL import Image
from io import BytesIO

# Inisialisasi OCR reader baca english dan indo
reader = easyocr.Reader(['en', 'id'])

app = FastAPI()

# Request ocr base64 text
class OCRText(BaseModel):
    fileBase64:str

@app.post("/ocr-from-file")
async def ocr_image_from_file(file: UploadFile = File(...)):
    try:
        # Baca file gambar yang diupload
        image_bytes = await file.read()
        image = Image.open(BytesIO(image_bytes))

        # Jalanin OCR pakai EasyOCR
        result = reader.readtext(image, detail=0)  # detail=0 untuk hanya mendapatkan teks
        text = " ".join(result)

        return {"raw_text": text}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

@app.post("/ocr")
async def ocr_image(request: OCRText):
    base64_str = request.fileBase64
    # remove unnecessary char
    if base64_str.startswith("data:image"):
        base64_str = base64_str.split(",")[1]

    # Decode base64 ke bytes
    try:
        image_bytes = base64.b64decode(base64_str)
        image = Image.open(BytesIO(image_bytes))
    except Exception as e:
        return {"error": str(e)}

    # Run OCR menggunakan EasyOCR (detail 0 artinya cuma ambil text aja)
    result = reader.readtext(image, detail=0)
    text = " ".join(result)

    return {"raw_text": text}