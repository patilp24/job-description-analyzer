import json
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from pydantic import ValidationError

from prompts import PROMPT_TEMPLATE
from schemas import JobExtraction

load_dotenv()
client = genai.Client()

MODEL = "gemini-3.5-flash-lite"
MAX_ATTEMPTS = 3
POSTINGS_DIR = Path("samples/postings")
OUTPUT_DIR = Path("outputs")


def clean_json_text(text: str) -> str:
    """Remove ```json ... ``` fences if the model added them."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]    # drop the first line (```json)
        text = text.rsplit("```", 1)[0]  # drop the closing ```
    return text.strip()


def extract_job(posting_text: str) -> JobExtraction:
    """Send a posting to Gemini, validate the result, retry if invalid."""
    base_prompt = PROMPT_TEMPLATE.format(posting=posting_text)
    prompt = base_prompt

    for attempt in range(1, MAX_ATTEMPTS + 1):
        interaction = client.interactions.create(model=MODEL, input=prompt)
        raw = interaction.output_text

        try:
            data = json.loads(clean_json_text(raw))
            return JobExtraction.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as error:
            print(f"  attempt {attempt} invalid: {error}")
            # Tell the model exactly what was wrong, then try again
            prompt = (
                base_prompt
                + "\n\nYour previous answer was invalid for this reason:\n"
                + str(error)
                + "\nReturn the corrected JSON object only."
            )
            time.sleep(5)

    raise ValueError(f"No valid result after {MAX_ATTEMPTS} attempts")


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)

    for posting_file in sorted(POSTINGS_DIR.glob("*.txt")):
        print(f"Analyzing {posting_file.name} ...")
        try:
            job = extract_job(posting_file.read_text(encoding="utf-8"))
        except ValueError as error:
            print(f"  FAILED: {error}")
            continue

        output_file = OUTPUT_DIR / f"{posting_file.stem}.json"
        output_file.write_text(job.model_dump_json(indent=2), encoding="utf-8")
        print(f"  valid ✓ saved to {output_file}")
        time.sleep(5)

    print("Done.")