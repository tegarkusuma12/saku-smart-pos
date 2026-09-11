import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Default ke SQLite lokal untuk development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///saku.db")

# Konfigurasi khusus untuk SQLite agar mendukung multithreading (penting untuk Streamlit)
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()