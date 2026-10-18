import json
import time

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, ValidationError

load_dotenv()
client = genai.Client()

MODEL = "gemini-3.5-flash-lite"
MAX_ATTEMPTS = 3


def clean_json_text(text: str) -> str:
    """Remove ```json ... ``` fences if the model added them."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return text.strip()


def generate_validated(prompt: str, schema: type[BaseModel]) -> BaseModel:
    """Call Gemini, validate the JSON against `schema`, retry with feedback if invalid."""
    current_prompt = prompt

    for attempt in range(1, MAX_ATTEMPTS + 1):
        interaction = client.interactions.create(model=MODEL, input=current_prompt)
        raw = interaction.output_text

        try:
            data = json.loads(clean_json_text(raw))
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as error:
            print(f"  attempt {attempt} invalid: {error}")
            current_prompt = (
                prompt
                + "\n\nYour previous answer was invalid for this reason:\n"
                + str(error)
                + "\nReturn the corrected JSON object only."
            )
            time.sleep(5)

    raise ValueError(f"No valid result after {MAX_ATTEMPTS} attempts")