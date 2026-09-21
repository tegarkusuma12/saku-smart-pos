from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Product


app = FastAPI(
    title="SAKU Smart POS API",
    description="Backend API untuk SAKU Smart POS",
    version="1.0.0",
)


# ============================================================
# BASIC
# ============================================================

@app.get("/")
def root():
    return {
        "message": "SAKU Smart POS API",
        "status": "running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "ok"
    }


# ============================================================
# DATABASE TEST
# ============================================================

@app.get("/api/test-database")
def test_database(db: Session = Depends(get_db)):
    """
    Endpoint sederhana untuk memastikan
    FastAPI berhasil membaca database.
    """

    total_products = db.query(Product).count()

    return {
        "status": "success",
        "database": "connected",
        "total_products": total_products
    }