import sys
import os
from datetime import datetime, timedelta
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.connection import engine, Base, SessionLocal
from database.models import Category, Product, Transaction, TransactionDetail, Expense, Debt, Income

def generate_dummy_data():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Kategori
    categories = ["Sembako", "Minuman", "Snack", "Rokok", "Kebutuhan Mandi"]
    cat_objs = {}
    for c in categories:
        cat = Category(name=c)
        db.add(cat)
        db.flush()
        cat_objs[c] = cat
    db.commit()

    # 2. Produk (Nama, Kategori, Harga Jual, Harga Modal/HPP, Stok)
    products_data = [
        ("Beras 5kg",        "Sembako",          75000, 65000, 50),
        ("Telur 1kg",        "Sembako",          28000, 24000, 40),
        ("Indomie Goreng",   "Sembako",           3500,  2800, 200),
        ("Kopi Kapal Api",   "Minuman",           1500,  1100, 100),
        ("Aqua 600ml",       "Minuman",           3500,  2500, 80),
        ("Taro Snack",       "Snack",             2000,  1500, 60),
        ("Chitato",          "Snack",             8000,  6500, 40),
        ("Rokok Sampoerna",  "Rokok",            25000, 23000, 30),
        ("Rokok Gudang Garam","Rokok",           20000, 18500, 30),
        ("Sabun Lifebuoy",   "Kebutuhan Mandi",   4000,  3000, 50),
        ("Shampo Pantene",   "Kebutuhan Mandi",  15000, 12000, 25),
    ]

    prod_objs = []
    for name, cat_name, price, cost_price, stock in products_data:
        p = Product(
            name=name, 
            category_id=cat_objs[cat_name].id, 
            price=price, 
            cost_price=cost_price, 
            stock=stock
        )
        db.add(p)
        db.flush()
        prod_objs.append(p)
    db.commit()

    # 3. Transaksi (30 hari terakhir, 90 transaksi)
    methods = ["Cash", "QRIS"]
    for i in range(90):
        days_ago = random.randint(0, 30)
        trx_time = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 12))

        trx = Transaction(
            timestamp=trx_time,
            total_amount=0,
            payment_method=random.choice(methods)
        )
        db.add(trx)
        db.flush()

        total_amount = 0
        for _ in range(random.randint(1, 4)):
            prod = random.choice(prod_objs)
            max_qty = min(prod.stock, 5)
            if max_qty <= 0:
                continue
            qty = random.randint(1, max_qty)
            sub = prod.price * qty
            total_amount += sub
            prod.stock -= qty  

            db.add(TransactionDetail(
                transaction_id=trx.id,
                product_id=prod.id,
                quantity=qty,
                cost_price=prod.cost_price,   
                selling_price=prod.price,     
                subtotal=sub
            ))

        trx.total_amount = total_amount
        db.commit()

    # 4. Pengeluaran (beragam kategori)
    expenses = [
        ("Bayar Listrik",          150000, "listrik"),
        ("Beli Plastik Kresek",     15000, "operasional"),
        ("Belanja Stok Indomie",   350000, "bahan_baku"),
        ("Belanja Telur & Beras",  500000, "bahan_baku"),
        ("Gaji Karyawan",         1500000, "gaji"),
        ("Bayar Air",               50000,  "listrik"),
        ("Beli Rokok Sampoerna",   600000,  "bahan_baku"),
    ]
    for desc, amount, category in expenses:
        days_ago = random.randint(0, 30)
        db.add(Expense(
            description=desc,
            amount=amount,
            category=category,
            timestamp=datetime.now() - timedelta(days=days_ago)
        ))

    # 5. Hutang (customer & supplier)
    debts = [
        ("Pak Budi",    25000,  "customer", False),
        ("Bu Sari",     50000,  "customer", False),
        ("Bu Ani",      15000,  "customer", True),
        ("Supplier ABC",500000, "supplier", False),
    ]
    for name, amount, dtype, is_paid in debts:
        db.add(Debt(
            customer_name=name,
            amount=amount,
            debt_type=dtype,
            is_paid=is_paid,
            paid_at=datetime.now() if is_paid else None
        ))

    # 6. Pemasukan non-kasir
    incomes = [
        ("Pesanan Katering Arisan",  500000, "katering"),
        ("Transfer Bu Dewi",         150000, "transfer"),
        ("Pesanan Nasi Kotak",       300000, "katering"),
    ]
    for desc, amount, source in incomes:
        days_ago = random.randint(0, 30)
        db.add(Income(
            description=desc,
            amount=amount,
            source=source,
            timestamp=datetime.now() - timedelta(days=days_ago)
        ))

    db.commit()
    db.close()
    print("✅ Berhasil! Database saku.db siap dengan data dummy UMKM.")

if __name__ == "__main__":
    generate_dummy_data()