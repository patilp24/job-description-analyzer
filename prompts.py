PROMPT_TEMPLATE = """Extract structured data from the job posting below and return it as a single JSON object.
Accuracy to the source text is the top priority: use ONLY information explicitly stated in the
posting, and never guess or invent. If a field is not mentioned, use null for single value and [] for lists.

<posting>
{posting}
</posting>

## Extraction rules

**Qualifications**
- Write each item as a short phrase (2-10 words), like a line on a resume skills list.
- ALWAYS keep specific named tools, languages, platforms, and methods (e.g., SQL, Python,
  AWS, Tableau, predictive modeling). Never replace them with a generic category.
  Good: "SQL, statistics, predictive modeling, spreadsheets", "AWS (EC2, S3, Lambda)", "Python"
  Bad: "Analytical tools and techniques", "Cloud experience", full sentences, copied paragraphs, or labels like "AI Engineering: ...".
- Split requirements joined by "and" into separate items. But keep "or" alternatives as ONE item (e.g., "2 yrs consulting, strategy, IB, VC, or PE"), because any one
  of them satisfies the requirement. Never list the same requirement twice. Skip pure filler such as "high-performing" or "passionate".
- Limit each list to a maximum of 8 items, most important first.
- required_qualifications: items the posting marks as required or minimum.
- preferred_qualifications: items marked preferred or nice-to-have.
- If the posting has no clear required section, put those items under preferred.
- Each item appears in only ONE list.

**Keywords**
- keywords: the specific skills, tools, technologies, methods, certifications, and domain
  terms an applicant tracking system would scan for, copied EXACTLY as written in the
  posting (same spelling, capitalization, and wording). One term per item
  (e.g., "SQL", "predictive modeling", "spreadsheet software").
  Do not paraphrase, abbreviate, expand, or invent terms. Maximum 25, most important first.

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
  "keywords": [string],
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
- Evaluate EVERY qualification listed above, in the same order, copying its text exactly into "qualification". Do not add, merge, or skip any.
- status:
  - "Met": the resume clearly shows it (skills, coursework, projects, or work experience).
  - "Partial": related or weaker evidence (e.g., a similar tool, fewer years, coursework only).
  - "Missing": no evidence in the resume.
- Use ONLY what the resume states. Never assume a skill from a job title or degree alone.
- evidence: for Met or Partial, copy ONE continuous excerpt from the resume WORD FOR WORD
  (3-15 words). Do not paraphrase, change tense, add words, or use "...". 
  null if Missing.
- education_status: "Met", "Not met", "Not required" (if no education is listed above), or "Unclear".
- summary: 2 sentences: the candidate's strongest fit and the most important gap.
- The candidate has {years} years of total professional experience (already calculated
  from their dated roles). Use this number for experience requirements; do not recalculate.
- general_experience: true ONLY if the qualification is about total years of professional
  experience in general (e.g., "5 years related experience", "3+ years of work experience").
  false if it names a specific field, role type, or skill
  (e.g., "2 years in consulting or banking", "2+ years SQL").


## Output
Return only the JSON object, with no commentary and no code fences, using exactly these keys:
{{
  "required": [{{"qualification": string, "status": string, "evidence": string or null, "general_experience": boolean}}],
  "preferred": [{{"qualification": string, "status": string, "evidence": string or null, "general_experience": boolean}}],
  "education_status": string,
  "summary": string
}}
"""

RESUME_ROLES_PROMPT = """List every professional role in the resume below: jobs and internships
from the work experience section. Do NOT include education or projects.

<resume>
{resume}
</resume>

## Rules
- Copy dates from the resume. Do not calculate anything.
- start and end must be in YYYY-MM format (e.g., "2020-11").
- If a role is current ("Present", "Current", "Now"), set end to "Present".
- If only a year is given, use "-01" for start and "-12" for end.

## Output
Return only the JSON object, with no commentary and no code fences:
{{
  "roles": [{{"title": string, "organization": string, "start": "YYYY-MM", "end": "YYYY-MM" or "Present"}}]
}}
"""