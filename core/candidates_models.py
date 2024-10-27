from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from core.database import Base
from core.job_description_model import JobDescription  # Importáld a JobDescription modellt


# Candidate model to store basic information about the candidate
class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String, index=True, nullable=False)
    phone_number = Column(String(50), nullable=True)
    location = Column(Text, nullable=True)
    linkedin_url = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)

    # Kapcsolatok más táblákkal
    educations = relationship("Education", back_populates="candidate", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="candidate", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="candidate", cascade="all, delete-orphan")
    languages = relationship("Language", back_populates="candidate", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="candidate", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="candidate", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="candidate", cascade="all, delete-orphan")

    # Használj szöveges hivatkozást a relationship-ben
    industries = relationship("CandidateIndustryCache", back_populates="candidate", cascade="all, delete-orphan")
class Education(Base):
    __tablename__ = "educations"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    degree = Column(Text, nullable=False)  # Degree title (e.g., Bachelor of Science)
    field_of_study = Column(Text, nullable=True)  # Subject (e.g., Computer Science)
    institution = Column(Text, nullable=False)  # Name of the institution
    start_date = Column(Date, nullable=True)  # Start date of the education
    end_date = Column(Date, nullable=True)  # End date of the education
    description = Column(Text, nullable=True)  # Additional details

    candidate = relationship("Candidate", back_populates="educations")


# Experience model to store work experience
class Experience(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    job_title = Column(Text, nullable=False)  # Job title (e.g., Senior Developer)
    company = Column(Text, nullable=True)  # Company name
    location = Column(Text, nullable=True)  # Job location
    start_date = Column(Date, nullable=True)  # Start date of employment
    end_date = Column(Date, nullable=True)  # End date of employment
    description = Column(Text, nullable=True)  # Job responsibilities and achievements

    candidate = relationship("Candidate", back_populates="experiences")


# Skill model to store individual skills and their proficiency
class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    skill_name = Column(Text, nullable=False)  # Name of the skill (e.g., Python)
    skill_level = Column(String(50), nullable=True)  # Level of proficiency (e.g., Expert)

    candidate = relationship("Candidate", back_populates="skills")


# Language model to store languages spoken by the candidate
class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    language = Column(Text, nullable=False)  # Language (e.g., English)
    proficiency = Column(String(50), nullable=True)  # Level of proficiency (e.g., Fluent)

    candidate = relationship("Candidate", back_populates="languages")

from sqlalchemy import Column, Integer, String, Float, LargeBinary, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from core.database import Base

# Szöveg és vektorok cache-elésére szolgáló tábla
# Szöveg és vektorok cache-elésére szolgáló tábla
class TextVectorCache(Base):
    __tablename__ = 'text_vector_cache'

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, unique=True, index=True)
    vector = Column(LargeBinary)  # A vektort bináris formában tároljuk

# Jelölt iparági tapasztalatainak cache-elésére szolgáló tábla
class CandidateIndustryCache(Base):
    __tablename__ = 'candidate_industry_cache'

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), index=True)
    industry_name = Column(String, index=True)

    # Használj szöveges hivatkozást a relationship-ben
    candidate = relationship("Candidate", back_populates="industries")
class CandidateJobScore(Base):
    __tablename__ = 'candidate_job_score'

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), index=True)
    job_id = Column(Integer, ForeignKey('job_descriptions.id'), index=True)
    industry_score = Column(Float, nullable=False)
    technical_score = Column(Float, nullable=False)
    job_matching_score = Column(Float, nullable=False)
    final_score = Column(Float, nullable=False)

    __table_args__ = (UniqueConstraint('candidate_id', 'job_id', name='unique_candidate_job'),)

    # Használj szöveges hivatkozást
    candidate = relationship("Candidate")
    job_description = relationship("JobDescription")
class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    certificate_name = Column(Text, nullable=False)  # Certification title (e.g., AWS Certified)
    issuing_organization = Column(Text, nullable=True)  # Organization that issued the certificate
    issue_date = Column(Date, nullable=True)  # Date of issue
    expiration_date = Column(Date, nullable=True)  # Expiration date (if any)
    certificate_url = Column(Text, nullable=True)  # URL to the certification (if applicable)

    candidate = relationship("Candidate", back_populates="certificates")


# Project model to store project details handled by the candidate
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    project_name = Column(Text, nullable=False)  # Name of the project
    description = Column(Text, nullable=True)  # Project details
    start_date = Column(Date, nullable=True)  # Start date of the project
    end_date = Column(Date, nullable=True)  # End date of the project
    url = Column(Text, nullable=True)  # Link to the project (if any)

    candidate = relationship("Candidate", back_populates="projects")


# Attachment model to store file attachments (like CV files)
class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    file_name = Column(Text, nullable=False)  # Name of the attached file
    file_path = Column(Text, nullable=False)  # Path to the file location
    upload_date = Column(Date, nullable=True)  # Date of file upload

    candidate = relationship("Candidate", back_populates="attachments")

def create_candidate(db: Session, first_name: str, last_name: str, email: str, phone_number: str = None, location: str = None, linkedin_url: str = None, summary: str = None) -> Candidate:
    try:
        candidate = Candidate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            location=location,
            linkedin_url=linkedin_url,
            summary=summary
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        print(f"Successfully created candidate: {first_name} {last_name} - {email}")
        return candidate
    except Exception as e:
        db.rollback()
        print(f"Error creating candidate {first_name} {last_name}: {e}")
        return None



def add_education(db: Session, candidate_id: int, degree: str, institution: str, start_date=None, end_date=None, description=None, field_of_study=None):
    education = Education(
        candidate_id=candidate_id,
        degree=degree,
        field_of_study=field_of_study,
        institution=institution,
        start_date=start_date,
        end_date=end_date,
        description=description
    )
    db.add(education)
    db.commit()


def add_experience(db: Session, candidate_id: int, job_title: str, company: str, start_date=None, end_date=None, location=None, description=None):
    experience = Experience(
        candidate_id=candidate_id,
        job_title=job_title,
        company=company,
        start_date=start_date,
        end_date=end_date,
        location=location,
        description=description
    )
    db.add(experience)
    db.commit()


def add_skill(db: Session, candidate_id: int, skill_name: str, skill_level=None):
    skill = Skill(
        candidate_id=candidate_id,
        skill_name=skill_name,
        skill_level=skill_level
    )
    db.add(skill)
    db.commit()


def add_language(db: Session, candidate_id: int, language: str, proficiency=None):
    language = Language(
        candidate_id=candidate_id,
        language=language,
        proficiency=proficiency
    )
    db.add(language)
    db.commit()


def add_certificate(db: Session, candidate_id: int, certificate_name: str, issuing_organization=None, issue_date=None, expiration_date=None, certificate_url=None):
    certificate = Certificate(
        candidate_id=candidate_id,
        certificate_name=certificate_name,
        issuing_organization=issuing_organization,
        issue_date=issue_date,
        expiration_date=expiration_date,
        certificate_url=certificate_url
    )
    db.add(certificate)
    db.commit()


def add_project(db: Session, candidate_id: int, project_name: str, description=None, start_date=None, end_date=None, url=None):
    project = Project(
        candidate_id=candidate_id,
        project_name=project_name,
        description=description,
        start_date=start_date,
        end_date=end_date,
        url=url
    )
    db.add(project)
    db.commit()


def add_attachment(db: Session, candidate_id: int, file_name: str, file_path: str, upload_date=None):
    attachment = Attachment(
        candidate_id=candidate_id,
        file_name=file_name,
        file_path=file_path,
        upload_date=upload_date
    )
    db.add(attachment)
    db.commit()

if __name__ == "__Main__":
    pass