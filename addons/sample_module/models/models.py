from sqlalchemy import Column, Integer, String
from core.database import Base

class SampleModel(Base):
    __tablename__ = "sample_model"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
