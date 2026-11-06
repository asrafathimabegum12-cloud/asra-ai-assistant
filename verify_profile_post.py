import json
import urllib.request

profile = {
    "personal_information": {
        "full_name": "Asra Khan",
        "preferred_name": "Asra",
        "email": "asra@example.com",
        "phone_number": "+1 234 567 8900",
        "date_of_birth": "1999-05-17",
        "gender": "Female",
        "current_city": "Bengaluru",
        "country": "India",
    },
    "education": {
        "highest_education_level": "Bachelor's Degree",
        "degree_course": "B.Tech Computer Science",
        "specialization_branch": "Artificial Intelligence",
        "college_university": "IIT Delhi",
        "graduation_year": "2022",
        "current_education_status": "Graduated",
    },
    "career_information": {
        "current_status": "Working Professional",
        "target_job_role": "Data Analyst",
        "preferred_industry": "Technology",
        "preferred_work_location": "Remote",
        "experience_level": "1-3 years",
        "current_company": "Acme",
        "current_job_role": "Junior Analyst",
    },
    "skills": {
        "programming_languages": ["Python", "JavaScript"],
        "technical_skills": ["Data Analysis"],
        "tools_technologies": ["MongoDB", "Power BI"],
        "soft_skills": ["Communication", "Leadership"],
    },
    "career_goals": {
        "short_term_career_goal": "Become a Senior Analyst within 2 years.",
        "long_term_career_goal": "Lead AI-driven product analytics teams.",
        "target_role": "Senior Data Analyst",
        "target_companies": ["Google", "Amazon"],
        "areas_to_improve": ["System Design", "Communication"],
        "preferred_learning_style": ["Mixed"],
    },
    "resume_information": {
        "uploaded": False,
        "file_name": None,
        "file_type": None,
        "file_size_bytes": None,
        "processed": False,
        "storage_path": None,
    },
}

boundary = "----AsraBoundary"
body = (
    f"--{boundary}\r\n"
    'Content-Disposition: form-data; name="profile"\r\n\r\n'
    f"{json.dumps(profile)}\r\n"
    f"--{boundary}--\r\n"
).encode("utf-8")

request = urllib.request.Request(
    "http://localhost:8000/api/users/profile",
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    method="POST",
)
with urllib.request.urlopen(request, timeout=20) as response:
    print(response.status)
    print(response.read().decode())
