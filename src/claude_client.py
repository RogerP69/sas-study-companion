import base64
import json
from io import BytesIO

import anthropic
from PIL import Image

_SYSTEM_PROMPT = """You are an expert clinical SAS programmer and exam tutor.
You will be shown a screenshot of a clinical SAS programming exam question.

Your job is to:
1. Identify the question being asked
2. Provide the correct answer with a clear explanation
3. If code is involved, show and explain the correct SAS code
4. Reference relevant CDISC standards (SDTM, ADaM) or SAS procedures where appropriate
5. Keep explanations educational — explain WHY, not just WHAT

Format your response as JSON with these exact keys:
- "question": what you understood the question to be
- "answer": the correct answer (concise)
- "explanation": why this is correct, with any relevant SAS/CDISC context and code examples

Respond with valid JSON only — no markdown wrapper, no extra text."""


def _image_to_base64(image: Image.Image) -> str:
    buf = BytesIO()
    image.save(buf, format="PNG")
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


class ClaudeClient:
    def __init__(self, model: str = "claude-sonnet-4-6", max_tokens: int = 1500):
        self._client = anthropic.Anthropic()
        self._model = model
        self._max_tokens = max_tokens

    def analyze(self, image: Image.Image) -> dict:
        image_data = _image_to_base64(image)
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": "Please analyze this exam question."},
                    ],
                }
            ],
        )
        return json.loads(response.content[0].text)
