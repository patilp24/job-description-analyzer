import time
from pathlib import Path

import re

from llm import generate_validated
from prompts import MATCH_PROMPT_TEMPLATE
from schemas import JobExtraction, MatchResult

RESUME_FILE = Path("samples/my_resume.txt")
OUTPUT_DIR = Path("outputs")
MATCH_DIR = Path("outputs/matches")

POINTS = {"Met": 1.0, "Partial": 0.5, "Missing": 0.0}
REQUIRED_WEIGHT = 0.7
PREFERRED_WEIGHT = 0.3


def format_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "(none listed)"


def required_years(job: JobExtraction) -> float | None:
    """Pull the number from e.g. '5 years' or '2+ years'. None if there is no number."""
    if not job.years_experience_required:
        return None
    found = re.search(r"\d+(\.\d+)?", job.years_experience_required)
    return float(found.group()) if found else None


def apply_years_check(job: JobExtraction, result: MatchResult) -> None:
    """Replace the model's judgment on years-of-experience items with fixed arithmetic."""
    needed = required_years(job)
    if needed is None:
        return
    have = result.candidate_years_experience
    if have >= needed:
        status = "Met"
    elif have >= needed / 2:
        status = "Partial"
    else:
        status = "Missing"

    for m in result.required + result.preferred:
        text = m.qualification.lower()
        if "year" in text and "experience" in text:
            m.status = status
            m.evidence = f"~{have:.1f} yrs vs {needed:g} required (calculated)"


def match_resume(job: JobExtraction, resume_text: str) -> MatchResult:
    prompt = MATCH_PROMPT_TEMPLATE.format(
        required=format_list(job.required_qualifications),
        preferred=format_list(job.preferred_qualifications),
        education=job.education_required or "(none listed)",
        resume=resume_text,
    )
    result = generate_validated(prompt, MatchResult)

    # Sanity check: did the model judge every qualification?
    if (len(result.required) != len(job.required_qualifications)
            or len(result.preferred) != len(job.preferred_qualifications)):
        print("  warning: model skipped or added qualifications")
        
    apply_years_check(job, result)
    return result


def coverage(matches: list) -> float | None:
    """Share of qualifications met (Partial counts as half). None if the list is empty."""
    if not matches:
        return None
    return sum(POINTS[m.status] for m in matches) / len(matches)


def compute_score(result: MatchResult) -> int:
    required = coverage(result.required)
    preferred = coverage(result.preferred)

    if required is not None and preferred is not None:
        score = REQUIRED_WEIGHT * required + PREFERRED_WEIGHT * preferred
    elif required is not None:
        score = required
    elif preferred is not None:
        score = preferred
    else:
        return 0
    return round(score * 100)


def missing_skills(result: MatchResult) -> list[str]:
    return [m.qualification for m in result.required + result.preferred
            if m.status == "Missing"]


def confidence(job: JobExtraction) -> str:
    """Low confidence when the posting gives too little to measure against."""
    total = len(job.required_qualifications) + len(job.preferred_qualifications)
    if not job.required_qualifications or total < 5:
        return "Low (posting lists few concrete requirements)"
    return "Normal"


def count_met(matches: list) -> str:
    met = sum(m.status == "Met" for m in matches)
    return f"{met}/{len(matches)}"


if __name__ == "__main__":
    MATCH_DIR.mkdir(parents=True, exist_ok=True)
    resume_text = RESUME_FILE.read_text(encoding="utf-8")

    for job_file in sorted(OUTPUT_DIR.glob("*.json")):
        job = JobExtraction.model_validate_json(job_file.read_text(encoding="utf-8"))
        print(f"\n{job.job_title} ({job.company or 'company not named'})")

        try:
            result = match_resume(job, resume_text)
        except ValueError as error:
            print(f"  FAILED: {error}")
            continue

        print(f"  Match score: {compute_score(result)}/100  (confidence: {confidence(job)})")
        print(f"  Required met: {count_met(result.required)}      | "    f"Preferred met: {count_met(result.preferred)}")
        print(f"  Experience: ~{result.candidate_years_experience} yrs "     f"(job asks: {job.years_experience_required or 'not stated'})")
        print(f"  Missing: {', '.join(missing_skills(result)) or 'none'}")
        print(f"  Summary: {result.summary}")

        (MATCH_DIR / job_file.name).write_text(
            result.model_dump_json(indent=2), encoding="utf-8")
        time.sleep(5)