from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

#1. Read the Job Description from the text file.
with open("sample_jd.txt", "r", encoding = "utf-8") as f:
    job_description = f.read()

#2. Build the Prompt: instructions + the job description
prompt = f"""
You are a career assistant. Summarize this job description for a job seeker.

Give:
1. Job title and compnay
2. A 2-sentence summary fo a role
3. The top 5 required skills
4. Experience level (entry, mid, senior)

Job Description:
{job_description}
"""

#3. Send it to Gemini
interaction = client.interactions.create(
    model = "gemini-3.5-flash-lite",
    input = prompt
)

#4. Print the answer
print(interaction.output_text)