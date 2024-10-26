from sqlalchemy import Column, Integer, String, Text
from core.database import Base

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String, nullable=True)
    company_overview = Column(Text, nullable=True)
    key_responsibilities = Column(Text, nullable=True)
    required_qualifications = Column(Text, nullable=True)
    preferred_skills = Column(Text, nullable=True)
    benefits = Column(Text, nullable=True)
