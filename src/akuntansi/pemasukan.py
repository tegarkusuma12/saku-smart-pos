# src/akuntansi/pemasukan.py
from sqlalchemy.orm import Session
from database.models import Income

def catat_pemasukan(db: Session, deskripsi: str, nominal: float, sumber: str | None = None):
    """Mencatat pemasukan di luar transaksi kasir (katering, dll)."""
    if nominal <= 0:
        raise ValueError("Nominal harus lebih besar dari 0.")
    
    pemasukan_baru = Income(
        description=deskripsi,
        amount=nominal,
        source=sumber
    )
    db.add(pemasukan_baru)
    db.commit()
    db.refresh(pemasukan_baru)
    return pemasukan_baru

def get_pemasukan(db: Session, limit: int = 50):
    return db.query(Income).order_by(Income.timestamp.desc()).limit(limit).all()