import sys
import os
from datetime import datetime, timedelta
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.connection import engine, Base, SessionLocal
from database.models import Category, Product, ItemType, Transaction, TransactionDetail, Expense, Debt, Income, InventoryMovement

NUM_DAYS = 120            # rentang data historis (sebelumnya 31)
RESTOCK_THRESHOLD = 0.25  # restock kalau stok < 25% dari stok awal

# Produk yang lebih laris di hari tertentu
WEEKEND_BOOST_PRODUCTS = {"Aqua 600ml", "Chitato", "Taro Snack", "Kopi Kapal Api"}
WEEKDAY_STAPLE_PRODUCTS = {"Beras 5kg", "Telur 1kg", "Indomie Goreng"}


def generate_dummy_data():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # ── 1. KATEGORI ──────────────────────────────────────────────────────────
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
    initial_stock = {}  # acuan level restock
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
        initial_stock[p.id] = stock
    db.commit()

    # ── 3. BAHAN BAKU ────────────────────────────────────────────────────────
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
            price=None,
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

    # ── 5. OPENING STOCK MOVEMENTS ───────────────────────────────────────────
    start_date = datetime.now() - timedelta(days=NUM_DAYS)
    all_products = db.query(Product).all()
    for p in all_products:
        if p.stock > 0:
            db.add(InventoryMovement(
                product_id      = p.id,
                quantity_change = +p.stock,
                stock_after     = p.stock,
                reason          = "opening_stock",
                timestamp       = start_date,
                notes           = "Stok awal saat sistem pertama digunakan",
            ))
    db.commit()

    # ── 6. TRANSAKSI HARIAN (pola weekend, tren, preferensi produk) ──────────
    methods = ["Cash", "QRIS"]
    expense_log = []  # biaya restock, dimasukkan ke Expense setelah loop harian

    for day_offset in range(NUM_DAYS):
        current_date = start_date + timedelta(days=day_offset)
        is_weekend = current_date.weekday() >= 5  # Sabtu=5, Minggu=6

        growth_factor = 1 + (day_offset / NUM_DAYS) * 0.6  # tren naik gradual
        base_trx = random.randint(6, 11) if is_weekend else random.randint(3, 6)
        trx_count_today = max(1, round(base_trx * growth_factor))

        for _ in range(trx_count_today):
            trx_time = current_date.replace(
                hour=random.randint(7, 21),
                minute=random.randint(0, 59),
            )
            trx = Transaction(timestamp=trx_time, total_amount=0, payment_method=random.choice(methods))
            db.add(trx)
            db.flush()

            total_amount = 0
            for _ in range(random.randint(1, 4)):
                weights = []
                for prod in prod_objs:
                    w = 1.0
                    if is_weekend and prod.name in WEEKEND_BOOST_PRODUCTS:
                        w *= 2.2
                    if (not is_weekend) and prod.name in WEEKDAY_STAPLE_PRODUCTS:
                        w *= 1.6
                    weights.append(w)
                prod = random.choices(prod_objs, weights=weights, k=1)[0]

                max_qty = min(prod.stock, 5)
                if max_qty <= 0:
                    continue
                qty = random.randint(1, int(max_qty))
                sub = prod.price * qty
                total_amount += sub
                prod.stock -= qty

                db.add(InventoryMovement(
                    product_id      = prod.id,
                    quantity_change = -qty,
                    stock_after     = prod.stock,
                    reason          = "sale",
                    reference_id    = trx.id,
                    timestamp       = trx_time,
                ))
                db.add(TransactionDetail(
                    transaction_id=trx.id,
                    product_id=prod.id,
                    quantity=qty,
                    cost_price=prod.cost_price,
                    selling_price=prod.price,
                    subtotal=sub,
                ))

            trx.total_amount = total_amount
            db.commit()

        # ── RESTOCK: cek tiap produk, isi ulang kalau stok tipis ─────────────
        for prod in prod_objs:
            threshold = initial_stock[prod.id] * RESTOCK_THRESHOLD
            if prod.stock < threshold:
                restock_qty = initial_stock[prod.id] - prod.stock
                restock_time = current_date.replace(hour=8, minute=0)
                prod.stock += restock_qty

                db.add(InventoryMovement(
                    product_id      = prod.id,
                    quantity_change = +restock_qty,
                    stock_after     = prod.stock,
                    reason          = "restock",
                    timestamp       = restock_time,
                ))
                expense_log.append((
                    f"Restock {prod.name}",
                    round(restock_qty * prod.cost_price),
                    "bahan_baku",
                    restock_time,
                ))
        db.commit()

    # ── 7. PENGELUARAN ───────────────────────────────────────────────────────
    months_span = (NUM_DAYS // 30) + 1
    for m in range(months_span):
        month_date = start_date + timedelta(days=m * 30 + random.randint(1, 5))
        if month_date > datetime.now():
            break
        db.add(Expense(description="Bayar Listrik", amount=150000, category="listrik", timestamp=month_date))
        db.add(Expense(description="Bayar Air", amount=50000, category="listrik",
                        timestamp=month_date + timedelta(days=1)))
        db.add(Expense(description="Gaji Karyawan", amount=1500000, category="gaji",
                        timestamp=month_date + timedelta(days=2)))

    for desc, amount, category, ts in expense_log:
        db.add(Expense(description=desc, amount=amount, category=category, timestamp=ts))

    # ── 8. HUTANG ────────────────────────────────────────────────────────────
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
            paid_at=datetime.now() if is_paid else None,
        ))

    # ── 9. PEMASUKAN NON-KASIR ───────────────────────────────────────────────
    n_incomes = max(3, NUM_DAYS // 15)
    income_templates = [
        ("Pesanan Katering Arisan", 500000, "katering"),
        ("Transfer Bu Dewi",        150000, "transfer"),
        ("Pesanan Nasi Kotak",      300000, "katering"),
    ]
    for _ in range(n_incomes):
        desc, amount, source = random.choice(income_templates)
        db.add(Income(
            description=desc,
            amount=amount,
            source=source,
            timestamp=start_date + timedelta(days=random.randint(0, NUM_DAYS)),
        ))

    db.commit()
    db.close()
    print(f"Berhasil! Database saku.db siap dengan data dummy {NUM_DAYS} hari.")


if __name__ == "__main__":
    generate_dummy_data()