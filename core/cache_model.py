from sqlalchemy import Column, Integer, String, Float, LargeBinary, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from core.database import Base

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

    # Kapcsolat a jelölt táblával
    candidate = relationship("Candidate", back_populates="industries")

# Jelöltek és állások pontszámainak tárolása
class CandidateJobScore(Base):
    __tablename__ = 'candidate_job_score'

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), index=True)
    job_id = Column(Integer, ForeignKey('job_descriptions.id'), index=True)
    industry_score = Column(Float, nullable=False)
    technical_score = Column(Float, nullable=False)
    job_matching_score = Column(Float, nullable=False)
    final_score = Column(Float, nullable=False)

    # Egyedi kombináció biztosítása, hogy minden jelölt és állás kombináció csak egyszer szerepeljen
    __table_args__ = (UniqueConstraint('candidate_id', 'job_id', name='unique_candidate_job'),)

    # Kapcsolatok a jelölt és munkaköri leírás táblákhoz
    candidate = relationship("Candidate")
    job_description = relationship("JobDescription")
