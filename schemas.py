from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class JobExtraction(BaseModel):
    """The exact shape every job analysis must have."""

    # Reject any key that isn't listed below (e.g., jd5's "early-career")
    model_config = ConfigDict(extra="forbid")

    job_title: str
    company: str | None
    seniority: Literal["Entry", "Early-career", "Mid", "Senior", "Unclear"]
    years_experience_required: str | None
    salary: str | None
    work_model: Literal["Remote", "Hybrid", "On-site"] | None
    education_required: str | None
    education_preferred: str | None
    required_qualifications: list[str] = Field(max_length=8)
    preferred_qualifications: list[str] = Field(max_length=8)
    red_flags: list[str]
    sponsorship: Literal["Offered", "Not offered", "Not mentioned"]