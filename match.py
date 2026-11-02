from datetime import date
from functools import lru_cache
from extract import find_exact

import time
from pathlib import Path

import re

from llm import generate_validated
from prompts import MATCH_PROMPT_TEMPLATE, RESUME_ROLES_PROMPT
from schemas import JobExtraction, MatchResult, ResumeRoles


RESUME_FILE = Path("samples/my_resume.txt")
OUTPUT_DIR = Path("outputs")
MATCH_DIR = Path("outputs/matches")

POINTS = {"Met": 1.0, "Partial": 0.5, "Missing": 0.0}
REQUIRED_WEIGHT = 0.7
PREFERRED_WEIGHT = 0.3


def format_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "(none listed)"

def month_number(value: str) -> int:
    """Turn '2020-11' into a single month count. 'Present' means this month."""
    if value == "Present":
        today = date.today()
        return today.year * 12 + today.month
    year, month = value.split("-")
    return int(year) * 12 + int(month)


@lru_cache(maxsize=16)
def get_candidate_years(resume_text: str) -> float:
    """Ask the model for the dated roles, then calculate total experience in code."""
    prompt = RESUME_ROLES_PROMPT.format(resume=resume_text)
    resume = generate_validated(prompt, ResumeRoles)

    # Turn each role into a (start, end) pair of month numbers, oldest first
    periods = sorted((month_number(r.start), month_number(r.end)) for r in resume.roles)

    # Merge overlapping periods so two jobs at the same time aren't counted twice
    merged = []
    for start, end in periods:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    total_months = sum(end - start for start, end in merged)
    for r in resume.roles:
        print(f"  role: {r.title} @ {r.organization}: {r.start} to {r.end}")
    print(f"  total experience: {total_months} months")
    return round(total_months / 12, 1)

def normalize(text: str) -> str:
    """Keep only lowercase letters and digits, so spacing/punctuation differences don't matter."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def verify_evidence(result: MatchResult, resume_text: str) -> int:
    """Check each evidence quote really appears in the resume. Returns how many failed."""
    resume_normalized = normalize(resume_text)
    unverified = 0

    for m in result.required + result.preferred:
        if m.status == "Missing" or not m.evidence:
            continue
        if normalize(m.evidence) not in resume_normalized:
            unverified += 1
            m.evidence = f"{m.evidence} (unverified)"
            if m.status == "Met":
                m.status = "Partial"

    return unverified

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
        if m.general_experience:
            m.status = status
            m.evidence = f"~{have:.1f} yrs vs {needed:g} required (calculated)"


def match_resume(job: JobExtraction, resume_text: str) -> MatchResult:
    candidate_years = get_candidate_years(resume_text)

    prompt = MATCH_PROMPT_TEMPLATE.format(
        required=format_list(job.required_qualifications),
        preferred=format_list(job.preferred_qualifications),
        education=job.education_required or "(none listed)",
        years=candidate_years,
        resume=resume_text,
    )
    result = generate_validated(prompt, MatchResult)
    result.candidate_years_experience = candidate_years

    if (len(result.required) != len(job.required_qualifications)
            or len(result.preferred) != len(job.preferred_qualifications)):
        print("  warning: model skipped or added qualifications")

    unverified = verify_evidence(result, resume_text)
    if unverified:
        print(f"  {unverified} evidence quote(s) could not be verified")
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

def keyword_coverage(job: JobExtraction, resume_text: str) -> tuple[list[str], list[str]]:
    """Split the posting's keywords into those found exactly in the resume and those missing."""
    present, missing = [], []
    for keyword in job.keywords:
        (present if find_exact(keyword, resume_text) else missing).append(keyword)
    return present, missing

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