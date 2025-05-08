from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import easyocr
import base64
from PIL import Image
from io import BytesIO

# Inisialisasi OCR reader baca english dan indo
reader = easyocr.Reader(['en', 'id'])

# siapin open ai key
load_dotenv()
client = OpenAI(api_key="OPEN_AI_KEY")
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


# request untuk formating ocr text
class OCRResult(BaseModel):
    raw_text:str


@app.post("/format-bill")
async def formatBill(data: OCRResult):
    print(f"Client API Key: {client.api_key}")

    prompt = f"""
            Berikut adalah hasil dari OCR struk pembelian
            {data.raw_text}
            Tolong ekstrak data ini dalam format JSON seperti berikut:
            
            {{
                "totalAmount" : "",
                "subTotal" : "",
                "discount" : "",
                "tax" : "",
                "serviceFee" : "",
                "items" : [
                    {{
                        "name" : "",
                        "quantity" : "",
                        "price" : "",
                        "subItems" : [
                            {{
                                "name" : "",
                                "quantity" : "",
                                "price" : ""
                            }}
                        ]
                    }}
                ]
            }}
            """

    try:
        # kirim propmt ke gpt
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return {"result": client.api_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
