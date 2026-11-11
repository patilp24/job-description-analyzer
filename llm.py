import json
import time

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, ValidationError

load_dotenv()
client = genai.Client()

MODEL = "gemini-3.5-flash-lite"

MAX_ATTEMPTS = 3


class LLMError(ValueError):
    """The model couldn't produce a valid answer. The message is safe to show users."""


def clean_json_text(text: str) -> str:
    """Remove ```json ... ``` fences if the model added them."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return text.strip()


def call_model(prompt: str) -> str:
    """Call Gemini, waiting and retrying on rate limits and temporary failures."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            interaction = client.interactions.create(model=MODEL, input=prompt)
            return interaction.output_text
        except Exception as error:
            message = str(error).lower()
            print(f"  API error (attempt {attempt}): {error}")

            # Problems that waiting won't fix: stop right away
            if "api key" in message or "401" in message or "403" in message:
                raise LLMError("The app's API key isn't working. Please contact the owner.") from error
            if "not found" in message or "404" in message:
                raise LLMError("The AI model is unavailable. Please contact the owner.") from error

            # Rate limit: wait longer each time
            if "429" in message or "quota" in message or "too_many_requests" in message:
                if attempt < MAX_ATTEMPTS:
                    time.sleep(15 * attempt)
                    continue
                raise LLMError("The free usage limit was reached. Please wait a minute and try again.") from error

            # Anything else (network, server hiccup): short wait, then retry
            if attempt < MAX_ATTEMPTS:
                time.sleep(5)
                continue
            raise LLMError("The AI service isn't responding right now. Please try again shortly.") from error


def generate_validated(prompt: str, schema: type[BaseModel]) -> BaseModel:
    """Call Gemini, validate the JSON against `schema`, retry with feedback if invalid."""
    current_prompt = prompt

    for attempt in range(1, MAX_ATTEMPTS + 1):
        raw = call_model(current_prompt)

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

    raise LLMError("The AI gave an unusable answer several times. Please try again.")