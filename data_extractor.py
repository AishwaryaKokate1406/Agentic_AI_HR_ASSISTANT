import os
import json
import requests
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL_NAME = "llama-3.1-8b-instant"  # Supported Groq model

def query_llm(payload):
    """Send request to Groq using OpenAI-compatible chat completions."""
    if not GROQ_API_KEY:
        return {"error": "Groq API key missing in .env"}

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    try:
        resp = requests.post(f"{GROQ_BASE_URL}/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file."""
    try:
        with open(pdf_path, "rb") as file:
            reader = PdfReader(file)
            text = "".join(page.extract_text() or "" for page in reader.pages)
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def get_profile_data_from_text(resume_text: str):
    """Extract structured candidate profile from resume text with forced JSON mode."""
    prompt = f"""
Extract the following candidate details from the resume and return ONLY valid JSON:

- name
- email
- phone
- summary
- skills (list of strings)
- experience (list of objects: company, title, duration, description)
- education (list of objects: degree, institution, year)
- linkedin_profile (string URL if available)

Resume:
{resume_text}
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are an expert HR assistant that extracts structured data from resumes."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 800,
        "response_format": {"type": "json_object"}  # 👈 forces valid JSON
    }

    response = query_llm(payload)
    if "error" in response:
        return response

    try:
        content = response["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        return {"error": f"JSON parsing error: {e}", "raw": response}

def generate_chatbot_response(user_message: str, candidate_data: dict):
    """Generate chatbot response based on candidate profile."""
    profile_json = json.dumps(candidate_data, indent=2)
    prompt = f"""
Here is a candidate profile:
{profile_json}

User question: {user_message}
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are an HR assistant answering based only on the provided candidate profile."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 500
    }

    response = query_llm(payload)
    if "error" in response:
        return response["error"]

    try:
        return response["choices"][0]["message"]["content"]
    except Exception:
        return "Error: Could not parse chatbot response."
