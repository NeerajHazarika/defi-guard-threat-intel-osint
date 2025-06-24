from sqlalchemy import create_engine, Column, String, DateTime, Float, Boolean, Text, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./defi_guard.db")

try:
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(DATABASE_URL)
except ImportError as e:
    if "psycopg2" in str(e) and not DATABASE_URL.startswith("sqlite"):
        print("Warning: PostgreSQL driver not available, falling back to SQLite")
        DATABASE_URL = "sqlite:///./defi_guard.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ThreatIntelDB(Base):
    __tablename__ = "threat_intel"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    protocol_name = Column(String, index=True)
    risk_level = Column(String, nullable=False, index=True)
    source_url = Column(String, nullable=False, unique=True)
    source_name = Column(String, nullable=False, index=True)
    published_date = Column(DateTime)
    scraped_date = Column(DateTime, default=func.now())
    tags = Column(JSON)
    amount_lost = Column(Float)
    attack_type = Column(String, index=True)
    blockchain = Column(String, index=True)
    severity_score = Column(Float)
    is_verified = Column(Boolean, default=False)
    additional_data = Column(JSON)

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
