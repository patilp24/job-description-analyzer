PROMPT_TEMPLATE = """Extract structured data from the job posting below and return it as a single JSON object.
Accuracy to the source text is the top priority: use ONLY information explicitly stated in the
posting, and never guess or invent. If a field is not mentioned, use null for single values
and [] for lists.

<posting>
{posting}
</posting>

## Extraction rules

**Qualifications**
- Write each item as a short keyword phrase of 2-6 words, like a line on a resume skills list.
  Good: "Python", "2+ years SQL", "AWS (EC2, S3, Lambda)", "Stakeholder communication".
  Bad: full sentences, copied paragraphs, or labels like "AI Engineering: ...".
- Split combined requirements into separate items. Skip pure filler such as
  "high-performing" or "passionate".
- Limit each list to a maximum of 8 items, most important first.
- required_qualifications: items the posting marks as required or minimum.
- preferred_qualifications: items marked preferred or nice-to-have.
- If the posting has no clear required section, put those items under preferred.
- Each item appears in only ONE list.

**Education**
- Put ALL degree requirements in the education fields, never in the qualification lists.
- education_required: the minimum degree stated, as a short phrase (e.g., "Bachelor's in CS or related").
- education_preferred: any preferred/advanced degree (e.g., "Master's degree").

**Seniority** (exactly one of: "Entry" (0-1 yrs), "Early-career" (1-3 yrs), "Mid" (3-5 yrs),
"Senior" (5+ yrs), "Unclear")
- Use stated years of experience first. "Several years" = "Mid".
- If no years are stated: "Senior", "Staff", "Lead", or "Principal" in the title = "Senior";
  "Associate", "Junior", "Entry", "Graduate", or "New grad" in the title or text =
  "Entry" or "Early-career".
- If there is no evidence either way, use "Unclear". Never default to "Mid".

**Work model** (exactly one of: "Remote", "Hybrid", "On-site", or null)
- Use null unless the posting explicitly states it.

**Sponsorship** (exactly one of: "Offered", "Not offered", "Not mentioned")

**Red flags**
- Check the posting against each of these, and add a short flag (under 15 words) naming the
  specific evidence for every one that applies:
  - Salary missing or no upper range
  - Experience required doesn't match the level
  - Unusually broad required tech stack
  - Vague or filler requirements
  - Key details missing (company, location, duties)
- Hybrid or on-site work is NOT a red flag.
- Return [] only if none apply.

## Output
Return only the JSON object, with no commentary and no code fences, using exactly these keys:
{{
  "job_title": string,
  "company": string or null,
  "seniority": string,
  "years_experience_required": string or null,
  "salary": string or null,
  "work_model": string or null,
  "education_required": string or null,
  "education_preferred": string or null,
  "required_qualifications": [string],
  "preferred_qualifications": [string],
  "red_flags": [string],
  "sponsorship": string
}}
"""


MATCH_PROMPT_TEMPLATE = """Compare a candidate's resume against a job's qualifications.
Be strict and honest: this helps the candidate decide where to apply and what to learn.

<required_qualifications>
{required}
</required_qualifications>

<preferred_qualifications>
{preferred}
</preferred_qualifications>

<education_required>
{education}
</education_required>

<resume>
{resume}
</resume>

## Rules
- Evaluate EVERY qualification listed above, in the same order, copying its text exactly
  into "qualification". Do not add, merge, or skip any.
- status:
  - "Met": the resume clearly shows it (skills, coursework, projects, or work experience).
  - "Partial": related or weaker evidence (e.g., a similar tool, fewer years, coursework only).
  - "Missing": no evidence in the resume.
- Use ONLY what the resume states. Never assume a skill from a job title or degree alone.
- evidence: a short quote or reference from the resume (under 15 words) supporting
  Met or Partial; null if Missing.
- education_status: "Met", "Not met", "Not required" (if no education is listed above),
  or "Unclear".
- summary: 2 sentences: the candidate's strongest fit and the most important gap.
- Years of experience: count ONLY from dates in the resume's work history
  (internships count at their actual length; education does not count).
  If the total is below the requirement, use "Partial" if it is at least half,
  otherwise "Missing". Show the calculation in evidence (e.g., "~2.5 yrs total").
  - candidate_years_experience: total years of professional work from the dated roles
  in the resume (internships at their actual length, education excluded), as a number
  rounded to one decimal (e.g., 3.5).

## Output
Return only the JSON object, with no commentary and no code fences, using exactly these keys:
{{
  "required": [{{"qualification": string, "status": string, "evidence": string or null}}],
  "preferred": [{{"qualification": string, "status": string, "evidence": string or null}}],
  "education_status": string,
  "candidate_years_experience": number,
  "summary": string
}}
"""