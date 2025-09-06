# Agentic AI HR Assistant

## Overview

**Agentic AI HR Assistant** is an intelligent recruitment assistant designed to **automate resume screening, candidate management, and profile analysis** using AI.  
Built with **Streamlit**, it enables HR teams to seamlessly upload resumes, extract structured data, and chat with an AI agent about each candidate’s suitability.

Perfect for:
- HR teams and recruiters managing multiple applicants
- Companies aiming to streamline their hiring pipeline
- Anyone wanting to explore AI-driven recruitment tools


## Key Features

- **Smart Resume Parsing (PDF)**  
  Extracts key candidate details:
  - Name, email, phone, LinkedIn
  - Skills
  - Work experience
  - Education
  - Summary/Bio

- **Agentic AI Chatbot**  
  - Answers recruiter questions about candidates
  - Provides quick insights based on parsed profiles
  - Powered by **Groq LLM** (OpenAI-compatible)

- **Candidate Database Management**  
  - Add, update, delete candidate profiles
  - Store securely in SQLite
  - View all candidates in a simple interface

- **Interactive Web App**  
  Built with Streamlit for ease of use and fast deployment.


## Tech Stack

- **Python 3.9+**
- [Streamlit](https://streamlit.io/)
- [PyPDF2](https://pypi.org/project/PyPDF2/) – Resume text extraction
- [Requests](https://pypi.org/project/requests/) – API calls
- [SQLite3](https://docs.python.org/3/library/sqlite3.html) – Lightweight database
- [Groq API](https://groq.com/) – AI-powered parsing & chat


## Getting Started

**1. Clone the Repository**
```bash
git clone https://github.com/AishwaryaKokate1406/Agentic_AI_HR_ASSISTANT.git
cd Agentic_AI_HR_ASSISTANT
```

**2. Install Dependencies**
```bash
python3 -m venv venv
pip install -r requirements.txt
```

**3. Set Up API Key**  

Create new `.env` file and store your `GROQ_API_KEY`
```bash
GROQ_API_KEY="your_groq_api_key_here"
```

**4. Run the App**
```bash
streamlit run app.py
```



