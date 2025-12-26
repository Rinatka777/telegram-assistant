import pytest
from pytest_mock import mocker
from apps.api.app.ai_service import summarize_text


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