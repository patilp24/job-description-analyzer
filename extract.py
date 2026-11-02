import re
import time
from pathlib import Path

from llm import generate_validated
from prompts import PROMPT_TEMPLATE
from schemas import JobExtraction

POSTINGS_DIR = Path("samples/postings")
OUTPUT_DIR = Path("outputs")

def find_exact(term: str, text: str) -> str | None:
    """Find `term` in `text` (ignoring capitalization and spacing) and
    return it exactly as written in `text`. None if not found."""
    words = term.split()
    if not words:
        return None
    pattern = r"(?<!\w)" + r"\s+".join(re.escape(w) for w in words) + r"(?!\w)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return " ".join(match.group().split()) if match else None


def verify_keywords(keywords: list[str], posting_text: str) -> list[str]:
    """Keep only keywords that really appear in the posting, in the posting's exact wording."""
    exact = []
    for keyword in keywords:
        found = find_exact(keyword, posting_text)
        if found is None:
            print(f"  dropped keyword (not in posting): {keyword}")
        elif found.lower() not in (e.lower() for e in exact):
            exact.append(found)
    return exact

def extract_job(posting_text: str) -> JobExtraction:
    prompt = PROMPT_TEMPLATE.format(posting=posting_text)
    job = generate_validated(prompt, JobExtraction)
    job.keywords = verify_keywords(job.keywords, posting_text)
    return job


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