from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from core.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from core.database import Base
# Új táblázat az iparági tapasztalatok tárolására
class IndustryField(Base):
    __tablename__ = "industry_fields"

    id = Column(Integer, primary_key=True, index=True)
    industry_name = Column(String(255), nullable=False)  # Pl. "Retail", "Banking"
    job_description_id = Column(Integer, ForeignKey('job_descriptions.id'), nullable=False)
class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String(255), nullable=True)
    company_overview = Column(Text, nullable=True)

    # Kapcsolat a további részletekhez
    responsibilities = relationship("Responsibility", back_populates="job_description", cascade="all, delete-orphan")
    qualifications = relationship("Qualification", back_populates="job_description", cascade="all, delete-orphan")
    skills = relationship("PreferredSkill", back_populates="job_description", cascade="all, delete-orphan")
    benefits = relationship("Benefit", back_populates="job_description", cascade="all, delete-orphan")
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class Responsibility(Base):
    __tablename__ = "responsibilities"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    job_description_id = Column(Integer, ForeignKey('job_descriptions.id'), nullable=False)

    job_description = relationship("JobDescription", back_populates="responsibilities")
class Qualification(Base):
    __tablename__ = "qualifications"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    job_description_id = Column(Integer, ForeignKey('job_descriptions.id'), nullable=False)

    job_description = relationship("JobDescription", back_populates="qualifications")
class PreferredSkill(Base):
    __tablename__ = "preferred_skills"

    id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String(255), nullable=False)
    job_description_id = Column(Integer, ForeignKey('job_descriptions.id'), nullable=False)

    job_description = relationship("JobDescription", back_populates="skills")
class Benefit(Base):
    __tablename__ = "benefits"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    job_description_id = Column(Integer, ForeignKey('job_descriptions.id'), nullable=False)

    job_description = relationship("JobDescription", back_populates="benefits")
