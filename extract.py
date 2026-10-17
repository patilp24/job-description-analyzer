import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

MODEL = "gemini-3.5-flash-lite"
POSTINGS_DIR = Path("samples/postings")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

PROMPT_TEMPLATE = """You are an expert career analyst. Extract key facts from the job posting
delimited by <posting></posting> tags.

Rules:
- Use ONLY information stated in the posting. Never guess or invent.
- If a field is not mentioned, use null (for single values) or [] (for lists).
- Keep "required_skills" and "preferred_skills" separate, exactly as the posting divides them.
- Seniority must be one of: "Entry" (0-1 yrs), "Early-career" (1-3 yrs),
  "Mid" (3-5 yrs), "Senior" (5+ yrs). Base it on required years of experience;
  if no years are stated, infer from the title and responsibilities.
- Sponsorship must be one of: "Offered", "Not offered", "Not mentioned".
- Red flags are warning signs about the posting itself, such as: no salary listed,
  unrealistic experience for the level, vague duties, an extremely broad required
  tech stack, or missing key details. Hybrid or on-site work is NOT a red flag.

Return ONLY valid JSON with exactly these keys, and no other text:
{{
  "job_title": string,
  "company": string or null,
  "seniority": string,
  "years_experience_required": string or null,
  "salary": string or null,
  "work_model": string or null,
  "required_skills": [string],
  "preferred_skills": [string],
  "red_flags": [string],
  "sponsorship": string
}}

<posting>
{posting}
</posting>
"""

for posting_file in sorted(POSTINGS_DIR.glob("*.txt")):
    posting_text = posting_file.read_text(encoding="utf-8")
    prompt = PROMPT_TEMPLATE.format(posting=posting_text)

    print(f"Analyzing {posting_file.name} ...")
    interaction = client.interactions.create(model=MODEL, input=prompt)
    result = interaction.output_text

    # Save each result so you can compare it with your answer key
    output_file = OUTPUT_DIR / f"{posting_file.stem}.json"
    output_file.write_text(result, encoding="utf-8")
    print(f"  saved to {output_file}")

    time.sleep(5)  # stay well under the free tier's 15 requests/minute

print("Done.")