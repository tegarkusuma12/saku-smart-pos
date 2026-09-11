import sys
import os
from datetime import datetime, timedelta
import random

# Menambahkan root directory ke sys.path agar bisa import module database
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.connection import engine, Base, SessionLocal
from database.models import Category, Product, Transaction, TransactionDetail, Expense, Debt

def generate_dummy_data():
    # 1. Buat ulang semua tabel
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 2. Buat Kategori
    categories = ["Sembako", "Minuman", "Snack", "Rokok", "Kebutuhan Mandi"]
    cat_objs = {}
    for c in categories:
        cat = Category(name=c)
        db.add(cat)
        db.commit()
        db.refresh(cat)
        cat_objs[c] = cat

    # 3. Buat Produk (Gaya Warung UMKM)
    products_data = [
        ("Beras 5kg", cat_objs["Sembako"].id, 75000, 20),
        ("Telur 1kg", cat_objs["Sembako"].id, 28000, 15),
        ("Indomie Goreng", cat_objs["Sembako"].id, 3500, 100),
        ("Kopi Kapal Api", cat_objs["Minuman"].id, 1500, 50),
        ("Aqua 600ml", cat_objs["Minuman"].id, 3500, 40),
        ("Taro Snack", cat_objs["Snack"].id, 2000, 30),
        ("Sabun Lifebuoy", cat_objs["Kebutuhan Mandi"].id, 4000, 25),
    ]
    
    prod_objs = []
    for name, cat_id, price, stock in products_data:
        p = Product(name=name, category_id=cat_id, price=price, stock=stock)
        db.add(p)
        db.commit()
        db.refresh(p)
        prod_objs.append(p)

    # 4. Buat Transaksi (7 hari terakhir)
    methods = ["Cash", "QRIS"]
    for i in range(30): # 30 transaksi dummy
        days_ago = random.randint(0, 7)
        trx_time = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(1, 8))
        
        trx = Transaction(timestamp=trx_time, total_amount=0, payment_method=random.choice(methods))
        db.add(trx)
        db.commit()
        db.refresh(trx)

        total_amount = 0
        # Beli 1 sampai 3 item per transaksi
        for _ in range(random.randint(1, 3)):
            prod = random.choice(prod_objs)
            qty = random.randint(1, 5)
            sub = prod.price * qty
            total_amount += sub
            
            detail = TransactionDetail(transaction_id=trx.id, product_id=prod.id, quantity=qty, subtotal=sub)
            db.add(detail)
            
            # Kurangi stok
            prod.stock -= qty
            
        trx.total_amount = total_amount
        db.commit()

    # 5. Buat Pengeluaran & Hutang
    db.add(Expense(description="Bayar Listrik", amount=150000))
    db.add(Expense(description="Beli Plastik Kresek", amount=15000))
    db.add(Debt(customer_name="Pak Budi", amount=25000))
    
    db.commit()
    db.close()
    print("✅ Berhasil! Database saku.db siap digunakan dengan data dummy.")

if __name__ == "__main__":
    generate_dummy_data()