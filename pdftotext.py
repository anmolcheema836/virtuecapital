import os
from pdf2image import convert_from_path
import pytesseract

# Set tesseract path (change if installed elsewhere)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def pdf_to_text_ocr(pdf_path):
    txt_file = os.path.splitext(pdf_path)[0] + ".txt"

    images = convert_from_path(pdf_path)
    all_text = ""

    for i, img in enumerate(images):
        print(f"OCR on page {i+1}...")
        text = pytesseract.image_to_string(img, lang="eng")
        all_text += text + "\n\n"

    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(all_text)

    print(f"✔ OCR text extracted → {txt_file}")

if __name__ == "__main__":
    pdf_to_text_ocr("kvs.pdf")
