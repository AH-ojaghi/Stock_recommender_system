# database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# اتصال به PostgreSQL از طریق URL در فایل .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Engine
# pool_pre_ping=True for robust connection handling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# SessionLocal for database interaction
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()

# Dependency function to get database session (used in FastAPI routes)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create tables
def create_tables():
    """Creates all defined tables in the database."""
    # Note: Ensure models.py is imported before calling this function
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")