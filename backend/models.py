from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PersonalInformation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(..., min_length=2)
    preferred_name: str = Field(..., min_length=1)
    email: str
    phone_number: str = Field(..., min_length=7)
    date_of_birth: str
    gender: str
    current_city: str
    country: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("Email must contain an @ symbol.")
        return value.strip()


class Education(BaseModel):
    model_config = ConfigDict(extra="forbid")

    highest_education_level: str
    degree_course: str
    specialization_branch: str
    college_university: str
    graduation_year: str
    current_education_status: str


class CareerInformation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_status: str
    target_job_role: str
    preferred_industry: str
    preferred_work_location: str
    experience_level: str
    current_company: Optional[str] = None
    current_job_role: Optional[str] = None


class Skills(BaseModel):
    model_config = ConfigDict(extra="forbid")

    programming_languages: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    tools_technologies: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)


class CareerGoals(BaseModel):
    model_config = ConfigDict(extra="forbid")

    short_term_career_goal: str
    long_term_career_goal: str
    target_role: str
    target_companies: list[str] = Field(default_factory=list)
    areas_to_improve: list[str] = Field(default_factory=list)
    preferred_learning_style: list[str] = Field(default_factory=list)


class ResumeInformation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    uploaded: bool = False
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    processed: bool = False
    storage_path: Optional[str] = None


class UserProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    personal_information: PersonalInformation
    education: Education
    career_information: CareerInformation
    skills: Skills
    career_goals: CareerGoals
    resume_information: ResumeInformation = Field(default_factory=ResumeInformation)
