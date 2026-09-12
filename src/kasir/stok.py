from sqlalchemy.orm import Session
from database.models import Product

def tambah_stok(db: Session, product_id: int, jumlah_tambah: int):
    """Menambahkan stok produk yang ada."""
    produk = db.query(Product).filter(Product.id == product_id).first()
    if not produk:
        raise ValueError("Produk tidak ditemukan.")
    
    # Use setattr to avoid the ORM class-level Column typing on assignment.
    setattr(produk, "stock", produk.stock + jumlah_tambah)
    db.commit()
    db.refresh(produk)
    return produk

def get_stok_kritis(db: Session, threshold: int = 5):
    """Mendapatkan daftar produk yang stoknya di bawah batas minimal."""
    return db.query(Product).filter(Product.stock <= threshold).all()

def get_semua_produk(db: Session):
    return db.query(Product).filter(Product.is_active == True).all()

def get_produk_by_id(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()