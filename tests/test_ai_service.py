import pytest
from pytest_mock import mocker
from apps.api.app.ai_service import summarize_text
from apps.api.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_summarize_text_success(mocker):
    mock_response = mocker.Mock()
    mock_response.choices = [
        mocker.Mock(message=mocker.Mock(content="Concise summary: Bought milk."))
    ]

    mocker.patch("apps.api.app.ai_service.client.chat.completions.create", return_value=mock_response)

    result = summarize_text("Long text about buying milk...")

    assert result == "Concise summary: Bought milk."


def test_summarize_text_api_failure(mocker):
    mocker.patch(
        "apps.api.app.ai_service.client.chat.completions.create",
        side_effect=Exception("API Timeout")
    )


    result = summarize_text("Some text")

    assert result == "Summary unavailable."


def test_summarize_empty_text():
    result = summarize_text("")
    assert result == "No text found."

def test_chat_endpoint_happy_path(mocker):
    mock_note1 = mocker.Mock(full_text="Milk cost 5$")
    mock_note2 = mocker.Mock(full_text="Bread cost 2$")
    mocker.patch("apps.api.app.main.crud.search_notes", return_value=[mock_note1, mock_note2])
    mocker.patch("apps.api.app.main.ai_service.answer_user_question", return_value="You spent 7 dollars.")
    app.dependency_overrides = {}
    response = client.post("/chat", json={"user_id": 1, "question": "How much did I spend?"})
    assert response.status_code == 200
    assert response.json() == "You spent 7 dollars."


def test_chat_endpoint_no_notes_found(mocker):
    mocker.patch("apps.api.app.main.crud.search_notes", return_value=[])
    ai_spy = mocker.patch("apps.api.app.main.ai_service.answer_user_question")
    response = client.post("/chat", json={"user_id": 1, "question": "Where are my keys?"})
    assert response.status_code == 200
    assert response.json() == "I couldn't find any notes matching your question."
    ai_spy.assert_not_called()