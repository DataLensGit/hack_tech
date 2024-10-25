from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from .repositories import create_sample, get_samples, update_sample, delete_sample

router = APIRouter()

# Új minta létrehozása
@router.post("/samples/")
def create_new_sample(name: str, description: str, db: Session = Depends(get_db)):
    return create_sample(db, name, description)

# Minták lekérdezése
@router.get("/samples/")
def read_samples(db: Session = Depends(get_db)):
    return get_samples(db)

# Minta frissítése
@router.put("/samples/{sample_id}")
def update_sample_record(sample_id: int, name: str, description: str, db: Session = Depends(get_db)):
    return update_sample(db, sample_id, name, description)

# Minta törlése
@router.delete("/samples/{sample_id}")
def delete_sample_record(sample_id: int, db: Session = Depends(get_db)):
    return delete_sample(db, sample_id)
