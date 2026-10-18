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