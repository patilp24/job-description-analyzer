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
- Use ONLY information explicitly stated in the posting. Never guess or invent.
- If a field is not mentioned, use null (for single values) or [] (for lists).
- "required_qualifications": everything the posting marks as required/minimum,
  INCLUDING degrees and years of experience. "preferred_qualifications": everything
  marked preferred/nice-to-have. Each item must appear in only ONE list.
  If the posting has no explicit required section, put items under preferred.
- Seniority must be one of: "Entry" (0-1 yrs), "Early-career" (1-3 yrs),
  "Mid" (3-5 yrs), "Senior" (5+ yrs).
  Use stated years first. "Several years" = "Mid".
  If no years are stated, use the title: "Senior", "Staff", "Lead", "Principal" = "Senior";
  "Associate", "Junior", "Entry", "Graduate" = "Entry" or "Early-career".
  Never choose "Senior" unless the title or years clearly say so.
- work_model must be one of "Remote", "Hybrid", "On-site", or null.
  Use null unless the posting explicitly states it.
- Sponsorship must be one of: "Offered", "Not offered", "Not mentioned".
- red_flags: specific concerns about THIS posting, each explaining the evidence
  (e.g., "Master's preferred for an entry-level role"). Do not use generic phrases.
  Hybrid or on-site work is NOT a red flag. Return [] if there are none.

Return ONLY valid JSON with exactly these keys, and no other text:
{{
  "job_title": string,
  "company": string or null,
  "seniority": string,
  "Educationsl Requirements": string,
  "years_experience_required": string or null,
  "salary": string or null,
  "work_model": string or null,
  "required_qualifications": [string],
  "preferred_qualifications": [string],
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