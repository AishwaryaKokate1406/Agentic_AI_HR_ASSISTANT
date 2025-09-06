import streamlit as st
import json
import tempfile
import re
from database import (
    init_db,
    get_all_candidate_names,
    get_candidate_by_name,
    add_or_update_candidate,
    delete_candidate_by_name,
)
from data_extractor import (
    extract_text_from_pdf,
    get_profile_data_from_text,
    generate_chatbot_response,
)

# --- App Configuration ---
st.set_page_config(
    page_title="AI HR Assistant",
    page_icon="🤖",
    layout="wide"
)

# --- Database Initialization ---
init_db()

# --- App State Management ---
if "current_candidate" not in st.session_state:
    st.session_state.current_candidate = None
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "temp_profile" not in st.session_state:
    st.session_state.temp_profile = None

# --- Helpers: cleaning/sanitization ---
def _strip(v):
    return v.strip() if isinstance(v, str) else ""

def parse_skills(skills_text: str):
    parts = re.split(r"[,\n;]", skills_text or "")
    out, seen = [], set()
    for p in parts:
        s = _strip(p)
        key = s.lower()
        if s and key not in seen:
            out.append(s)
            seen.add(key)
    return out

def clean_experience(entries):
    cleaned = []
    for e in entries or []:
        company = _strip(e.get("company", ""))
        title = _strip(e.get("title", ""))
        duration = _strip(e.get("duration", ""))
        description = _strip(e.get("description", ""))
        if company or title or duration or description:
            cleaned.append({
                "company": company,
                "title": title,
                "duration": duration,
                "description": description
            })
    return cleaned


def clean_education(entries):
    cleaned = []
    for e in entries or []:
        degree = _strip(e.get("degree", ""))
        institution = _strip(e.get("institution", ""))
        year = _strip(e.get("year", ""))
        if degree or institution or year:
            cleaned.append({"degree": degree, "institution": institution, "year": year})
    return cleaned

# --- Helper Functions ---
def display_profile(data):
    """Renders the candidate profile in a structured form."""
    st.subheader("📄 Candidate Profile")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Name:** <span style='color:white'>{data.get('name', 'N/A')}</span>", unsafe_allow_html=True)
        st.markdown(f"**Email:** <span style='color:white'>{data.get('email', 'N/A')}</span>", unsafe_allow_html=True)
        st.markdown(f"**Phone:** <span style='color:white'>{data.get('phone', 'N/A')}</span>", unsafe_allow_html=True)

    with col2:
        linkedin_url = data.get("linkedin_profile")
        if linkedin_url:
            if not linkedin_url.startswith("http"):
                linkedin_url = "https://" + linkedin_url
            st.markdown(f"**LinkedIn:** [Profile]({linkedin_url})", unsafe_allow_html=True)
        else:
            st.markdown("**LinkedIn:** N/A", unsafe_allow_html=True)
        
        st.markdown(f"**Summary:** <span style='color:white'>{data.get('summary', 'N/A')}</span>", unsafe_allow_html=True)

    st.markdown("")
    with st.expander("💼 Work Experience", expanded=True):
        for exp in data.get("experience", []):
            st.markdown(f"**{exp.get('title', 'N/A')}** at **{exp.get('company', 'N/A')}** ({exp.get('duration', 'N/A')})")
            if exp.get("description"):
                st.markdown(f"_{exp.get('description')}_")

    with st.expander("🎓 Education", expanded=True):
        for edu in data.get("education", []):
            st.markdown(f"**{edu.get('degree', 'N/A')}** from **{edu.get('institution', 'N/A')}** ({edu.get('year', 'N/A')})")

    with st.expander("🛠️ Skills", expanded=True):
        skills = data.get("skills", [])
        if skills:
            for skill in skills:
                st.markdown(f"- {skill}")
        else:
            st.warning("No skills listed.")

# --- Sidebar for Navigation & Resume Upload ---
with st.sidebar:
    st.title("🤖 AI HR Assistant")
    st.markdown("---")

    # --- Add New Candidate ---
    st.header("Add New Candidate")
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")

    if uploaded_file and st.button("Parse Resume"):
        with st.spinner("Analyzing resume..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                temp_file_path = tmp_file.name

            resume_text = extract_text_from_pdf(temp_file_path)
            if resume_text:
                profile_data = get_profile_data_from_text(resume_text)
                if profile_data and "error" not in profile_data:
                    st.session_state.temp_profile = profile_data
                    st.session_state.current_candidate = None  # New candidate mode
                    st.success("Resume parsed! Review details below before saving.")
                else:
                    st.error(f"AI Error: {profile_data.get('error', 'Could not extract data.')}")
            else:
                st.error("File Error: Could not read text from the PDF.")

    st.markdown("---")

    # --- Select Candidate ---
    st.header("Select Candidate")
    candidate_names = get_all_candidate_names()

    if candidate_names:
        if st.session_state.temp_profile:
            # Block switching while adding/editing a candidate
            st.info("📄 Finish adding or editing the current candidate before switching.")
        else:
            try:
                current_index = candidate_names.index(st.session_state.current_candidate)
            except (ValueError, TypeError):
                current_index = 0

            selected_candidate = st.selectbox("Choose a candidate", options=candidate_names, index=current_index)
            if selected_candidate != st.session_state.current_candidate:
                st.session_state.current_candidate = selected_candidate
                st.session_state.chats[selected_candidate] = []  # Reset chat
                st.session_state.temp_profile = None  # Clear edit state
                st.rerun()
    else:
        st.info("No candidates in the database. Add one to begin.")

# --- Editable Form for New Candidate ---
if st.session_state.temp_profile and not st.session_state.current_candidate:
    st.subheader("✏️ Review & Edit Candidate Details (New Candidate)")

    with st.form("new_candidate_form", clear_on_submit=False):
        name = st.text_input("Name", st.session_state.temp_profile.get("name", ""))
        email = st.text_input("Email", st.session_state.temp_profile.get("email", ""))
        phone = st.text_input("Phone", st.session_state.temp_profile.get("phone", ""))
        linkedin = st.text_input("LinkedIn", st.session_state.temp_profile.get("linkedin_profile", ""))
        summary = st.text_area("Summary", st.session_state.temp_profile.get("summary", ""))
        skills_text = st.text_area("Skills (comma separated)", ", ".join(st.session_state.temp_profile.get("skills", [])))

        st.markdown("**Experience**")
        exp_entries = st.session_state.temp_profile.get("experience", [])
        experience = []
        for i, exp in enumerate(exp_entries):
            company = st.text_input(f"Company {i+1}", exp.get("company", ""), key=f"new_exp_company_{i}")
            title = st.text_input(f"Title {i+1}", exp.get("title", ""), key=f"new_exp_title_{i}")
            duration = st.text_input(f"Duration {i+1}", exp.get("duration", ""), key=f"new_exp_duration_{i}")
            description = st.text_area(f"Description {i+1}", exp.get("description", ""), key=f"new_exp_desc_{i}")
            experience.append({
                "company": company,
                "title": title,
                "duration": duration,
                "description": description
            })

        st.markdown("**Education**")
        edu_entries = st.session_state.temp_profile.get("education", [])
        education = []
        for i, edu in enumerate(edu_entries):
            degree = st.text_input(f"Degree {i+1}", edu.get("degree", ""), key=f"new_edu_degree_{i}")
            institution = st.text_input(f"Institution {i+1}", edu.get("institution", ""), key=f"new_edu_institution_{i}")
            year = st.text_input(f"Year {i+1}", edu.get("year", ""), key=f"new_edu_year_{i}")
            education.append({"degree": degree, "institution": institution, "year": year})

        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("💾 Save Candidate")
        with col2:
            cancel = st.form_submit_button("❌ Cancel")

        if submitted:
            try:
                candidate_data = {
                    "name": _strip(name),
                    "email": _strip(email),
                    "phone": _strip(phone),
                    "linkedin_profile": _strip(linkedin),
                    "summary": _strip(summary),
                    "skills": parse_skills(skills_text),
                    "experience": clean_experience(experience),   # <-- drops blank rows
                    "education": clean_education(education),     # <-- drops blank rows
                }
                add_or_update_candidate(candidate_data)
                st.success(f"Candidate {candidate_data['name']} saved successfully!")
                st.session_state.current_candidate = candidate_data["name"]
                st.session_state.chats[candidate_data["name"]] = []
                st.session_state.temp_profile = None
                st.rerun()
            except Exception as e:
                st.error(f"Error saving candidate: {e}")

        if cancel:
            st.session_state.temp_profile = None
            st.rerun()

# --- Edit Existing Candidate ---
elif st.session_state.temp_profile and st.session_state.current_candidate:
    st.subheader(f"✏️ Edit Candidate: {st.session_state.current_candidate}")

    with st.form("edit_candidate_form", clear_on_submit=False):
        name = st.text_input("Name", st.session_state.temp_profile.get("name", ""))
        email = st.text_input("Email", st.session_state.temp_profile.get("email", ""))
        phone = st.text_input("Phone", st.session_state.temp_profile.get("phone", ""))
        linkedin = st.text_input("LinkedIn", st.session_state.temp_profile.get("linkedin_profile", ""))
        summary = st.text_area("Summary", st.session_state.temp_profile.get("summary", ""))
        skills_text = st.text_area("Skills (comma separated)", ", ".join(st.session_state.temp_profile.get("skills", [])))

        st.markdown("**Experience**")
        exp_entries = st.session_state.temp_profile.get("experience", [])
        experience = []
        for i, exp in enumerate(exp_entries):
            company = st.text_input(f"Company {i+1}", exp.get("company", ""), key=f"edit_exp_company_{i}")
            title = st.text_input(f"Title {i+1}", exp.get("title", ""), key=f"edit_exp_title_{i}")
            duration = st.text_input(f"Duration {i+1}", exp.get("duration", ""), key=f"edit_exp_duration_{i}")
            description = st.text_area(f"Description {i+1}", exp.get("description", ""), key=f"edit_exp_desc_{i}")
            experience.append({
                "company": company,
                "title": title,
                "duration": duration,
                "description": description
            })

        st.markdown("**Education**")
        edu_entries = st.session_state.temp_profile.get("education", [])
        education = []
        for i, edu in enumerate(edu_entries):
            degree = st.text_input(f"Degree {i+1}", edu.get("degree", ""), key=f"edit_edu_degree_{i}")
            institution = st.text_input(f"Institution {i+1}", edu.get("institution", ""), key=f"edit_edu_institution_{i}")
            year = st.text_input(f"Year {i+1}", edu.get("year", ""), key=f"edit_edu_year_{i}")
            education.append({"degree": degree, "institution": institution, "year": year})

        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("💾 Update Candidate")
        with col2:
            cancel = st.form_submit_button("❌ Cancel")

        if submitted:
            try:
                candidate_data = {
                    "name": _strip(name),
                    "email": _strip(email),
                    "phone": _strip(phone),
                    "linkedin_profile": _strip(linkedin),
                    "summary": _strip(summary),
                    "skills": parse_skills(skills_text),
                    "experience": clean_experience(experience),   # <-- drops blank rows
                    "education": clean_education(education),     # <-- drops blank rows
                }
                add_or_update_candidate(candidate_data, candidate_id=st.session_state.temp_profile["id"])

                # --- Handle chat rename (before overwriting current_candidate) ---
                old_name = st.session_state.current_candidate
                new_name = candidate_data["name"]

                if old_name in st.session_state.chats:
                    st.session_state.chats[new_name] = st.session_state.chats.pop(old_name)
                else:
                    st.session_state.chats[new_name] = []

                st.session_state.current_candidate = new_name
                st.session_state.temp_profile = None

                st.success(f"Candidate {new_name} updated successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"Error updating candidate: {e}")

        if cancel:
            st.session_state.temp_profile = None
            st.rerun()

# --- Main Page View ---
elif st.session_state.current_candidate:
    candidate_profile = get_candidate_by_name(st.session_state.current_candidate)

    if candidate_profile:
        display_profile(candidate_profile)

        col1, col2 = st.columns(2)

        with col1:
            if st.button(f"✏️ Edit {st.session_state.current_candidate}"):
                st.session_state.temp_profile = candidate_profile
                st.rerun()

        with col2:
            if st.button(f"🗑️ Delete {st.session_state.current_candidate}"):
                delete_candidate_by_name(st.session_state.current_candidate)
                st.success(f"Candidate {st.session_state.current_candidate} deleted successfully!")
                if st.session_state.current_candidate in st.session_state.chats:
                    del st.session_state.chats[st.session_state.current_candidate]
                st.session_state.current_candidate = None
                st.rerun()

        st.markdown("---")
        st.header("💬 Chat with AI Assistant")
        st.info(f"You are now chatting about **{st.session_state.current_candidate}**.")

        chat_history = st.session_state.chats[st.session_state.current_candidate]

        for message in chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask about their skills, experience, etc."):
            chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = generate_chatbot_response(prompt, candidate_profile)
                    st.markdown(response)

            chat_history.append({"role": "assistant", "content": response})
    else:
        st.error(f"Could not retrieve data for {st.session_state.current_candidate}.")
else:
    st.header("Welcome!")
    st.info("Please add a candidate using the sidebar to get started.")
