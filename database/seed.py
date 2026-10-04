import random
from datetime import datetime, timedelta
from database.connection import SessionLocal, engine, Base
from database.models import (
    Category, Product, ItemType, Transaction, TransactionDetail, 
    InventoryMovement, Expense, Income, Debt
)

# Pastikan tabel sudah ada
Base.metadata.create_all(bind=engine)

def seed_all_data():
    db = SessionLocal()
    
    # Cek apakah database sudah ada isinya
    if db.query(Product).count() > 0:
        print("Database sudah memiliki data. Seeding dibatalkan agar tidak duplikat.")
        db.close()
        return

    print("Memulai proses seeding data untuk SEMUA FITUR SAKU POS...")
    
    # ==========================================
    # 1. SEED KATEGORI & PRODUK (Inventaris)
    # ==========================================
    print("Mengisi data Kategori & Produk...")
    kat_sembako = Category(name="Sembako")
    kat_minuman = Category(name="Minuman")
    db.add_all([kat_sembako, kat_minuman])
    db.commit()

    produk_list = [
        Product(name="Beras Ramos 5kg", category_id=kat_sembako.id, cost_price=60000, price=65000, stock=20, min_stock=5, unit="karung", item_type=ItemType.PRODUK_DIJUAL),
        Product(name="Telur Ayam 1kg", category_id=kat_sembako.id, cost_price=24000, price=28000, stock=15, min_stock=5, unit="kg", item_type=ItemType.PRODUK_DIJUAL),
        Product(name="Minyak Goreng 2L", category_id=kat_sembako.id, cost_price=32000, price=36000, stock=10, min_stock=3, unit="pouch", item_type=ItemType.PRODUK_DIJUAL),
        Product(name="Aqua Botol 600ml", category_id=kat_minuman.id, cost_price=2500, price=4000, stock=50, min_stock=10, unit="botol", item_type=ItemType.PRODUK_DIJUAL),
        Product(name="Kopi Kapal Api", category_id=kat_minuman.id, cost_price=1200, price=2000, stock=100, min_stock=20, unit="sachet", item_type=ItemType.PRODUK_DIJUAL)
    ]
    db.add_all(produk_list)
    db.commit()

    # ==========================================
    # 2. SEED TRANSAKSI KASIR (Riwayat Penjualan)
    # ==========================================
    print("Mengisi data Transaksi Kasir (7 hari terakhir)...")
    hari_ini = datetime.now()
    
    for i in range(7, 0, -1):
        # Buat 2-3 transaksi per hari
        for _ in range(random.randint(2, 4)):
            waktu_transaksi = hari_ini - timedelta(days=i, hours=random.randint(1, 8))
            
            # Pilih 1-3 produk secara acak untuk dibeli
            produk_dibeli = random.sample(produk_list, random.randint(1, 3))
            
            total_belanja = 0
            details = []
            
            for p in produk_dibeli:
                qty = random.randint(1, 3)
                subtotal = qty * p.price
                total_belanja += subtotal
                
                details.append(TransactionDetail(
                    product_id=p.id,
                    quantity=qty,
                    cost_price=p.cost_price,
                    selling_price=p.price,
                    subtotal=subtotal
                ))
                
                # Catat pergerakan stok
                db.add(InventoryMovement(
                    product_id=p.id,
                    quantity_change=-qty,
                    stock_after=p.stock - qty, # dummy logic
                    reason="sale",
                    timestamp=waktu_transaksi,
                    notes="Penjualan dari Kasir"
                ))
            
            transaksi = Transaction(
                timestamp=waktu_transaksi,
                total_amount=total_belanja,
                payment_method=random.choice(["Tunai", "QRIS", "Tunai"]),
                details=details
            )
            db.add(transaksi)
    db.commit()

    # ==========================================
    # 3. SEED AKUNTANSI (Pengeluaran & Pemasukan)
    # ==========================================
    print("Mengisi data Akuntansi...")
    db.add(Expense(timestamp=hari_ini - timedelta(days=2), description="Bayar Listrik Toko", amount=150000, category="Operasional"))
    db.add(Expense(timestamp=hari_ini - timedelta(days=1), description="Beli Kantong Plastik", amount=25000, category="Perlengkapan"))
    db.add(Income(timestamp=hari_ini - timedelta(days=3), description="Titipan Katering Ibu RT", amount=50000, source="Lain-lain"))
    db.commit()

    # ==========================================
    # 4. SEED HUTANG / KASBON (Fase 3)
    # ==========================================
    print("Mengisi data Hutang & Kasbon...")
    db.add(Debt(customer_name="Pak Budi (Tetangga)", amount=45000, timestamp=hari_ini - timedelta(days=4), is_paid=False, notes="Ambil beras dan rokok"))
    db.add(Debt(customer_name="Bu Tejo", amount=28000, timestamp=hari_ini - timedelta(days=2), is_paid=True, paid_at=hari_ini, notes="Telur 1kg (Sudah Lunas)"))
    db.add(Debt(customer_name="Supplier Telur", amount=150000, timestamp=hari_ini - timedelta(days=1), is_paid=False, debt_type="supplier", notes="Hutang ke distributor"))
    db.commit()

    print("SEMUA DATA DUMMY BERHASIL DIMASUKKAN KE CLOUD DB!")
    db.close()

if __name__ == "__main__":
    seed_all_data()