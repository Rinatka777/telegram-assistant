from pathlib import Path
import pymupdf
from PIL import Image
import pytesseract


def extract_text_from_pdf(path: Path) -> str:
    doc = pymupdf.open(str(path))
    text = ""
    for page in doc:
        text += page.get_text("text")
    cleaned = " ".join(text.split())
    return cleaned

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
        raise ValueError(f"Unsupported file type: {ext}")

