import json
from unittest.mock import MagicMock, patch
from PIL import Image
from claude_client import ClaudeClient, _image_to_base64


def _blank_image() -> Image.Image:
    return Image.new("RGB", (100, 80), (200, 200, 200))


def test_image_to_base64_returns_string():
    result = _image_to_base64(_blank_image())
    assert isinstance(result, str)
    assert len(result) > 0


def test_analyze_parses_response():
    expected = {
        "question": "What does PROC SORT do?",
        "answer": "Sorts a SAS dataset",
        "explanation": "PROC SORT reorders observations by one or more variables.",
    }

    mock_content = MagicMock()
    mock_content.text = json.dumps(expected)

    mock_response = MagicMock()
    mock_response.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("claude_client.anthropic.Anthropic", return_value=mock_client):
        client = ClaudeClient(model="claude-sonnet-4-6", max_tokens=1500)
        result = client.analyze(_blank_image())

    assert result["question"] == expected["question"]
    assert result["answer"] == expected["answer"]
    assert result["explanation"] == expected["explanation"]


def test_analyze_sends_image_as_base64():
    mock_content = MagicMock()
    mock_content.text = json.dumps({"question": "Q", "answer": "A", "explanation": "E"})
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("claude_client.anthropic.Anthropic", return_value=mock_client):
        client = ClaudeClient()
        client.analyze(_blank_image())

    call_kwargs = mock_client.messages.create.call_args
    messages = call_kwargs.kwargs["messages"]
    image_block = messages[0]["content"][0]
    assert image_block["type"] == "image"
    assert image_block["source"]["type"] == "base64"
    assert image_block["source"]["media_type"] == "image/png"


def test_analyze_uses_prompt_caching():
    mock_content = MagicMock()
    mock_content.text = json.dumps({"question": "Q", "answer": "A", "explanation": "E"})
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("claude_client.anthropic.Anthropic", return_value=mock_client):
        client = ClaudeClient()
        client.analyze(_blank_image())

    call_kwargs = mock_client.messages.create.call_args
    system = call_kwargs.kwargs["system"]
    assert system[0]["cache_control"] == {"type": "ephemeral"}
