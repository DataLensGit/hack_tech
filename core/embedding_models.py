import json
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

# Embedding model for storing embeddings
class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    text_type = Column(String(50), nullable=False)  # lehet 'candidate' vagy 'job_description'
    text_id = Column(Integer, nullable=False)  # Jelölt vagy munkaköri leírás ID
    embedding = Column(Text, nullable=False)  # JSON-ként tárolt embedding
