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

class QualificationMatch(BaseModel):
    """How the resume matches one qualification."""
    model_config = ConfigDict(extra="forbid")

    qualification: str
    status: Literal["Met", "Partial", "Missing"]
    evidence: str | None


class MatchResult(BaseModel):
    """The full resume-vs-job comparison."""
    model_config = ConfigDict(extra="forbid")

    required: list[QualificationMatch]
    preferred: list[QualificationMatch]
    education_status: Literal["Met", "Not met", "Not required", "Unclear"]
    candidate_years_experience: float = 0.0   # filled in by code, not the model
    summary: str


class Role(BaseModel):
    """One job or internship from the resume."""
    model_config = ConfigDict(extra="forbid")

    title: str
    organization: str
    start: str = Field(pattern=r"^\d{4}-\d{2}$")              # e.g. "2020-11"
    end: str = Field(pattern=r"^(\d{4}-\d{2}|Present)$")      # e.g. "2022-06" or "Present"


class ResumeRoles(BaseModel):
    """All professional roles listed in a resume."""
    model_config = ConfigDict(extra="forbid")

    roles: list[Role]