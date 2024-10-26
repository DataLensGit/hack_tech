from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from core.database import Base

# Candidate modell
class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)

    # Kapcsolat az oktatással, tapasztalattal, készségekkel stb.
    educations = relationship("Education", back_populates="candidate", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="candidate", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="candidate", cascade="all, delete-orphan")
    languages = relationship("Language", back_populates="candidate", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="candidate", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="candidate", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="candidate", cascade="all, delete-orphan")


# Education modell
class Education(Base):
    __tablename__ = "educations"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    degree = Column(String(255), nullable=False)
    field_of_study = Column(String(255), nullable=True)
    institution = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)

    candidate = relationship("Candidate", back_populates="educations")


# Experience modell
class Experience(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    job_title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)

    candidate = relationship("Candidate", back_populates="experiences")


# Skill modell
class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    skill_name = Column(String(255), nullable=False)
    skill_level = Column(String(50), nullable=True)

    candidate = relationship("Candidate", back_populates="skills")


# Language modell
class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    language = Column(String(255), nullable=False)
    proficiency = Column(String(50), nullable=True)

    candidate = relationship("Candidate", back_populates="languages")


# Certificate modell
class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    certificate_name = Column(String(255), nullable=False)
    issuing_organization = Column(String(255), nullable=True)
    issue_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True)
    certificate_url = Column(String(255), nullable=True)

    candidate = relationship("Candidate", back_populates="certificates")


# Project modell
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    project_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    url = Column(String(255), nullable=True)

    candidate = relationship("Candidate", back_populates="projects")


# Attachment modell
class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    upload_date = Column(Date, nullable=True)

    candidate = relationship("Candidate", back_populates="attachments")


# Candidate model kezelés az adatbázisban
def create_candidate(db: Session, first_name: str, last_name: str, email: str, phone_number: str = None, location: str = None, linkedin_url: str = None, summary: str = None) -> Candidate:
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
    return candidate

def get_candidate(db: Session, candidate_id: int) -> Candidate:
    return db.query(Candidate).filter(Candidate.id == candidate_id).first()

def get_candidate_by_email(db: Session, email: str) -> Candidate:
    return db.query(Candidate).filter(Candidate.email == email).first()

def update_candidate(db: Session, candidate_id: int, update_data: dict) -> Candidate:
    candidate = get_candidate(db, candidate_id)
    if candidate:
        for key, value in update_data.items():
            setattr(candidate, key, value)
        db.commit()
        db.refresh(candidate)
    return candidate

def delete_candidate(db: Session, candidate_id: int) -> bool:
    candidate = get_candidate(db, candidate_id)
    if candidate:
        db.delete(candidate)
        db.commit()
        return True
    return False
