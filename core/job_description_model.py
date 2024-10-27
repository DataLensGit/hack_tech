from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class IndustryField(Base):
    __tablename__ = "industry_fields"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    industry_name = Column(String(255), nullable=False)
    job_description_id = Column(Integer, ForeignKey('job_descriptions.id'), nullable=False)

    job_description = relationship("JobDescription", back_populates="industries")


class JobDescription(Base):
    __tablename__ = "job_descriptions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String(255), nullable=True)
    company_overview = Column(Text, nullable=True)

    # Iparágak hozzáadása
    industries = relationship("IndustryField", back_populates="job_description")

    responsibilities = relationship("core.job_description_model.Responsibility", back_populates="job_description",
                                    cascade="all, delete-orphan")
    qualifications = relationship("core.job_description_model.Qualification", back_populates="job_description",
                                  cascade="all, delete-orphan")
    skills = relationship("core.job_description_model.PreferredSkill", back_populates="job_description",
                          cascade="all, delete-orphan")
    benefits = relationship("core.job_description_model.Benefit", back_populates="job_description",
                            cascade="all, delete-orphan")

    def get_full_job_description(self) -> str:
        # Összefűzzük a leírások szövegét
        description_parts = []

        if self.company_overview:
            description_parts.append(self.company_overview)

        if self.responsibilities:
            responsibilities_text = " ".join([resp.description for resp in self.responsibilities])
            description_parts.append(f"Responsibilities: {responsibilities_text}")

        if self.qualifications:
            qualifications_text = " ".join([qual.description for qual in self.qualifications])
            description_parts.append(f"Qualifications: {qualifications_text}")

        if self.skills:
            skills_text = ", ".join([skill.skill_name for skill in self.skills])
            description_parts.append(f"Required Skills: {skills_text}")

        if self.benefits:
            benefits_text = " ".join([benefit.description for benefit in self.benefits])
            description_parts.append(f"Benefits: {benefits_text}")

        # Visszatérünk az összefűzött szöveggel
        return " | ".join(description_parts)

class Responsibility(Base):
    __tablename__ = "responsibilities"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    job_description_id = Column(Integer, ForeignKey('job_descriptions.id'), nullable=False)

    job_description = relationship("core.job_description_model.JobDescription", back_populates="responsibilities")


class Qualification(Base):
    __tablename__ = "qualifications"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    job_description_id = Column(Integer, ForeignKey('job_descriptions.id'), nullable=False)

    job_description = relationship("core.job_description_model.JobDescription", back_populates="qualifications")


class PreferredSkill(Base):
    __tablename__ = "preferred_skills"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String(255), nullable=False)
    job_description_id = Column(Integer, ForeignKey('job_descriptions.id'), nullable=False)

    job_description = relationship("core.job_description_model.JobDescription", back_populates="skills")


class Benefit(Base):
    __tablename__ = "benefits"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    job_description_id = Column(Integer, ForeignKey('job_descriptions.id'), nullable=False)

    job_description = relationship("core.job_description_model.JobDescription", back_populates="benefits")


if __name__ == "__main__":
    pass
