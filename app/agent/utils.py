import json
import logging
import sys
from pathlib import Path
from typing import Any

LOG_FORMAT = "%(levelname)s:     %(message)s"
LOGGER = logging.getLogger("agent")
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
        LOGGER.info("Response text: %s", response_text)
        response_dict = json.loads(response_text)
    except json.JSONDecodeError as e:
        LOGGER.error(f"Failed to parse JSON response: {e}")
        return {}
    return response_dict


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # ensures consistent config across modules
    )
