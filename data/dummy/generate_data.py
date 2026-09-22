import sys
import os
from datetime import datetime, timedelta
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.connection import engine, Base, SessionLocal
from database.models import Category, Product, ItemType, Transaction, TransactionDetail, Expense, Debt, Income


def generate_dummy_data():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # ── 1. KATEGORI ──────────────────────────────────────────────────────────
    # Pisah kategori produk jual vs bahan/kemasan supaya filter UI lebih mudah
    kategori_produk   = ["Sembako", "Minuman", "Snack", "Rokok", "Kebutuhan Mandi"]
    kategori_internal = ["Bahan Baku", "Kemasan"]

    cat_objs = {}
    for c in kategori_produk + kategori_internal:
        cat = Category(name=c)
        db.add(cat)
        db.flush()
        cat_objs[c] = cat
    db.commit()

    # ── 2. PRODUK DIJUAL ─────────────────────────────────────────────────────
    # (Nama, Kategori, Harga Jual, HPP, Stok, Unit)
    produk_dijual_data = [
        ("Beras 5kg",          "Sembako",         75000, 65000, 50.0,  "pack"),
        ("Telur 1kg",          "Sembako",         28000, 24000, 40.0,  "kg"),
        ("Indomie Goreng",     "Sembako",          3500,  2800, 200.0, "pcs"),
        ("Kopi Kapal Api",     "Minuman",          1500,  1100, 100.0, "bungkus"),
        ("Aqua 600ml",         "Minuman",          3500,  2500,  80.0, "botol"),
        ("Taro Snack",         "Snack",            2000,  1500,  60.0, "pcs"),
        ("Chitato",            "Snack",            8000,  6500,  40.0, "pcs"),
        ("Rokok Sampoerna",    "Rokok",           25000, 23000,  30.0, "bungkus"),
        ("Rokok Gudang Garam", "Rokok",           20000, 18500,  30.0, "bungkus"),
        ("Sabun Lifebuoy",     "Kebutuhan Mandi",  4000,  3000,  50.0, "pcs"),
        ("Shampo Pantene",     "Kebutuhan Mandi", 15000, 12000,  25.0, "pcs"),
    ]

    prod_objs = []
    for name, cat_name, price, cost_price, stock, unit in produk_dijual_data:
        p = Product(
            name=name,
            category_id=cat_objs[cat_name].id,
            item_type=ItemType.PRODUK_DIJUAL,
            price=price,
            cost_price=cost_price,
            stock=stock,
            unit=unit,
        )
        db.add(p)
        db.flush()
        prod_objs.append(p)
    db.commit()

    # ── 3. BAHAN BAKU ────────────────────────────────────────────────────────
    # price=None — bahan baku tidak dijual langsung ke pelanggan
    # (Nama, HPP per unit, Stok, Unit)
    bahan_baku_data = [
        ("Tepung Terigu",  12000,  5.0,  "kg"),
        ("Gula Pasir",     14000,  3.0,  "kg"),
        ("Minyak Goreng",  18000,  2.0,  "liter"),
        ("Gas LPG 3kg",    22000,  2.0,  "tabung"),
        ("Saus Sambal",     8000,  3.0,  "botol"),
    ]

    for name, cost_price, stock, unit in bahan_baku_data:
        db.add(Product(
            name=name,
            category_id=cat_objs["Bahan Baku"].id,
            item_type=ItemType.BAHAN_BAKU,
            price=None,           # tidak punya harga jual
            cost_price=cost_price,
            stock=stock,
            unit=unit,
        ))

    # ── 4. KEMASAN ───────────────────────────────────────────────────────────
    kemasan_data = [
        ("Plastik Kresek",  8000, 10.0, "pack"),
        ("Cup Plastik",     5000,  5.0, "pack"),
        ("Kantong Kertas",  6000,  3.0, "pack"),
    ]

    for name, cost_price, stock, unit in kemasan_data:
        db.add(Product(
            name=name,
            category_id=cat_objs["Kemasan"].id,
            item_type=ItemType.KEMASAN,
            price=None,
            cost_price=cost_price,
            stock=stock,
            unit=unit,
        ))

    db.commit()

    # ── 5. TRANSAKSI (30 hari terakhir, 90 transaksi) ────────────────────────
    # Hanya pakai prod_objs (produk_dijual) — bahan baku tidak masuk kasir
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
            qty = random.randint(1, int(max_qty))
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

    # ── 6. PENGELUARAN ───────────────────────────────────────────────────────
    expenses = [
        ("Bayar Listrik",         150000, "listrik"),
        ("Beli Plastik Kresek",    15000, "operasional"),
        ("Belanja Stok Indomie",  350000, "bahan_baku"),
        ("Belanja Telur & Beras", 500000, "bahan_baku"),
        ("Gaji Karyawan",        1500000, "gaji"),
        ("Bayar Air",              50000, "listrik"),
        ("Beli Rokok Sampoerna",  600000, "bahan_baku"),
    ]
    for desc, amount, category in expenses:
        db.add(Expense(
            description=desc,
            amount=amount,
            category=category,
            timestamp=datetime.now() - timedelta(days=random.randint(0, 30))
        ))

    # ── 7. HUTANG ────────────────────────────────────────────────────────────
    debts = [
        ("Pak Budi",     25000, "customer", False),
        ("Bu Sari",      50000, "customer", False),
        ("Bu Ani",       15000, "customer", True),
        ("Supplier ABC", 500000, "supplier", False),
    ]
    for name, amount, dtype, is_paid in debts:
        db.add(Debt(
            customer_name=name,
            amount=amount,
            debt_type=dtype,
            is_paid=is_paid,
            paid_at=datetime.now() if is_paid else None
        ))

    # ── 8. PEMASUKAN NON-KASIR ───────────────────────────────────────────────
    incomes = [
        ("Pesanan Katering Arisan", 500000, "katering"),
        ("Transfer Bu Dewi",        150000, "transfer"),
        ("Pesanan Nasi Kotak",      300000, "katering"),
    ]
    for desc, amount, source in incomes:
        db.add(Income(
            description=desc,
            amount=amount,
            source=source,
            timestamp=datetime.now() - timedelta(days=random.randint(0, 30))
        ))

    db.commit()
    db.close()
    print("Berhasil! Database saku.db siap dengan data dummy.")

if __name__ == "__main__":
    generate_dummy_data()