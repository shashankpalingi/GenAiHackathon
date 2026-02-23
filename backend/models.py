"""
Drishyamitra - SQLAlchemy ORM Models
Defines: User, Photo, Face, Person, DeliveryHistory
"""

from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text,
    DateTime, ForeignKey, JSON, Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from config import SQLALCHEMY_DATABASE_URI

Base = declarative_base()
engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)
SessionLocal = sessionmaker(bind=engine)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    photos = relationship("Photo", back_populates="user", cascade="all, delete-orphan")
    persons = relationship("Person", back_populates="user", cascade="all, delete-orphan")
    deliveries = relationship("DeliveryHistory", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    original_filename = Column(String(255))
    upload_date = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    exif_data = Column(JSON)  # Store EXIF metadata (date taken, camera, GPS, etc.)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="photos")
    faces = relationship("Face", back_populates="photo", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "filepath": self.filepath,
            "original_filename": self.original_filename,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "user_id": self.user_id,
            "faces": [face.to_dict() for face in self.faces] if self.faces else [],
        }


class Face(Base):
    __tablename__ = "faces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    photo_id = Column(Integer, ForeignKey("photos.id"), nullable=False)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)  # Null = unidentified

    # Bounding box coordinates
    bbox_x = Column(Integer)
    bbox_y = Column(Integer)
    bbox_w = Column(Integer)
    bbox_h = Column(Integer)

    # Face embedding (stored as JSON array of floats)
    embedding = Column(JSON)

    confidence = Column(Float)  # Detection confidence
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    photo = relationship("Photo", back_populates="faces")
    person = relationship("Person", back_populates="faces")

    def to_dict(self):
        return {
            "id": self.id,
            "photo_id": self.photo_id,
            "person_id": self.person_id,
            "bbox": {
                "x": self.bbox_x, "y": self.bbox_y,
                "w": self.bbox_w, "h": self.bbox_h
            },
            "confidence": self.confidence,
            "person_name": self.person.name if self.person else "Unknown"
        }


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), default="Unknown")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Representative embedding for quick matching (average of all face embeddings)
    representative_embedding = Column(JSON)

    photo_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="persons")
    faces = relationship("Face", back_populates="person")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "photo_count": self.photo_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "face_count": len(self.faces) if self.faces else 0
        }


class DeliveryHistory(Base):
    __tablename__ = "delivery_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    method = Column(String(20), nullable=False)  # "email" or "whatsapp"
    recipient = Column(String(255), nullable=False)
    photo_ids = Column(JSON)  # List of photo IDs sent
    subject = Column(String(255))
    message = Column(Text)
    status = Column(String(20), default="pending")  # pending, sent, failed
    timestamp = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text)

    # Relationships
    user = relationship("User", back_populates="deliveries")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "method": self.method,
            "recipient": self.recipient,
            "photo_ids": self.photo_ids,
            "status": self.status,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


def init_db():
    """Create all tables."""
    Base.metadata.create_all(engine)
    print("Drishyamitra: Database tables created successfully.")


def get_session():
    """Get a new database session."""
    return SessionLocal()


if __name__ == "__main__":
    init_db()
