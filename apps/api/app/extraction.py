import fitz
from PIL import Image
import pytesseract
from pathlib import Path

def extract_text_from_pdf(path: Path) -> str:
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_image(path: Path) -> str:
    img = Image.open(path)
    gray_img = img.convert("L")
    text = pytesseract.image_to_string(gray_img)
    clean_text = text.replace("\x0c", "").strip()
    return clean_text

def extract_text_generic(path: Path) -> str:
    ext = path.suffix.lower()

    if ext in [".png", ".jpg", ".jpeg", ".webp"]:
        return extract_text_from_image(path)
    elif ext == ".pdf":
        return extract_text_from_pdf(path)
    else:
        raise ValueError(f"Unsupported file type:{ext}")

