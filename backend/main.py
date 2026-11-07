from __future__ import annotations
from io import BytesIO
from pathlib import Path
import asyncio
import re
import json
import time
from datetime import datetime, timezone
from typing import Annotated, Any
from uuid import uuid4

import httpx
from pypdf import PdfReader
from docx import Document

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.config import APP_NAME, CORS_ORIGINS

from backend.database import (
    fetch_all_profiles,
    fetch_profile_by_user_id,
    fetch_test_results,
    get_users_collection,
    store_profile_document,
    store_chat_message,
    store_test_result,
    fetch_chat_history,
    update_profile_document,
    get_learning_plans_collection,
    fetch_interview_sessions,
    store_interview_session,
    store_job_application,
    fetch_job_applications,
    update_job_application_status,
    fetch_study_tasks,
    store_study_task,
    update_study_task,
    delete_study_task,
    fetch_quiz_results,
    store_quiz_result,
    fetch_interview_bank_progress,
    upsert_interview_bank_progress,
    fetch_roadmaps,
    store_roadmap,
    update_roadmap,
    fetch_notes,
    store_note,
    update_note,
    delete_note,
    fetch_achievements,
    store_achievement,
)

from backend.models import UserProfileCreate
from backend.practice_tests import QUESTION_BANK, SUBJECTS, evaluate_answers, get_questions_for_subject, normalize_subject
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={"timeout": 180000},
)


def _is_retryable_gemini_error(exc: Exception) -> bool:
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    message = str(exc).lower()
    if code in {429, 500, 503, 504}:
        return True
    if isinstance(exc, (httpx.TimeoutException, TimeoutError)):
        return True
    return (
        "timeout" in message
        or "timed out" in message
        or "temporarily unavailable" in message
        or "overloaded" in message
        or "deadline_exceeded" in message
        or "unavailable" in message
    )



def generate_gemini_reply(prompt: str) -> str:
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=1024,
            ),
        )

        text = (getattr(response, "text", None) or "").strip()

        if not text:
            raise RuntimeError("Gemini returned an empty response.")

        print(f"[GEMINI] Reply generated successfully.", flush=True)
        return text

    except Exception as exc:
        print(f"[GEMINI ERROR]: {exc!r}", flush=True)
        raise


def generate_openai_reply(message: str, student_context: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Asra's AI Tutor and personal learning assistant. "
                    "Answer clearly, briefly, and with examples when helpful. "
                    "Adapt to the student's background when known."
                ),
            },
            {
                "role": "user",
                "content": f"{student_context}\n\nUser's question: {message}",
            },
        ],
        "temperature": 0.3,
        "max_tokens": 250,
    }

    response = httpx.post(
        f"{OPENAI_API_BASE.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60.0,
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    return content.strip() if isinstance(content, str) else str(content)


RESUME_MAX_FILE_SIZE = 5 * 1024 * 1024
RESUME_ALLOWED_EXTENSIONS = {".pdf", ".docx"}
RESUME_SKILL_ALIASES = {
    "python": ["python", "py"],
    "javascript": ["javascript", "js"],
    "sql": ["sql", "postgresql", "mysql", "database querying"],
    "java": ["java"],
    "c++": ["c++", "cpp", "c plus plus"],
    "c#": ["c#", "c sharp", "csharp"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "react": ["react", "reactjs"],
    "node.js": ["node.js", "nodejs", "node js"],
    "git": ["git", "github"],
    "docker": ["docker", "containers"],
    "aws": ["aws", "amazon web services"],
    "machine learning": ["machine learning", "ml", "predictive modeling"],
    "data analysis": ["data analysis", "analytics", "data visualization"],
    "problem solving": ["problem solving", "troubleshooting"],
    "communication": ["communication", "stakeholder communication"],
    "project management": ["project management", "project planning"],
    "excel": ["excel", "spreadsheets"],
    "mongodb": ["mongodb", "mongo db"],
    "api development": ["api development", "rest api", "apis"],
}


def _normalize_text(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value or "")
    return normalized.lower().strip()


def _extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return "\n".join(pages)


def _extract_docx_text(file_bytes: bytes) -> str:
    document = Document(BytesIO(file_bytes))
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    return "\n".join(paragraphs)


def _generate_resume_docx_from_text(text: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = Document()
    cleaned_text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    blocks = [block.strip() for block in re.split(r"\n\s*\n+", cleaned_text)]

    for block in blocks:
        if not block:
            continue
        lines = [line.strip() for line in block.split("\n")]
        if not lines:
            continue

        heading = lines[0].strip()
        if heading.lower() in {"summary", "education", "experience", "skills", "projects", "certifications"}:
            document.add_heading(heading, level=1)

        for line in lines[1:]:
            if line:
                document.add_paragraph(line)

        if heading.lower() not in {"summary", "education", "experience", "skills", "projects", "certifications"}:
            for line in lines:
                if line:
                    document.add_paragraph(line)

    document.save(output_path)
    return output_path


def _get_resume_sections(text: str) -> list[str]:
    sections: list[str] = []
    text_lower = _normalize_text(text)
    checks = {
        "Skills": ["skills", "technical skills", "core competencies", "tools"],
        "Education": ["education", "degree", "university", "college", "qualification", "certification"],
        "Experience": ["experience", "work history", "employment", "professional experience", "internships", "roles"],
        "Projects": ["projects", "portfolio", "key projects"],
        "Certifications": ["certifications", "licenses"],
    }
    for name, needles in checks.items():
        if any(needle in text_lower for needle in needles):
            sections.append(name)
    return sections


def _find_resume_keywords(text: str, aliases: list[str]) -> list[str]:
    normalized = _normalize_text(text)
    matches: list[str] = []
    for alias in aliases:
        if alias in normalized:
            matches.append(alias)
    return matches


def _extract_skill_matches(resume_text: str, job_description: str) -> tuple[list[str], list[str]]:
    match_set: set[str] = set()
    missing_set: set[str] = set()
    text = _normalize_text(resume_text)
    job = _normalize_text(job_description)

    for skill_name, aliases in RESUME_SKILL_ALIASES.items():
        resume_hits = _find_resume_keywords(text, aliases)
        job_hits = _find_resume_keywords(job, aliases)

        if resume_hits and job_hits:
            match_set.add(skill_name)
        elif job_hits and not resume_hits:
            missing_set.add(skill_name)

    matched = sorted(match_set)
    missing = sorted(missing_set)
    return matched, missing


def _build_improvement_suggestions(missing_skills: list[str], resume_sections: list[str]) -> list[str]:
    suggestions: list[str] = []
    if missing_skills:
        suggestions.append(
            "Add the missing keywords to the skills section, project descriptions, and summary so recruiters can see them quickly."
        )
        suggestions.append(
            "For each missing skill, provide one concrete example from coursework, work, or a project that used it."
        )
    if "Experience" not in resume_sections:
        suggestions.append("Add a clear work experience or internship section with roles, responsibilities, and outcomes.")
    if "Education" not in resume_sections:
        suggestions.append("Include degree, university, graduation year, and relevant coursework or honors.")
    if "Projects" not in resume_sections:
        suggestions.append("Add 2-3 realistic project bullet points that connect your skills to business or technical outcomes.")
    if not suggestions:
        suggestions.append("Keep the resume concise and make the skill and project sections easy to scan for the target role.")
    return suggestions


def _analyze_resume_text(resume_text: str, job_description: str) -> dict[str, Any]:
    sections = _get_resume_sections(resume_text)
    matched_skills, missing_skills = _extract_skill_matches(resume_text, job_description)
    suggestions = _build_improvement_suggestions(missing_skills, sections)

    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "resume_sections": sections,
        "improvement_suggestions": suggestions,
        "estimated_match_note": "Skill matches are estimates based on text matching. They should be reviewed manually and are not a guarantee of qualification or score.",
        "resume_excerpt": resume_text[:600],
    }


def _estimate_ats_score(matched_skills: list[str], missing_skills: list[str], resume_sections: list[str]) -> int:
    matched_weight = max(0, len(matched_skills))
    missing_weight = max(0, len(missing_skills))
    section_bonus = 10 if "Skills" in resume_sections else 0
    section_bonus += 10 if "Experience" in resume_sections else 0
    section_bonus += 5 if "Education" in resume_sections else 0
    score = 40 + (matched_weight * 8) - (missing_weight * 5) + section_bonus
    if "Projects" in resume_sections:
        score += 5
    return max(20, min(99, round(score)))


INTERVIEW_QUESTION_BANK: list[dict[str, Any]] = [
    {
        "id": "ds-python-1",
        "role": "Data Scientist",
        "topic": "Python",
        "difficulty": "Beginner",
        "question": "How do you handle missing values in a pandas DataFrame before training a model?",
        "answer": "Use fillna(), dropna(), or isnull() to inspect and clean missing values before training.",
    },
    {
        "id": "ds-sql-1",
        "role": "Data Scientist",
        "topic": "SQL",
        "difficulty": "Intermediate",
        "question": "What is the difference between WHERE and HAVING in SQL?",
        "answer": "WHERE filters rows before aggregation, while HAVING filters grouped data after aggregation.",
    },
    {
        "id": "da-sql-1",
        "role": "Data Analyst",
        "topic": "SQL",
        "difficulty": "Beginner",
        "question": "Write a query to find the top 3 products by sales using ORDER BY and LIMIT.",
        "answer": "SELECT product, SUM(sales) AS total_sales FROM sales_data GROUP BY product ORDER BY total_sales DESC LIMIT 3;",
    },
    {
        "id": "py-dev-1",
        "role": "Python Developer",
        "topic": "Python",
        "difficulty": "Advanced",
        "question": "What are the benefits of using async/await in Python web services?",
        "answer": "It allows concurrent I/O-bound work without blocking threads, improving throughput and responsiveness.",
    },
    {
        "id": "ml-eng-1",
        "role": "ML Engineer",
        "topic": "Machine Learning",
        "difficulty": "Intermediate",
        "question": "Why is train/test split important when evaluating a model?",
        "answer": "It prevents overfitting by measuring model performance on data it has not seen during training.",
    },
    {
        "id": "ml-eng-2",
        "role": "ML Engineer",
        "topic": "Modeling",
        "difficulty": "Advanced",
        "question": "How do you choose between precision and recall as your primary metric?",
        "answer": "Use precision when false positives are costly and recall when missing a positive is more costly.",
    },
    {
        "id": "da-eda-1",
        "role": "Data Analyst",
        "topic": "Analytics",
        "difficulty": "Intermediate",
        "question": "How would you explain a sudden drop in conversion rates using SQL and dashboard trends?",
        "answer": "Segment by channel, date, and user cohort to isolate when the drop began and which variables explain it.",
    },
    {
        "id": "py-dev-2",
        "role": "Python Developer",
        "topic": "API Design",
        "difficulty": "Beginner",
        "question": "What is a REST API and why is it useful?",
        "answer": "A REST API exposes endpoints for resources so applications can communicate over HTTP in a consistent way.",
    },
    {
        "id": "ds-stat-1",
        "role": "Data Scientist",
        "topic": "Statistics",
        "difficulty": "Advanced",
        "question": "Why is feature scaling important in many machine learning workflows?",
        "answer": "Scaling helps algorithms that depend on distance or magnitude, making optimization more stable and fair.",
    },
]


ROADMAP_LIBRARY: dict[str, dict[str, Any]] = {
    "Data Scientist": {
        "skills": ["Python", "SQL", "Statistics", "Machine Learning", "Data Visualization"],
        "technologies": ["Python", "Pandas", "Scikit-learn", "SQL", "Tableau"],
        "projects": ["House price prediction", "Customer churn dashboard", "Forecasting project"],
        "milestones": [
            {"title": "Python and SQL foundation", "done": False},
            {"title": "Exploratory data analysis project", "done": False},
            {"title": "ML model and evaluation", "done": False},
            {"title": "Portfolio presentation", "done": False},
        ],
    },
    "Data Analyst": {
        "skills": ["Excel", "SQL", "Dashboarding", "Business Analysis", "Communication"],
        "technologies": ["Excel", "Power BI", "SQL", "Python"],
        "projects": ["Business KPI dashboard", "Retention analysis", "Marketing funnel report"],
        "milestones": [
            {"title": "SQL basics and joins", "done": False},
            {"title": "Dashboard project", "done": False},
            {"title": "Business insight storytelling", "done": False},
            {"title": "Portfolio review", "done": False},
        ],
    },
    "Python Developer": {
        "skills": ["Python", "API Design", "Testing", "Git", "Problem Solving"],
        "technologies": ["FastAPI", "PostgreSQL", "Git", "Docker"],
        "projects": ["REST API service", "Task scheduler", "Authentication mini-project"],
        "milestones": [
            {"title": "Core Python practice", "done": False},
            {"title": "REST API project", "done": False},
            {"title": "Testing and debugging", "done": False},
            {"title": "Deployment basics", "done": False},
        ],
    },
    "ML Engineer": {
        "skills": ["Python", "Machine Learning", "Model Evaluation", "MLOps", "Statistics"],
        "technologies": ["Python", "Scikit-learn", "Pandas", "MLflow", "Docker"],
        "projects": ["Model comparison study", "Deployment-ready pipeline", "A/B experiment analysis"],
        "milestones": [
            {"title": "Model fundamentals", "done": False},
            {"title": "Feature engineering project", "done": False},
            {"title": "Evaluation and bias check", "done": False},
            {"title": "Production-ready pipeline", "done": False},
        ],
    },
}


JOB_ROLE_CATALOG = [
    {
        "title": "Data Scientist",
                "company": "TCS",
                 "application_url": "https://www.tcs.com/careers",
        "family": "Data Science",
        "description": "Build statistical and machine-learning solutions that turn data into business insight.",
        "required_skills": ["python", "sql", "statistics", "machine learning", "data analysis", "communication"],
        "eligibility": "Strong fit for learners who combine Python, SQL, and analytical thinking with a clear communication style.",
        "next_steps": [
            "Strengthen Python and statistics foundations with a short project portfolio.",
            "Practice 1-2 end-to-end data analysis workflows using real datasets.",
            "Document decisions, metrics, and business impact clearly in your portfolio."
        ],
    },
    {
        "title": "Data Analyst",
                "company": "Accenture",
        "application_url": "https://www.accenture.com/in-en/careers",
        "family": "Data Analytics",
        "description": "Translate data into dashboards, reports, and practical business recommendations.",
        "required_skills": ["sql", "excel", "data analysis", "dashboarding", "communication", "python"],
        "eligibility": "A good match for candidates who can query data, explain trends, and present insights simply.",
        "next_steps": [
            "Create 2-3 dashboard projects using business datasets and KPI tracking.",
            "Practice SQL joins, aggregation, and summarization techniques.",
            "Write short business summaries to improve storytelling and stakeholder communication."
        ],
    },
    {
        "title": "Python Developer",
                "company": "Google",
        "application_url": "https://www.google.com/about/careers/applications/",
        "family": "Python Development",
        "description": "Build APIs, automation tools, and product features using Python-based workflows.",
        "required_skills": ["python", "api development", "sql", "git", "problem solving", "docker"],
        "eligibility": "Well suited for aspirants who can build clean, testable logic and work with backend tooling.",
        "next_steps": [
            "Build a small REST API project using FastAPI or Flask.",
            "Practice clean code structure, tests, and version control workflows.",
            "Add deployment basics such as Docker or a simple cloud setup."
        ],
    },
    {
        "title": "Machine Learning Engineer",
                "company": "Google",
        "application_url": "https://www.google.com/about/careers/applications/",
        "family": "Machine Learning",
        "description": "Design ML models, optimize experiments, and move models into production workflows.",
        "required_skills": ["python", "machine learning", "statistics", "data analysis", "sql", "model evaluation"],
        "eligibility": "Best aligned with people who already understand Python, statistics, and practical model evaluation.",
        "next_steps": [
            "Practice model selection, evaluation, and validation with realistic datasets.",
            "Build at least one supervised learning workflow and document its metrics.",
            "Focus on experiment tracking, bias checks, and deployment-ready pipelines."
        ],
    },
    {
        "title": "Generative AI Engineer",
                "company": "Microsoft",
        "application_url": "https://careers.microsoft.com/",
        "family": "Generative AI",
        "description": "Build applications that use prompts, model workflows, retrieval, and evaluation in AI systems.",
        "required_skills": ["python", "api development", "prompt engineering", "machine learning", "project management", "communication"],
        "eligibility": "A strong fit for learners who can combine software engineering with AI workflows and clear product thinking.",
        "next_steps": [
            "Build a small AI app that wraps an LLM with a backend API.",
            "Practice prompt design, evaluation, and retrieval workflows.",
            "Document reliability, safety, and improvement opportunities for each prototype."
        ],
    },
]


def _normalize_skill_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9+\s-]", "", (value or "").lower())
    return re.sub(r"\s+", " ", normalized).strip()


def _normalize_skill_list(values: Any) -> list[str]:
    raw_values: list[str] = []
    if isinstance(values, str):
        raw_values.extend(part.strip() for part in re.split(r"[,\n;]+", values) if part.strip())
    elif isinstance(values, list):
        raw_values.extend(str(item).strip() for item in values if str(item).strip())
    elif isinstance(values, dict):
        for item in values.values():
            raw_values.extend(_normalize_skill_list(item))

    normalized = []
    for item in raw_values:
        skill = _normalize_skill_name(item)
        if skill and skill not in normalized:
            normalized.append(skill)
    return normalized


def _extract_user_skills(payload: dict[str, Any]) -> list[str]:
    profile = payload.get("profile") or {}
    profile_skills = profile.get("skills") or {}
    skill_sources = [
        payload.get("key_skills", []),
        profile_skills.get("programming_languages", []),
        profile_skills.get("technical_skills", []),
        profile_skills.get("tools_technologies", []),
        profile_skills.get("soft_skills", []),
        (payload.get("resume_analysis") or {}).get("matched_skills", []),
    ]

    all_skills: list[str] = []
    for source in skill_sources:
        all_skills.extend(_normalize_skill_list(source))

    if payload.get("preferred_role"):
        all_skills.extend(_normalize_skill_list(payload.get("preferred_role")))

    return sorted(set(all_skills))


def _build_job_recommendation(role: dict[str, Any], user_skills: list[str], preferred_role: str | None) -> dict[str, Any]:
    required_skills = [_normalize_skill_name(skill) for skill in role["required_skills"]]
    matched_skills = [skill for skill in required_skills if skill in user_skills]
    missing_skills = [skill for skill in required_skills if skill not in user_skills]

    coverage = int((len(matched_skills) / len(required_skills)) * 100) if required_skills else 0
    if preferred_role:
        preferred_text = _normalize_skill_name(preferred_role)
        if preferred_text and preferred_text in _normalize_skill_name(role["title"]):
            coverage = min(98, coverage + 8)

    if not matched_skills and not missing_skills:
        coverage = 0

    reason_parts = []
    if matched_skills:
        reason_parts.append(f"Your background includes {', '.join(matched_skills[:3])}.")
    else:
        reason_parts.append("This role is a strong stretch target for your current experience profile.")

    if missing_skills:
        reason_parts.append(f"The biggest gaps are {', '.join(missing_skills[:3])}.")

   
    recommendation = {
        "title": role["title"],
        "family": role["family"],
        "score": max(30, min(98, coverage)),
        "match_reason": " ".join(reason_parts),
        "description": role["description"],
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "eligibility_guidance": role["eligibility"],
        "suggested_next_steps": role["next_steps"],
        "company": role.get("company", ""),
        "company_website": role.get("company_website", ""),
        "application_url": role.get("application_url", ""),
        "note": "These recommendations are based on skill matching. Check the application link for current vacancies."
    }

    return recommendation


app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobRecommendationRequest(BaseModel):
    user_id: str | None = None
    preferred_role: str | None = None
    experience_level: str | None = None
    location_preference: str | None = None
    key_skills: list[str] = Field(default_factory=list)
    resume_analysis: dict[str, Any] = Field(default_factory=dict)
    profile: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str
    user_id: str
    document_context: str | None = None

class LearningPlanSave(BaseModel):
    settings: dict[str, Any]
    weeks: list[dict[str, Any]]
    updatedAt: str | None = None


class StudyTaskCreate(BaseModel):
    task_id: str
    title: str
    deadline: str | None = None
    priority: str = "Medium"
    completed: bool = False


class StudyTaskUpdate(BaseModel):
    title: str | None = None
    deadline: str | None = None
    priority: str | None = None
    completed: bool | None = None


class QuizSubmission(BaseModel):
    user_id: str
    subject: str
    answers: list[str]


class InterviewBankProgress(BaseModel):
    user_id: str
    question_id: str
    role: str
    completed: bool = False
    saved: bool = False


class RoadmapPayload(BaseModel):
    target_role: str
    skills: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    milestones: list[dict[str, Any]] = Field(default_factory=list)


class NotePayload(BaseModel):
    note_id: str
    title: str
    content: str
    category: str = "General"
    updated_at: str | None = None


class AchievementAward(BaseModel):
    badge_id: str
    title: str
    description: str
    progress: int = 0
    total: int = 1


async def _award_achievements_for_user(user_id: str) -> list[dict[str, Any]]:
    tasks = await fetch_study_tasks(user_id)
    tests = await fetch_test_results(user_id)
    interviews = await fetch_interview_sessions(user_id)
    notes = await fetch_notes(user_id)
    earned = await fetch_achievements(user_id)
    earned_ids = {item.get("badge_id") for item in earned}

    award_list = [
        {
            "badge_id": "planner-pro",
            "title": "Planner Pro",
            "description": "Complete 3 study tasks.",
            "progress": sum(1 for task in tasks if task.get("completed")),
            "total": 3,
            "condition": sum(1 for task in tasks if task.get("completed")) >= 3,
        },
        {
            "badge_id": "practice-starter",
            "title": "Practice Starter",
            "description": "Complete your first technical quiz.",
            "progress": len(tests),
            "total": 1,
            "condition": len(tests) >= 1,
        },
        {
            "badge_id": "mock-ready",
            "title": "Mock Interview Ready",
            "description": "Complete 1 mock interview session.",
            "progress": len(interviews),
            "total": 1,
            "condition": len(interviews) >= 1,
        },
        {
            "badge_id": "notetaker",
            "title": "Notetaker",
            "description": "Save 3 personal notes.",
            "progress": len(notes),
            "total": 3,
            "condition": len(notes) >= 3,
        },
    ]

    for award in award_list:
        if award["condition"] and award["badge_id"] not in earned_ids:
            payload = {
                "badge_id": award["badge_id"],
                "title": award["title"],
                "description": award["description"],
                "progress": award["progress"],
                "total": award["total"],
                "awarded_at": datetime.now(timezone.utc).isoformat(),
            }
            await store_achievement(user_id, payload)
            earned.append(payload)

    return earned


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "app": APP_NAME}


@app.get("/api/users")
async def get_users():
    profiles = await fetch_all_profiles()
    return {"success": True, "count": len(profiles), "profiles": profiles}


@app.get("/api/users/{user_id}")
async def get_user_profile(user_id: str):
    profile = await fetch_profile_by_user_id(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return {"success": True, "profile": profile}


@app.post("/api/users/profile")
async def create_user_profile(
    profile: Annotated[str | None, Form()] = None,
    resume: UploadFile | None = File(default=None),
):
    if not profile:
        raise HTTPException(status_code=400, detail="Profile data is required.")

    try:
        raw_profile = json.loads(profile)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid profile JSON: {exc.msg}") from exc

    try:
        validated_profile = UserProfileCreate.model_validate(raw_profile)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Profile validation failed: {exc}") from exc

    collection = await get_users_collection()
    if collection is not None:
        try:
            existing_user = await collection.find_one({"personal_information.email": validated_profile.personal_information.email})
        except Exception:
            existing_user = None
        if existing_user is not None:
            raise HTTPException(status_code=409, detail="A profile with this email already exists.")

    user_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    resume_payload = validated_profile.resume_information
   
    if resume is not None:
        file_bytes = await resume.read()

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded resume is empty."
            )

        if len(file_bytes) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Resume size must not exceed 5 MB."
            )

        original_name = Path(resume.filename or "resume").name
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", original_name)

        upload_dir = Path(__file__).resolve().parent / "uploads" / user_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / safe_name
        file_path.write_bytes(file_bytes)

        resume_payload.uploaded = True
        resume_payload.file_name = original_name
        resume_payload.file_type = resume.content_type or "application/octet-stream"
        resume_payload.file_size_bytes = len(file_bytes)
        resume_payload.processed = False
        resume_payload.storage_path = str(file_path)


    profile_document = {
        "user_id": user_id,
        "personal_information": validated_profile.personal_information.model_dump(),
        "education": validated_profile.education.model_dump(),
        "career_information": validated_profile.career_information.model_dump(),
        "skills": validated_profile.skills.model_dump(),
        "career_goals": validated_profile.career_goals.model_dump(),
        "resume_information": resume_payload.model_dump(),
        "created_at": now,
        "updated_at": now,
    }

    await store_profile_document(profile_document)

    return JSONResponse(
        status_code=201,
        content={
            "success": True,
            "user_id": user_id,
            "message": "User profile created successfully.",
            "resume_uploaded": bool(resume),
        },
    )

@app.put("/api/users/{user_id}")
async def update_user_profile(
    user_id: str,
    profile: Annotated[str | None, Form()] = None,
    resume: UploadFile | None = File(default=None),
    remove_resume: Annotated[bool | None, Form()] = False,
):
    if not profile:
        raise HTTPException(status_code=400, detail="Profile data is required.")

    try:
        raw_profile = json.loads(profile)
        validated_profile = UserProfileCreate.model_validate(raw_profile)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid profile data: {exc}",
        ) from exc

    existing_profile = await fetch_profile_by_user_id(user_id)
    if existing_profile is None:
        raise HTTPException(status_code=404, detail="User profile not found.")

    collection = await get_users_collection()
    email = validated_profile.personal_information.email

    if collection is not None:
        duplicate = await collection.find_one({
            "personal_information.email": email,
            "user_id": {"$ne": user_id},
        })
        if duplicate is not None:
            raise HTTPException(
                status_code=409,
                detail="Another profile with this email already exists.",
            )

    now = datetime.now(timezone.utc).isoformat()

    from backend.models import ResumeInformation

    resume_payload = validated_profile.resume_information
    if not resume and not remove_resume:
        old_resume = existing_profile.get("resume_information")
        if old_resume:
            resume_payload = ResumeInformation.model_validate(old_resume)

    if remove_resume and not resume:
        old_resume = existing_profile.get("resume_information") or {}
        storage_path = old_resume.get("storage_path")
        if storage_path:
            try:
                Path(storage_path).unlink(missing_ok=True)
            except Exception:
                pass
        resume_payload = ResumeInformation(
            uploaded=False,
            file_name=None,
            file_type=None,
            file_size_bytes=None,
            processed=False,
            storage_path=None,
        )

    if resume is not None:
        file_bytes = await resume.read()

        if not file_bytes:
            raise HTTPException(status_code=400, detail="The uploaded resume is empty.")
        if len(file_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Resume size must not exceed 5 MB.")

        original_name = Path(resume.filename or "resume").name
        extension = Path(original_name).suffix.lower()
        if extension not in RESUME_ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Only PDF and DOCX resume files are supported.")

        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", original_name)
        upload_dir = Path(__file__).resolve().parent / "uploads" / user_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / safe_name
        file_path.write_bytes(file_bytes)

        resume_payload.uploaded = True
        resume_payload.file_name = original_name
        resume_payload.file_type = resume.content_type or "application/octet-stream"
        resume_payload.file_size_bytes = len(file_bytes)
        resume_payload.processed = False
        resume_payload.storage_path = str(file_path)

    updates = {
        "personal_information": validated_profile.personal_information.model_dump(),
        "education": validated_profile.education.model_dump(),
        "career_information": validated_profile.career_information.model_dump(),
        "skills": validated_profile.skills.model_dump(),
        "career_goals": validated_profile.career_goals.model_dump(),
        "resume_information": resume_payload.model_dump(),
        "updated_at": now,
    }

    updated_profile = await update_profile_document(user_id, updates)

    if updated_profile is None:
        raise HTTPException(status_code=404, detail="User profile not found.")

    return {
        "success": True,
        "user_id": user_id,
        "message": "User profile updated successfully.",
        "resume_uploaded": bool(resume),
    }


@app.get("/api/users/{user_id}/resume")
async def get_user_resume_text(user_id: str):
    profile = await fetch_profile_by_user_id(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User profile not found.")

    resume_info = profile.get("resume_information") or {}
    storage_path = resume_info.get("storage_path")
    if not storage_path:
        raise HTTPException(status_code=404, detail="No resume is stored for this user.")

    resume_file = Path(storage_path)
    if not resume_file.exists():
        raise HTTPException(status_code=404, detail="The stored resume file could not be found.")

    suffix = resume_file.suffix.lower()
    if suffix not in RESUME_ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="The stored resume file type is not supported.")

    try:
        file_bytes = resume_file.read_bytes()
        text = _extract_pdf_text(file_bytes) if suffix == ".pdf" else _extract_docx_text(file_bytes)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Unable to read the uploaded resume: {exc}") from exc

    if not text.strip():
        raise HTTPException(status_code=422, detail="The stored resume did not contain readable text.")

    return {
        "success": True,
        "filename": resume_info.get("file_name") or resume_file.name,
        "text": text,
    }


@app.get("/api/users/{user_id}/resume/download")
async def download_user_resume(user_id: str, file_name: str | None = None):
    profile = await fetch_profile_by_user_id(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User profile not found.")

    resume_info = profile.get("resume_information") or {}
    storage_path = resume_info.get("storage_path")
    if file_name:
        candidate = Path(__file__).resolve().parent / "uploads" / user_id / file_name
        if candidate.exists():
            storage_path = str(candidate)

    if not storage_path:
        raise HTTPException(status_code=404, detail="No downloadable resume is available for this user.")

    file_path = Path(storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="The resume file is missing from storage.")

    media_type = "application/pdf" if file_path.suffix.lower() == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(file_path, media_type=media_type, filename=file_path.name)


@app.post("/api/users/{user_id}/resume")
async def save_user_resume_text(user_id: str, resume_text: Annotated[str | None, Form()] = None):
    if resume_text is None or not resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text is required.")

    profile = await fetch_profile_by_user_id(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User profile not found.")

    upload_dir = Path(__file__).resolve().parent / "uploads" / user_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    output_name = f"resume_edited_{timestamp}.docx"
    output_path = upload_dir / output_name

    try:
        _generate_resume_docx_from_text(resume_text, output_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to generate the updated resume file: {exc}") from exc

    file_bytes = output_path.read_bytes() if output_path.exists() else b""
    if not file_bytes:
        raise HTTPException(status_code=500, detail="The generated resume file was empty.")

    resume_payload = {
        "uploaded": True,
        "file_name": output_name,
        "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "file_size_bytes": len(file_bytes),
        "processed": False,
        "storage_path": str(output_path),
    }

    updated_profile = await update_profile_document(
        user_id,
        {
            "resume_information": resume_payload,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    if updated_profile is None:
        try:
            output_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(status_code=404, detail="User profile not found while saving the edited resume.")

    return {
        "success": True,
        "message": "Resume saved successfully.",
        "filename": output_name,
        "download_url": f"http://127.0.0.1:8018/api/users/{user_id}/resume/download?file_name={output_name}",
    }


@app.post("/api/resume/analyze")
async def analyze_resume_upload(
    file: UploadFile = File(...),
    job_description: Annotated[str | None, Form()] = None,
):
    if not job_description or not job_description.strip():
        raise HTTPException(status_code=400, detail="A target job description is required.")

    filename = file.filename or "resume"
    extension = Path(filename).suffix.lower()
    if extension not in RESUME_ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX resume files are supported.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="The uploaded resume file is empty.")
    if len(file_bytes) > RESUME_MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Resume size must not exceed 5 MB.")

    try:
        text = _extract_pdf_text(file_bytes) if extension == ".pdf" else _extract_docx_text(file_bytes)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Unable to read the resume file: {exc}") from exc

    if not text.strip():
        raise HTTPException(status_code=422, detail="The uploaded resume did not contain readable text.")

    analysis = _analyze_resume_text(text, job_description)
    return {
        "success": True,
        "filename": filename,
        "file_type": extension,
        "estimated_match_note": analysis["estimated_match_note"],
        "matched_skills": analysis["matched_skills"],
        "missing_skills": analysis["missing_skills"],
        "resume_sections": analysis["resume_sections"],
        "improvement_suggestions": analysis["improvement_suggestions"],
        "resume_excerpt": analysis["resume_excerpt"],
    }


@app.post("/api/jobs/recommendations")
async def get_job_recommendations(payload: JobRecommendationRequest):
    if not payload.preferred_role and not payload.key_skills and not payload.profile and not payload.user_id:
        raise HTTPException(status_code=400, detail="Provide a preferred role, key skills, or user profile context for job recommendations.")

    profile_context: dict[str, Any] = {}
    if payload.user_id:
        profile_context = await fetch_profile_by_user_id(payload.user_id) or {}
    if not profile_context and payload.profile:
        profile_context = payload.profile

    user_skills = _extract_user_skills({
        "key_skills": payload.key_skills,
        "preferred_role": payload.preferred_role,
        "profile": profile_context,
        "resume_analysis": payload.resume_analysis,
    })

    if not user_skills and profile_context:
        profile_skills = profile_context.get("skills") or {}
        for section in profile_skills.values():
            user_skills.extend(_normalize_skill_list(section))
        user_skills = sorted(set(user_skills))

    if not user_skills:
        user_skills = ["python", "sql", "communication", "project management"]

    preferred_role = payload.preferred_role or profile_context.get("career_information", {}).get("target_job_role") or "Data Analyst"
    recommendations = [
        _build_job_recommendation(role, user_skills, preferred_role)
        for role in JOB_ROLE_CATALOG
    ]
    recommendations.sort(key=lambda item: item["score"], reverse=True)

    return {
        "success": True,
        "preferred_role": preferred_role,
        "experience_level": payload.experience_level or profile_context.get("career_information", {}).get("experience_level") or "Not specified",
        "location_preference": payload.location_preference or profile_context.get("career_information", {}).get("preferred_work_location") or "Flexible",
        "recommendations": recommendations,
        "note": "These recommendations are role fit estimates based on skills and experience context. They do not confirm live vacancies or employer hiring status.",
    }


@app.post("/api/tutor/upload-pdf")
async def upload_tutor_pdf(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name

    if Path(filename).suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="The PDF is empty.")

    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="PDF size must not exceed 5 MB.")

    try:
        text = _extract_pdf_text(file_bytes)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Could not read this PDF. Please check that it is a valid PDF."
        ) from exc

    text = text.strip()

    if not text:
        raise HTTPException(
            status_code=422,
            detail="No readable text found. Scanned PDFs need OCR and are not supported yet."
        )

    return {
        "success": True,
        "filename": filename,
        "text": text[:30000],
        "truncated": len(text) > 30000
    }


@app.post("/api/chat")
async def chat_with_tutor(request: ChatRequest):
    try:
        start_profile = time.perf_counter()
        profile = await fetch_profile_by_user_id(request.user_id)

        print(
            f"[CHAT-TIMER] Profile lookup: "
            f"{time.perf_counter() - start_profile:.3f}s",
            flush=True,
        )

        if profile:
            personal = profile.get("personal_information") or {}
            education = profile.get("education") or {}
            career = profile.get("career_information") or {}
            skills = profile.get("skills") or {}
            goals = profile.get("career_goals") or {}

            student_context = (
                "Student summary: "
                f"name={personal.get('full_name') or personal.get('preferred_name') or 'Unknown'}; "
                f"education={education.get('highest_education_level') or 'not specified'}; "
                f"degree={education.get('degree_course') or 'not specified'}; "
                f"target_role={career.get('target_job_role') or 'not specified'}; "
                f"industry={career.get('preferred_industry') or 'not specified'}; "
                f"skills={', '.join((skills.get('programming_languages') or []) + (skills.get('technical_skills') or [])[:10]) or 'not specified'}; "
                f"goals={goals.get('short_term_career_goal') or 'not specified'}; "
                "Use this context when relevant."
            )
        else:
            student_context = (
                "The user has not created a profile yet. "
                "Answer helpfully without requiring one."
            )

        document_context = getattr(request, "document_context", None)

        prompt = (
            "You are Asra's AI Tutor and personal learning assistant. "
            "Answer clearly, briefly, and with examples when helpful. "
            "Adapt to the student's background when known.\n\n"
            f"{student_context}\n\n"
        )

        if document_context:
            prompt += (
                "The user uploaded study material. Use it as the main source "
                "when answering questions about that material. If the answer "
                "is not in the document, say so clearly.\n"
                "Document content:\n"
                f"{document_context[:30000]}\n\n"
            )

        prompt += f"User's question: {request.message}"

        start_gemini = time.perf_counter()
        try:
            reply = generate_gemini_reply(prompt)
        except Exception as exc:
            print("[GEMINI/CHAT ERROR]:", repr(exc), flush=True)
            raise HTTPException(
                status_code=502,
                detail="Gemini could not generate a reply. Check the backend terminal.",
            ) from exc

        print(
            f"[CHAT-TIMER] Gemini response: "
            f"{time.perf_counter() - start_gemini:.3f}s",
            flush=True,
        )

        await store_chat_message(
            user_id=request.user_id,
            message=request.message,
            reply=reply,
        )

        return {"reply": reply}

    except HTTPException:
        raise
    except Exception as exc:
        print("[CHAT/UNKNOWN ERROR]:", repr(exc), flush=True)
        raise HTTPException(
            status_code=500,
            detail="The AI Tutor could not respond or save the conversation.",
        ) from exc


@app.get("/api/chat/{user_id}")
async def get_chat_history(user_id: str):
    history = await fetch_chat_history(user_id)
    return {"history": history}


class PracticeTestSubmission(BaseModel):
    user_id: str
    subject: str
    answers: list[str]


class InterviewSessionCreate(BaseModel):
    user_id: str
    role: str
    difficulty: str
    interview_type: str
    answers: list[dict[str, str]]
    score: int = Field(ge=0, le=100)
    total_questions: int = Field(ge=1)



@app.get("/api/tests/questions")
async def get_test_questions(subject: str | None = None):
    try:
        if subject:
            normalized = normalize_subject(subject)
            if normalized is None:
                raise ValueError(f"Unknown subject: {subject}")
            return {"success": True, "subject": normalized, "questions": QUESTION_BANK[normalized]}
        return {"success": True, "subjects": SUBJECTS, "questions": QUESTION_BANK}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/tests/performance/{user_id}")
async def get_test_performance(user_id: str):
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="A user_id is required.")

    attempts = await fetch_test_results(user_id)
    if not attempts:
        return {
            "success": True,
            "user_id": user_id,
            "completed_tests": 0,
            "average_score": 0,
            "best_score": 0,
            "subject_summary": {},
            "history": [],
        }

    percentages = [int(item.get("percentage", 0)) for item in attempts]
    subject_summary: dict[str, dict[str, Any]] = {}
    for item in attempts:
        subject = item.get("subject", "Unknown")
        subject_summary.setdefault(subject, {"attempts": 0, "scores": []})
        subject_summary[subject]["attempts"] += 1
        subject_summary[subject]["scores"].append(int(item.get("percentage", 0)))

    for subject, data in subject_summary.items():
        scores = data["scores"]
        data["average_score"] = round(sum(scores) / len(scores)) if scores else 0
        data["best_score"] = max(scores) if scores else 0
        data["last_attempt"] = max(item.get("submitted_at", "") for item in attempts if item.get("subject") == subject) if scores else None
        data.pop("scores", None)

    return {
        "success": True,
        "user_id": user_id,
        "completed_tests": len(attempts),
        "average_score": round(sum(percentages) / len(percentages)),
        "best_score": max(percentages),
        "subject_summary": subject_summary,
        "history": attempts,
    }


@app.post("/api/tests/submit")
async def submit_test(payload: PracticeTestSubmission):
    if not payload.user_id or not payload.user_id.strip():
        raise HTTPException(status_code=400, detail="A user_id is required to save the test result.")

    normalized_subject = normalize_subject(payload.subject)
    if normalized_subject is None:
        raise HTTPException(status_code=400, detail=f"Unsupported subject: {payload.subject}")

    if not isinstance(payload.answers, list):
        raise HTTPException(status_code=400, detail="Answers must be provided as a list.")

    try:
        result = evaluate_answers(normalized_subject, payload.answers)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    saved_result = await store_test_result(
        user_id=payload.user_id,
        subject=normalized_subject,
        score=result["score"],
        total_questions=result["total_questions"],
        percentage=result["percentage"],
        review=result["review"],
    )

    await _award_achievements_for_user(payload.user_id)

    return {
        "success": True,
        "user_id": payload.user_id,
        "subject": normalized_subject,
        "score": result["score"],
        "total_questions": result["total_questions"],
        "percentage": result["percentage"],
        "review": result["review"],
        "attempt_id": saved_result.get("_id"),
        "message": "Test submitted and saved successfully.",
    }


@app.get("/api/technical-quiz/questions")
async def get_technical_quiz_questions(subject: str | None = None):
    if subject:
        normalized = normalize_subject(subject)
        if normalized is None:
            raise HTTPException(status_code=400, detail=f"Unsupported subject: {subject}")
        return {"success": True, "subject": normalized, "questions": QUESTION_BANK[normalized]}
    return {"success": True, "subjects": SUBJECTS, "questions": QUESTION_BANK}


@app.post("/api/technical-quiz/submit")
async def submit_technical_quiz(payload: QuizSubmission):
    if not payload.user_id or not payload.user_id.strip():
        raise HTTPException(status_code=400, detail="A user_id is required.")
    return await submit_test(payload)


@app.post("/api/interviews")
async def save_interview(payload: InterviewSessionCreate):
    user_id = payload.user_id.strip()

    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="A user_id is required to save the interview.",
        )

    if len(payload.answers) != payload.total_questions:
        raise HTTPException(
            status_code=400,
            detail="The number of answers must match total_questions.",
        )

    saved_session = await store_interview_session(
        user_id=user_id,
        session_data={
            "role": payload.role,
            "difficulty": payload.difficulty,
            "interview_type": payload.interview_type,
            "answers": payload.answers,
            "score": payload.score,
            "total_questions": payload.total_questions,
        },
    )

    await _award_achievements_for_user(user_id)

    return {
        "success": True,
        "user_id": user_id,
        "interview_id": saved_session.get("_id"),
        "message": "Interview session saved successfully.",
    }


@app.get("/api/interview-bank/questions")
async def get_interview_question_bank(role: str | None = None, difficulty: str | None = None):
    questions = INTERVIEW_QUESTION_BANK
    if role:
        questions = [item for item in questions if item.get("role", "").lower() == role.lower()]
    if difficulty:
        questions = [item for item in questions if item.get("difficulty", "").lower() == difficulty.lower()]
    return {"success": True, "roles": sorted({item["role"] for item in INTERVIEW_QUESTION_BANK}), "difficulty_levels": ["Beginner", "Intermediate", "Advanced"], "questions": questions}


@app.get("/api/interview-bank/{user_id}")
async def get_interview_bank_progress(user_id: str):
    progress = await fetch_interview_bank_progress(user_id)
    return {"success": True, "user_id": user_id, "progress": progress}


@app.post("/api/interview-bank/{user_id}/progress")
async def save_interview_bank_progress(user_id: str, payload: InterviewBankProgress):
    if payload.user_id != user_id:
        raise HTTPException(status_code=400, detail="The payload user_id must match the route user_id.")
    saved = await upsert_interview_bank_progress(user_id, {"question_id": payload.question_id, "role": payload.role, "completed": payload.completed, "saved": payload.saved})
    return {"success": True, "user_id": user_id, "entry": saved}


@app.get("/api/interviews/{user_id}")
async def get_interview_history(user_id: str):
    user_id = user_id.strip()

    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="A user_id is required.",
        )

    history = await fetch_interview_sessions(user_id)

    return {
        "success": True,
        "user_id": user_id,
        "total_interviews": len(history),
        "history": history,
    }



@app.get("/api/learning/{user_id}")
async def get_learning_plan(user_id: str):
    collection = await get_learning_plans_collection()

    if collection is None:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable."
        )

    document = await collection.find_one({"user_id": user_id})

    if document is None:
        return {"plan": None}

    document.pop("_id", None)
    return {"plan": document}


@app.get("/api/roadmaps/{user_id}")
async def get_user_roadmaps(user_id: str):
    roadmaps = await fetch_roadmaps(user_id)
    return {"success": True, "user_id": user_id, "roadmaps": roadmaps}


@app.post("/api/roadmaps/{user_id}")
async def create_user_roadmap(user_id: str, payload: RoadmapPayload):
    roadmap = ROADMAP_LIBRARY.get(payload.target_role, {
        "skills": payload.skills or ["Python", "SQL"],
        "technologies": payload.technologies or ["Python", "MongoDB"],
        "projects": payload.projects or ["Portfolio project"],
        "milestones": payload.milestones or [{"title": "Build your starter project", "done": False}],
    })

    final_payload = {
        "roadmap_id": f"roadmap-{uuid4().hex[:8]}",
        "target_role": payload.target_role,
        "skills": payload.skills or roadmap["skills"],
        "technologies": payload.technologies or roadmap["technologies"],
        "projects": payload.projects or roadmap["projects"],
        "milestones": payload.milestones or roadmap["milestones"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    saved = await store_roadmap(user_id, final_payload)
    return {"success": True, "user_id": user_id, "roadmap": saved}


@app.patch("/api/roadmaps/{user_id}/milestones")
async def update_roadmap_milestone(user_id: str, roadmap_id: str = None, milestone_index: int | None = None, done: bool = False):
    if roadmap_id is None or milestone_index is None:
        raise HTTPException(status_code=400, detail="roadmap_id and milestone_index are required.")
    roadmaps = await fetch_roadmaps(user_id)
    target = next((item for item in roadmaps if item.get("roadmap_id") == roadmap_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Roadmap not found.")
    milestones = list(target.get("milestones", []))
    if milestone_index < 0 or milestone_index >= len(milestones):
        raise HTTPException(status_code=400, detail="milestone_index is out of range.")
    milestones[milestone_index]["done"] = done
    updated = await update_roadmap(user_id, roadmap_id, {"milestones": milestones, "updated_at": datetime.now(timezone.utc).isoformat()})
    return {"success": True, "user_id": user_id, "roadmap": updated}


@app.put("/api/learning/{user_id}")
async def save_learning_plan(user_id: str, plan: LearningPlanSave):
    collection = await get_learning_plans_collection()

    if collection is None:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable."
        )

    plan_data = plan.model_dump()
    plan_data["user_id"] = user_id
    plan_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    await collection.update_one(
        {"user_id": user_id},
        {"$set": plan_data},
        upsert=True
    )

    return {"message": "Learning plan saved successfully."}

from pydantic import BaseModel


class JobApplicationCreate(BaseModel):
    user_id: str
    role: str
    company: str
    location: str = ""
    status: str = "Interested"



@app.get("/api/study-planner/{user_id}")
async def get_study_tasks(user_id: str):
    tasks = await fetch_study_tasks(user_id)
    completed_count = sum(1 for item in tasks if item.get("completed"))
    total = len(tasks)
    completion_percent = round((completed_count / total) * 100) if total else 0
    return {"success": True, "user_id": user_id, "tasks": tasks, "completion_percent": completion_percent, "completed_count": completed_count, "total_tasks": total}


@app.post("/api/study-planner/{user_id}")
async def create_study_task(user_id: str, payload: StudyTaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="A task title is required.")

    task = {
        "task_id": payload.task_id or f"task-{uuid4().hex[:8]}",
        "title": payload.title.strip(),
        "deadline": payload.deadline,
        "priority": payload.priority,
        "completed": payload.completed,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    saved = await store_study_task(user_id, task)
    await _award_achievements_for_user(user_id)
    return {"success": True, "user_id": user_id, "task": saved}


@app.patch("/api/study-planner/{user_id}/{task_id}")
async def update_study_task_status(user_id: str, task_id: str, payload: StudyTaskUpdate):
    updates = {key: value for key, value in payload.model_dump(exclude_none=True).items()}
    if not updates:
        raise HTTPException(status_code=400, detail="At least one field must be updated.")
    updated = await update_study_task(user_id, task_id, updates)
    if updated is None:
        raise HTTPException(status_code=404, detail="Study task not found.")
    await _award_achievements_for_user(user_id)
    return {"success": True, "user_id": user_id, "task": updated}


@app.delete("/api/study-planner/{user_id}/{task_id}")
async def delete_study_task_status(user_id: str, task_id: str):
    deleted = await delete_study_task(user_id, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Study task not found.")
    await _award_achievements_for_user(user_id)
    return {"success": True, "user_id": user_id, "message": "Task deleted successfully."}


@app.get("/api/notes/{user_id}")
async def get_user_notes(user_id: str):
    notes = await fetch_notes(user_id)
    return {"success": True, "user_id": user_id, "notes": notes}


@app.post("/api/notes/{user_id}")
async def create_user_note(user_id: str, payload: NotePayload):
    if not payload.title.strip() or not payload.content.strip():
        raise HTTPException(status_code=400, detail="Note title and content are required.")
    note = {
        "note_id": payload.note_id or f"note-{uuid4().hex[:8]}",
        "title": payload.title.strip(),
        "content": payload.content.strip(),
        "category": payload.category,
        "updated_at": payload.updated_at or datetime.now(timezone.utc).isoformat(),
    }
    saved = await store_note(user_id, note)
    await _award_achievements_for_user(user_id)
    return {"success": True, "user_id": user_id, "note": saved}


@app.put("/api/notes/{user_id}/{note_id}")
async def update_user_note(user_id: str, note_id: str, payload: NotePayload):
    updates = {
        "title": payload.title.strip(),
        "content": payload.content.strip(),
        "category": payload.category,
        "updated_at": payload.updated_at or datetime.now(timezone.utc).isoformat(),
    }
    updated = await update_note(user_id, note_id, updates)
    if updated is None:
        raise HTTPException(status_code=404, detail="Note not found.")
    return {"success": True, "user_id": user_id, "note": updated}


@app.delete("/api/notes/{user_id}/{note_id}")
async def delete_user_note(user_id: str, note_id: str):
    deleted = await delete_note(user_id, note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found.")
    await _award_achievements_for_user(user_id)
    return {"success": True, "user_id": user_id, "message": "Note deleted successfully."}


@app.get("/api/achievements/{user_id}")
async def get_user_achievements(user_id: str):
    earned = await _award_achievements_for_user(user_id)
    return {"success": True, "user_id": user_id, "achievements": earned, "count": len(earned)}


@app.post("/api/ats/check")
async def check_ats_score(
    user_id: str | None = Form(default=None),
    job_description: Annotated[str | None, Form()] = None,
    resume_text: Annotated[str | None, Form()] = None,
    file: UploadFile | None = File(default=None),
):
    if not job_description or not job_description.strip():
        raise HTTPException(status_code=400, detail="A job description is required.")

    text = resume_text.strip() if resume_text else ""
    if file is not None:
        if file.filename and Path(file.filename).suffix.lower() not in RESUME_ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Only PDF and DOCX resume files are supported.")
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="The uploaded resume file is empty.")
        extension = Path(file.filename or "resume").suffix.lower()
        text = _extract_pdf_text(content) if extension == ".pdf" else _extract_docx_text(content)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Please upload a resume file or provide resume text.")

    analysis = _analyze_resume_text(text, job_description)
    estimated_score = _estimate_ats_score(analysis["matched_skills"], analysis["missing_skills"], analysis["resume_sections"])
    return {
        "success": True,
        "user_id": user_id,
        "estimated_score": estimated_score,
        "matched_skills": analysis["matched_skills"],
        "missing_skills": analysis["missing_skills"],
        "resume_sections": analysis["resume_sections"],
        "improvement_suggestions": analysis["improvement_suggestions"],
        "resume_excerpt": analysis["resume_excerpt"],
        "estimated_match_note": analysis["estimated_match_note"],
    }


@app.post("/api/job-applications")
async def create_job_application(payload: JobApplicationCreate):
    user_id = payload.user_id.strip()

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required.")

    allowed_statuses = {
        "Interested", "Applied", "Interview", "Offered", "Rejected"
    }

    if payload.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid application status.")

    # Check existing applications for this user.
    existing_applications = await fetch_job_applications(user_id)

    for application in existing_applications:
        same_role = (
            application.get("role", "").strip().casefold()
            == payload.role.strip().casefold()
        )
        same_company = (
            application.get("company", "").strip().casefold()
            == payload.company.strip().casefold()
        )

        if same_role and same_company:
            return {
                "success": True,
                "duplicate": True,
                "message": "This job is already in your tracker.",
                "application": application,
            }

    saved = await store_job_application(
        user_id,
        {
            "role": payload.role,
            "company": payload.company,
            "location": payload.location,
            "status": payload.status,
        },
    )

    return {
        "success": True,
        "duplicate": False,
        "message": "Application saved successfully.",
        "application": saved,
    }


@app.get("/api/job-applications/{user_id}")
async def list_job_applications(user_id: str):
    user_id = user_id.strip()

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required.")

    applications = await fetch_job_applications(user_id)

    return {
        "success": True,
        "applications": applications,
        "total": len(applications),
    }


class JobApplicationStatusUpdate(BaseModel):
    user_id: str
    created_at: str
    status: str


@app.patch("/api/job-applications/status")
async def change_job_application_status(
    payload: JobApplicationStatusUpdate,
):
    user_id = payload.user_id.strip()

    allowed_statuses = {
        "Interested", "Applied", "Interview", "Offered", "Rejected"
    }

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required.")

    if payload.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid application status.")

    updated = await update_job_application_status(
        user_id,
        payload.created_at,
        payload.status,
    )

    if updated is None:
        raise HTTPException(status_code=404, detail="Application not found.")

    return {"success": True, "application": updated}
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app.mount(
    "/",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="frontend",
)





