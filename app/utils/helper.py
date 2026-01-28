import json
import logging
from pathlib import Path
from typing import Any

from utils.logger import configure_logging

configure_logging()
LOGGER = logging.getLogger("nodes")
LOGGER.setLevel(logging.INFO)


def load_prompt(filename: str) -> str:
    file_path = Path(__file__).parent.parent / "prompts" / filename
    return file_path.read_text()


def parse_json_response(response_text: str) -> dict[str, Any]:
    """Parse the response text into a dictionary."""
    response_text = response_text.strip().replace("```json", "").replace("```", "").strip()
    # small LLMs can fail to provide valid JSON and provide some text before and after the JSON
    response_text = response_text[response_text.find("{") : response_text.rfind("}") + 1]
    try:
        response_dict = json.loads(response_text)
    except json.JSONDecodeError as e:
        LOGGER.error(f"Failed to parse JSON response: {e}")
        return {"response": response_text}
    return response_dict
