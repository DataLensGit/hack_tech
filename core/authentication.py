from sqlalchemy.orm import Session
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from core.database import Base
from core.config import settings
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from addons.admin_module.models import Parameter

# Jelszó hash-elés
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# UserProperty modell
class UserProperty(Base):
    __tablename__ = "user_properties"

    id = Column(Integer, primary_key=True, index=True)
    property_name = Column(String(255), nullable=False)  # Paraméter neve (pl. név, adószám)
    property_description = Column(Text, nullable=True)   # Paraméter leírása
    identifier = Column(String(255), nullable=False, unique=True)  # Azonosító (kisbetű, ékezet nélkül)

    # Kapcsolat a UserPropertyAssignment táblával
    properties_assignments = relationship("UserPropertyAssignment", back_populates="property")


# Felhasználók táblája
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # Kapcsolat a tulajdonságokkal
    properties = relationship("UserPropertyAssignment", back_populates="user")


# UserPropertyAssignment modell
class UserPropertyAssignment(Base):
    __tablename__ = "user_property_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    property_id = Column(Integer, ForeignKey('user_properties.id'), nullable=False)
    value = Column(Text, nullable=True)  # Felhasználóspecifikus érték

    # Kapcsolat a felhasználókkal és a tulajdonságokkal
    user = relationship("User", back_populates="properties")
    property = relationship("UserProperty", back_populates="properties_assignments")


# Jelszó kezelése és JWT kezelés
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def decode_jwt(token: str) -> str:
    payload = verify_access_token(token)
    return payload.get('sub', "Guest") if payload else "Guest"

# User model kezelés az adatbázisban
def create_user(db: Session, username: str, email: str, password: str) -> User:
    hashed_password = get_password_hash(password)
    user = User(username=username, email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user(db: Session, user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> User:
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()
