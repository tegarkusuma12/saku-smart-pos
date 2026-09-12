from sqlalchemy.orm import Session
from database.models import Transaction, TransactionDetail, Product

def proses_checkout(db: Session, keranjang: list[dict], payment_method: str = "Cash"):
    """
    Memproses transaksi penjualan dan memotong stok.
    
    Args:
        db (Session): SQLAlchemy session
        keranjang (list[dict]): List item dengan format [{"product_id": int, "qty": int}]
        payment_method (str): Metode pembayaran (Cash, QRIS, dll)
        
    Returns:
        dict: Status transaksi, total, dan ID transaksi
    """
    try:
        # 1. Inisiasi transaksi utama
        transaksi_baru = Transaction(total_amount=0, payment_method=payment_method)
        db.add(transaksi_baru)
        db.flush() # Mendapatkan ID transaksi tanpa commit
        
        total_belanja = 0
        
        # 2. Proses detail item
        for item in keranjang:
            produk = db.query(Product).filter(Product.id == item["product_id"]).first()
            
            if not produk:
                raise ValueError(f"Produk ID {item['product_id']} tidak ditemukan.")
            if produk.stock < item["qty"]:
                raise ValueError(f"Stok '{produk.name}' tidak mencukupi (Sisa: {produk.stock}).")
            
            subtotal = produk.price * item["qty"]
            total_belanja += subtotal
            
            # Catat detail
            detail = TransactionDetail(
                transaction_id=transaksi_baru.id,
                product_id=produk.id,
                quantity=item["qty"],
                subtotal=subtotal
            )
            db.add(detail)
            
            # Kurangi stok
            produk.stock -= item["qty"]
            
        # 3. Finalisasi transaksi
        setattr(transaksi_baru, "total_amount", total_belanja)
        db.commit()
        db.refresh(transaksi_baru)
        
        return {
            "status": "success", 
            "transaction_id": transaksi_baru.id, 
            "total_amount": total_belanja
        }
        
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

def get_riwayat_transaksi(db: Session, limit: int = 50):
    return db.query(Transaction).order_by(
        Transaction.timestamp.desc()
    ).limit(limit).all()