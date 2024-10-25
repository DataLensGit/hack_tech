from sqlalchemy.orm import Session
from .models.models import SampleModel

# Új elem létrehozása
def create_sample(db: Session, name: str, description: str):
    sample = SampleModel(name=name, description=description)
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample

# Elemek lekérdezése
def get_samples(db: Session):
    return db.query(SampleModel).all()

# Elem frissítése
def update_sample(db: Session, sample_id: int, name: str, description: str):
    sample = db.query(SampleModel).filter(SampleModel.id == sample_id).first()
    if sample:
        sample.name = name
        sample.description = description
        db.commit()
    return sample

# Elem törlése
def delete_sample(db: Session, sample_id: int):
    sample = db.query(SampleModel).filter(SampleModel.id == sample_id).first()
    if sample:
        db.delete(sample)
        db.commit()
    return sample
if __name__ == "__main__":
    pass
