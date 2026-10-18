import time
from pathlib import Path

from llm import generate_validated
from prompts import PROMPT_TEMPLATE
from schemas import JobExtraction

POSTINGS_DIR = Path("samples/postings")
OUTPUT_DIR = Path("outputs")


def extract_job(posting_text: str) -> JobExtraction:
    prompt = PROMPT_TEMPLATE.format(posting=posting_text)
    return generate_validated(prompt, JobExtraction)


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