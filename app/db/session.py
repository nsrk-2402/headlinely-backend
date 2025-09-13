from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Load DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/headlinely")

#create the sqlalchemy engine
engine = create_engine(
    DATABASE_URL,
    echo = True,      # Log SQL queries for development
)


# Create a configured "Session" class
SessionLocal = sessionmaker(
    autocommit = False,
    autoflush = False,
    bind = engine
)

# Base class for models
Base  = declarative_base()

# Dependency for FastAPI Routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()