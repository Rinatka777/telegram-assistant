import pytest
from pathlib import Path
from pytest_mock import mocker
from apps.api.app.extraction import extract_text_generic

def test_extract_text_unsupported_file():
    bad_path = Path("test_file.unknown_extension")
    with pytest.raises(ValueError) as excinfo:
        extract_text_generic(bad_path)
    assert (f"Unsupported file type") in str(excinfo.value)

def test_extract_text_from_pdf(mocker):
    mocker.patch("apps.api.app.extraction.extract_text_from_pdf", return_value="Fake PDF Content")
    fake_path = Path("document.pdf")
    result = extract_text_generic(fake_path)
    assert result == "Fake PDF Content"

def test_extract_text_image_logic(mocker):
    mocker.patch("apps.api.app.extraction.extract_text_from_image", return_value="Fake Image Text")
    fake_path = Path("photo.jpg")
    result = extract_text_generic(fake_path)
    assert result == "Fake Image Text"

def test_extract_text_docx(mocker):
    mocker.patch("apps.api.app.extraction.extract_text_from_docx", return_value="Fake Docx Text")
    fake_path = Path("document.docx")
    result = extract_text_generic(fake_path)
    assert result == "Fake Docx Text"


