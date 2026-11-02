import cv2
import numpy as np
import easyocr
import os

reader = easyocr.Reader(['en'], gpu=False)

def process_and_extract_text(image_path: str) -> dict:
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Could not read image file.")

        height, width = img.shape[:2]
        if width > 1000:
            scale = 1000 / width
            img = cv2.resize(img, (int(width * scale), int(height * scale)))

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        denoised = cv2.fastNlMeansDenoising(gray, h=15)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        processed_dir = "uploads/processed"
        os.makedirs(processed_dir, exist_ok=True)
        processed_path = os.path.join(processed_dir, f"proc_{os.path.basename(image_path)}")
        cv2.imwrite(processed_path, enhanced)

        ocr_results = reader.readtext(processed_path, detail=0)
        
        extracted_text = "\n".join(ocr_results)

        return {
            "status": "success",
            "extracted_text": extracted_text,
            "raw_lines": ocr_results
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }