import json
from pathlib import Path
from typing import Any


def load_prompt(filename: str) -> str:
    file_path = Path(__file__).parent.parent / "prompts" / filename
    return file_path.read_text()


def parse_json_response(response_text: str) -> dict[str, Any]:
    """Parse the response text into a dictionary."""
    response_text = response_text.strip().removeprefix("```json").removesuffix("```").strip()
    response_dict = json.loads(response_text)
    return response_dict
