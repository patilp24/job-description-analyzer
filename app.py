import gradio as gr
from llm import LLMError

from extract import extract_job
from match import (match_resume, compute_score, missing_skills, confidence,
                   count_met, keyword_coverage)
from schemas import JobExtraction, MatchResult

STATUS_ICON = {"Met": "✅", "Partial": "🟡", "Missing": "❌"}


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "_None listed_"


def format_job(job: JobExtraction) -> str:
    return f"""## {job.job_title}
**Company:** {job.company or "Not named"}  
**Seniority:** {job.seniority} · **Experience:** {job.years_experience_required or "Not stated"}  
**Salary:** {job.salary or "Not listed"}  
**Work model:** {job.work_model or "Not stated"} · **Sponsorship:** {job.sponsorship}  
**Education:** {job.education_required or "Not stated"}{f" (preferred: {job.education_preferred})" if job.education_preferred else ""}

### Required
{bullet_list(job.required_qualifications)}

### 🔑 Exact keywords from the posting
{" · ".join(f"`{k}`" for k in job.keywords) or "_None found_"}

### Preferred
{bullet_list(job.preferred_qualifications)}

### 🚩 Red flags
{bullet_list(job.red_flags)}
"""

def table_cell(text: str) -> str:
    """Make text safe for one Markdown table cell (no column separators or line breaks)."""
    return text.replace("|", "/").replace("\n", " ").strip()

def format_match(job: JobExtraction, result: MatchResult, resume_text: str) -> str:
    present, missing_keywords = keyword_coverage(job, resume_text)
    rows = "\n".join(
        f"| {STATUS_ICON[m.status]} {m.status} | {table_cell(m.qualification)} | "
        f"{table_cell(m.evidence or '—')} |"
        for m in result.required + result.preferred
    )
    return f"""## Match score: {compute_score(result)}/100
**Confidence:** {confidence(job)}  
**Required met:** {count_met(result.required)} · **Preferred met:** {count_met(result.preferred)}  
**Your experience:** ~{result.candidate_years_experience} yrs (job asks: {job.years_experience_required or "not stated"})

**Summary:** {result.summary}

### Missing skills
{bullet_list(missing_skills(result))}

### 🔑 Keywords on your resume: {len(present)}/{len(job.keywords)}
**Missing (exact wording from the posting):**  
{" · ".join(f"`{k}`" for k in missing_keywords) or "_None — every keyword appears on your resume_"}

### Details
| Status | Qualification | Evidence from your resume |
|---|---|---|
{rows}
"""


MAX_CHARS = 15000


def analyze(posting_text: str, resume_text: str):
    posting_text = posting_text.strip()
    resume_text = resume_text.strip()

    if not posting_text:
        raise gr.Error("Please paste a job description first.")
    if len(posting_text) < 200:
        raise gr.Error("That looks too short to be a job posting. Please paste the full description.")
    if len(posting_text) > MAX_CHARS or len(resume_text) > MAX_CHARS:
        raise gr.Error(f"Please keep each box under {MAX_CHARS:,} characters.")

    try:
        job = extract_job(posting_text)
        if not resume_text:
            return format_job(job), "_Paste your resume to see your match score._", job.model_dump()
        result = match_resume(job, resume_text)
    except LLMError as error:
        raise gr.Error(str(error))

    return format_job(job), format_match(job, result, resume_text), job.model_dump()


with gr.Blocks(title="Job Description Analyzer") as demo:
    gr.Markdown(
        "# 🔍 Job Description Analyzer\n"
        "Paste a job posting to get a structured breakdown and red flags. "
        "Add your resume to see an evidence-based match score.\n\n"
        "_Your text is sent to Google's Gemini API for analysis. Don't paste anything confidential._"
    )

    with gr.Row():
        posting_box = gr.Textbox(label="Job description", lines=15,
                                 placeholder="Paste the full job posting here...")
        resume_box = gr.Textbox(label="Your resume (optional)", lines=15,
                                placeholder="Paste your resume as plain text...")

    analyze_button = gr.Button("Analyze", variant="primary")

    with gr.Row():
        job_output = gr.Markdown()
        match_output = gr.Markdown()

    with gr.Accordion("Raw JSON", open=False):
        json_output = gr.JSON()

    analyze_button.click(
        analyze,
        inputs=[posting_box, resume_box],
        outputs=[job_output, match_output, json_output],
    )


if __name__ == "__main__":
    demo.launch()