from pydantic import ValidationError
from schemas import JobExtraction

good = {
    "job_title": "AI Engineer", "company": "Hertz", "seniority": "Early-career",
    "years_experience_required": "2+ years", "salary": "Starts at $90k",
    "work_model": None, "education_required": "Bachelor's", "education_preferred": None,
    "required_qualifications": ["Python", "SQL"], "preferred_qualifications": ["Spark"],
    "red_flags": [], "sponsorship": "Not mentioned",
}

# 1. A valid example should pass
print(JobExtraction.model_validate(good))

# 2. jd5's real mistake: an extra key
bad = {**good, "early-career": None}
try:
    JobExtraction.model_validate(bad)
except ValidationError as e:
    print("\nCaught the extra key:\n", e)

# 3. A seniority value that isn't allowed
bad2 = {**good, "seniority": "Mid-level"}
try:
    JobExtraction.model_validate(bad2)
except ValidationError as e:
    print("\nCaught the bad seniority:\n", e)