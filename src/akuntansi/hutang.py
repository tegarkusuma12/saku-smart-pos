from sqlalchemy.orm import Session
from database.models import Debt

def catat_hutang(db: Session, nama_pelanggan: str, nominal: float):
    """Mencatat hutang baru/kasbon pelanggan."""
    if nominal <= 0:
        raise ValueError("Nominal hutang harus lebih besar dari 0.")
        
    hutang_baru = Debt(customer_name=nama_pelanggan, amount=nominal)
    db.add(hutang_baru)
    db.commit()
    db.refresh(hutang_baru)
    return hutang_baru

def lunasi_hutang(db: Session, debt_id: int):
    """Mengubah status hutang menjadi sudah lunas."""
    hutang = db.query(Debt).filter(Debt.id == debt_id).first()
    if not hutang:
        raise ValueError("Data hutang tidak ditemukan.")
        
    hutang.is_paid = True
    db.commit()
    db.refresh(hutang)
    return hutang