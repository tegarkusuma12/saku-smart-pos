from sqlalchemy.orm import Session
from database.models import Expense

def catat_pengeluaran(db: Session, deskripsi: str, nominal: float, kategori: str | None = None):
    """Menyimpan data pengeluaran operasional baru."""
    if nominal <= 0:
        raise ValueError("Nominal pengeluaran harus lebih besar dari 0.")
        
    pengeluaran_baru = Expense(
        description=deskripsi, 
        amount=nominal,
        category=kategori  # "bahan_baku", "listrik", "gaji", dll
    )
    db.add(pengeluaran_baru)
    db.flush()
    db.refresh(pengeluaran_baru)
    return pengeluaran_baru

def get_pengeluaran(db: Session, limit: int = 50):
    return db.query(Expense).order_by(Expense.timestamp.desc()).limit(limit).all()