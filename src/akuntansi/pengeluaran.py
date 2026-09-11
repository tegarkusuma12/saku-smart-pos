from sqlalchemy.orm import Session
from database.models import Expense

def catat_pengeluaran(db: Session, deskripsi: str, nominal: float):
    """Menyimpan data pengeluaran operasional baru."""
    if nominal <= 0:
        raise ValueError("Nominal pengeluaran harus lebih besar dari 0.")
        
    pengeluaran_baru = Expense(description=deskripsi, amount=nominal)
    db.add(pengeluaran_baru)
    db.commit()
    db.refresh(pengeluaran_baru)
    return pengeluaran_baru