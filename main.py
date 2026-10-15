from dotenv import load_dotenv
from google import genai

load_dotenv()  # reads .env and sets GEMINI_API_KEY for this program

client = genai.Client()

interaction = client.interactions.create(
    model="gemini-3.5-flash-lite",
    input="Say hello in one short sentence."
)

print(interaction.output_text)