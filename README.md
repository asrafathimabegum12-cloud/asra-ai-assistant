# Asra's AI Assistant

This project includes the first user onboarding/profile collection flow for Asra's AI Assistant.

## Project Structure

```text
project1/
├── backend/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   └── models.py
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── script.js
├── requirements.txt
├── .gitignore
├── README.md
└── run.py
```

## Required Dependencies

```bash
pip install -r requirements.txt
```

## Setup Commands

### 1. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the FastAPI backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Open the frontend

Open the file in a browser or run a local static server:

```bash
cd frontend
python -m http.server 5500
```

Then visit:

```text
http://localhost:5500
```

## API Endpoint

### POST /api/users/profile

Form fields:
- `profile`: JSON string containing the full user profile object
- `resume`: optional file upload (`PDF`, `DOC`, or `DOCX`)

Expected JSON structure:

```json
{
  "personal_information": {
    "full_name": "Asra Khan",
    "preferred_name": "Asra",
    "email": "asra@example.com",
    "phone_number": "+1 234 567 8900",
    "date_of_birth": "1999-05-17",
    "gender": "Female",
    "current_city": "Bengaluru",
    "country": "India"
  },
  "education": {
    "highest_education_level": "Bachelor's Degree",
    "degree_course": "B.Tech Computer Science",
    "specialization_branch": "Artificial Intelligence",
    "college_university": "IIT Delhi",
    "graduation_year": "2022",
    "current_education_status": "Graduated"
  },
  "career_information": {
    "current_status": "Working Professional",
    "target_job_role": "Data Analyst",
    "preferred_industry": "Technology",
    "preferred_work_location": "Remote",
    "experience_level": "1-3 years",
    "current_company": "Acme",
    "current_job_role": "Junior Analyst"
  },
  "skills": {
    "programming_languages": ["Python", "JavaScript"],
    "technical_skills": ["Data Analysis"],
    "tools_technologies": ["MongoDB", "Power BI"],
    "soft_skills": ["Communication", "Leadership"]
  },
  "career_goals": {
    "short_term_career_goal": "Become a Senior Analyst in 2 years.",
    "long_term_career_goal": "Lead AI-based decision systems in product teams.",
    "target_role": "Senior Data Analyst",
    "target_companies": ["Google", "Amazon"],
    "areas_to_improve": ["System Design", "Communication"],
    "preferred_learning_style": ["Mixed"]
  },
  "resume_information": {
    "uploaded": true,
    "file_name": "resume.pdf",
    "file_type": "application/pdf",
    "file_size_bytes": 154200,
    "processed": false,
    "storage_path": null
  }
}
```

## MongoDB

The backend is prepared to store the profile document in MongoDB using this logical structure:

```text
user_id
personal_information
education
career_information
skills
career_goals
resume_information
created_at
updated_at
```

Connection settings can be configured in [backend/config.py](backend/config.py) using the environment variables:

```bash
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=asra_ai_assistant
MONGODB_COLLECTION_NAME=user_profiles
```

If MongoDB is not running, the backend falls back to in-memory storage for local development.

## Running Locally

1. Start MongoDB locally.
2. Activate your virtual environment.
3. Run the backend:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

4. Open the frontend page:

```bash
cd frontend
python -m http.server 5500
```

Then open:

```text
http://localhost:5500
```

## Notes

- This stage focuses only on the onboarding/profile collection system.
- Dashboard and AI features are intentionally not included.
- The app is intentionally built with plain HTML, CSS, and JavaScript to keep the frontend and backend separated.
