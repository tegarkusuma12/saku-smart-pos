from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from database.connection import get_db, engine, Base
from database.models import Product, Category, ItemType, Transaction, TransactionDetail, InventoryMovement, Debt, Expense, Income
from src.ai.agent import run_agent
from src.akuntansi.pengeluaran import catat_pengeluaran
from src.akuntansi.pemasukan import catat_pemasukan
from src.ml.forecasting import predict_revenue, get_restock_recommendations

# Auto generate table
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SAKU Smart POS API",
    description="Backend API untuk SAKU Smart POS",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:5500",
        "https://saku-smart-pos-app.vercel.app",  # <-- Masukkan URL Vercel Anda di sini
        "*"
    ],
    allow_credentials=False, 
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST SCHEMA
# ============================================================

class RestockRequest(BaseModel):
    quantity: float = Field(
        ...,
        gt=0,
        description="Jumlah stok yang ditambahkan"
    )
    total_harga: float = Field(
        ...,
        ge=0,
        description="Total harga pembelian"
    )
    catatan: str | None = None

class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    category_id: int | None = None
    item_type: ItemType = ItemType.PRODUK_DIJUAL
    cost_price: float = Field(..., ge=0)
    price: float = Field(..., ge=0)
    stock: float = Field(0, ge=0)
    min_stock: float = Field(5, ge=0)
    unit: str = Field("pcs", min_length=1)
    description: str | None = None

class ProductUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    category_id: int | None = None
    item_type: ItemType | None = None
    cost_price: float = Field(..., ge=0)
    price: float = Field(..., ge=0)
    min_stock: float | None = Field(None, ge=0)
    unit: str = Field("pcs", min_length=1)
    description: str | None = None

class StockAdjustmentRequest(BaseModel):
    quantity: float                      # positif = tambah, negatif = kurangi
    movement_type: str = Field("adjustment", pattern="^(adjustment|waste)$")
    reason: str = Field(..., min_length=1, max_length=255)


class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class TransactionItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class TransactionRequest(BaseModel):
    items: list[TransactionItemRequest]
    payment_method: str = Field(..., pattern="^(Cash|QRIS|Kasbon)$")
    customer_name: str | None = None   # wajib 
    notes: str | None = None

class LunasHutangRequest(BaseModel):
    catatan: str | None = None
class ChatRequest(BaseModel):
    message: str
    chat_history: list[dict] = Field(default_factory=list)

# ============================================================
# HELPER
# ============================================================

def get_stock_status(stock: float, min_stock: float) -> str:
    if stock <= 0:
        return "Habis"
    elif stock <= min_stock:  
        return "Menipis"
    else:
        return "Aman"


def product_to_dict(product: Product):

    return {
        "id": product.id,
        "name": product.name,
        "item_type": product.item_type,
        "category_id": product.category_id,
        "category": product.category.name if product.category else None,
        "cost_price": product.cost_price,
        "price": product.price,
        "stock": product.stock,
        "min_stock": product.min_stock,
        "unit": product.unit,
        "description": product.description,
        "is_active": product.is_active,
        "status": get_stock_status(product.stock, product.min_stock),
    }

def catat_movement(
    db: Session,
    product: Product,
    quantity_change: float,
    reason: str,
    reference_id: int | None = None,
    notes: str | None = None,
):
    movement = InventoryMovement(
        product_id      = product.id,
        quantity_change = quantity_change,
        stock_after     = product.stock,   # dipanggil setelah stock diupdate
        reason          = reason,
        reference_id    = reference_id,
        notes           = notes,
    )
    db.add(movement)

# ============================================================
# ML PREDICTIONS
# ============================================================

@app.get("/api/ml/forecast")
def forecast_revenue(days: int = 7):
    """Prediksi revenue harian untuk N hari ke depan."""
    if days < 1 or days > 30:
        raise HTTPException(
            status_code=400,
            detail="Parameter 'days' harus antara 1-30."
        )
    try:
        predictions = predict_revenue(days_ahead=days)
        return {
            "status": "success",
            "model": "sales_forecast",
            "days_ahead": days,
            "data": predictions.to_dict(orient="records"),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.get("/api/ml/restock-recommendations")
def restock_recommendations(safety_factor: float = 1.3):
    """Rekomendasi restock berdasarkan analisis inventory + demand."""
    try:
        recs = get_restock_recommendations(safety_factor=safety_factor)
        perlu_restock = [r for r in recs if r["restock_qty"] > 0]
        return {
            "status": "success",
            "safety_factor": safety_factor,
            "total_products": len(recs),
            "perlu_restock": len(perlu_restock),
            "data": recs,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================================================
# BASIC
# ============================================================

@app.get("/")
def root():

    return {
        "message": "SAKU Smart POS API",
        "status": "running"
    }


@app.get("/api/health")
def health_check():

    return {
        "status": "ok"
    }


# ============================================================
# DATABASE TEST
# ============================================================

@app.get("/api/test-database")
def test_database(
    db: Session = Depends(get_db)
):

    total_products = db.query(Product).count()

    return {
        "status": "success",
        "database": "connected",
        "total_products": total_products
    }

# ============================================================
# DASHBOARD
# ============================================================

@app.get("/api/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func, desc
    
    max_ts = db.query(func.max(Transaction.timestamp)).scalar()
    if not max_ts:
        return {
            "total_revenue": 0, "total_expense": 0, "total_profit": 0, "total_transactions": 0,
            "chart_labels": [], "chart_data": [], "top_products": [], "recent_transactions": []
        }
    
    if isinstance(max_ts, str):
        max_ts = datetime.fromisoformat(max_ts)
        
    start_date = (max_ts - timedelta(days=6)).replace(hour=0, minute=0, second=0)
    
    # 1. Stats Utama (7 hari terakhir dari data dummy)
    trx_7d = db.query(Transaction).filter(Transaction.timestamp >= start_date).all()
    total_rev_7d = sum(t.total_amount for t in trx_7d)
    
    exp_7d = db.query(Expense).filter(Expense.timestamp >= start_date).all()
    total_exp_7d = sum(e.amount for e in exp_7d)
    
    # 2. Chart Data
    daily_rev = {}
    for i in range(7):
        d = start_date + timedelta(days=i)
        daily_rev[d.strftime('%a, %d %b')] = 0
        
    for t in trx_7d:
        ts = t.timestamp if not isinstance(t.timestamp, str) else datetime.fromisoformat(t.timestamp)
        day_str = ts.strftime('%a, %d %b')
        if day_str in daily_rev:
            daily_rev[day_str] += t.total_amount
            
    # 3. Top Products
    top_items = db.query(
        Product.name,
        func.sum(TransactionDetail.quantity).label('total_qty'),
        func.sum(TransactionDetail.subtotal).label('total_rev')
    ).join(TransactionDetail, Product.id == TransactionDetail.product_id)\
     .join(Transaction, TransactionDetail.transaction_id == Transaction.id)\
     .filter(Transaction.timestamp >= start_date)\
     .group_by(Product.id, Product.name)\
     .order_by(desc('total_qty'))\
     .limit(5).all()
     
    # 4. Recent Transactions
    recent = db.query(Transaction).order_by(desc(Transaction.timestamp)).limit(5).all()
    recent_transactions = []
    for r in recent:
        ts = r.timestamp if not isinstance(r.timestamp, str) else datetime.fromisoformat(r.timestamp)
        recent_transactions.append({
            "id": f"TRX-{r.id:04d}",
            "time": ts.strftime('%H:%M'),
            "method": r.payment_method.capitalize(),
            "status": "Selesai",
            "total": r.total_amount
        })
        
    return {
        "total_revenue": total_rev_7d,
        "total_expense": total_exp_7d,
        "total_profit": total_rev_7d - total_exp_7d,
        "total_transactions": len(trx_7d),
        "chart_labels": list(daily_rev.keys()),
        "chart_data": list(daily_rev.values()),
        "top_products": [
            {"rank": i+1, "name": t.name, "sold": t.total_qty, "revenue": t.total_rev} 
            for i, t in enumerate(top_items)
        ],
        "recent_transactions": recent_transactions
    }

# ============================================================
# CHATBOT
# ============================================================

@app.post("/api/chat")
def chat(request: ChatRequest):

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Pesan tidak boleh kosong."
        )

    response = run_agent(
        user_input=request.message,
        chat_history=request.chat_history
    )

    return {
        "status": "success",
        "response": response
    }

# ============================================================
# KASIR
# ============================================================

@app.get("/api/kasir")
def get_kasir_products(
    db: Session = Depends(get_db)
):

    products = db.query(Product).filter(
        Product.is_active == True,
        Product.item_type == "produk_dijual"
    ).order_by(
        Product.name.asc()
    ).all()

    return {
        "status": "success",
        "total": len(products),
        "data": [
            product_to_dict(product)
            for product in products
        ]
    }

@app.post("/api/kasir/transaksi")
def catat_transaksi(
    request: TransactionRequest,
    db: Session = Depends(get_db)
):
    # Validasi kasbon harus ada nama
    if request.payment_method == "Kasbon" and not request.customer_name:
        raise HTTPException(
            status_code=400,
            detail="Nama pelanggan wajib diisi untuk pembayaran Kasbon."
        )

    total_amount = 0.0
    details_data = []

    # ── Validasi semua item sebelum commit apapun ──
    for item in request.items:
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.is_active == True,
            Product.item_type == "produk_dijual"
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Produk id {item.product_id} tidak ditemukan."
            )

        if product.price is None:
            raise HTTPException(
                status_code=400,
                detail=f"Produk '{product.name}' belum memiliki harga jual."
            )

        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Stok '{product.name}' tidak cukup. Sisa: {product.stock} {product.unit}."
            )

        subtotal = item.quantity * product.price
        total_amount += subtotal

        details_data.append({
            "product":       product,
            "quantity":      item.quantity,
            "cost_price":    product.cost_price,   # snapshot harga modal saat jual
            "selling_price": product.price,         # snapshot harga jual saat jual
            "subtotal":      subtotal,
        })

    # ── Semua valid — mulai commit ──

    # 1. Buat transaksi
    transaksi = Transaction(
        total_amount=total_amount,
        payment_method=request.payment_method,
        notes=request.notes,
    )
    db.add(transaksi)
    db.flush()   # dapat transaksi.id tanpa commit dulu

    # 2. Buat detail + kurangi stok
    for d in details_data:
        detail = TransactionDetail(
            transaction_id=transaksi.id,
            product_id=d["product"].id,
            quantity=d["quantity"],
            cost_price=d["cost_price"],
            selling_price=d["selling_price"],
            subtotal=d["subtotal"],
        )
        db.add(detail)
        d["product"].stock -= d["quantity"]   # kurangi stok

        catat_movement(                   
            db,
            d["product"],
            quantity_change = -d["quantity"],
            reason          = "sale",
            reference_id    = transaksi.id,
        )

    # 3. Kalau Kasbon → otomatis catat hutang
    if request.payment_method == "Kasbon":
        hutang = Debt(
            customer_name=request.customer_name,
            amount=total_amount,
            debt_type="customer",
            notes=f"Kasbon dari transaksi #{transaksi.id}",
        )
        db.add(hutang)

    db.commit()

    return {
        "status":          "success",
        "message":         "Transaksi berhasil dicatat.",
        "transaction_id":  transaksi.id,
        "total_amount":    total_amount,
        "payment_method":  request.payment_method,
        "items_count":     len(details_data),
    }

# ============================================================
# AKUNTANSI
# ============================================================

@app.get("/api/akuntansi/ledger")
def get_akuntansi_ledger(db: Session = Depends(get_db)):
    """Mengambil riwayat transaksi jurnal/buku besar."""
    ledger_entries = []
    
    # 1. Transaksi Penjualan
    transactions = db.query(Transaction).all()
    for t in transactions:
        ts = t.timestamp if not isinstance(t.timestamp, str) else datetime.fromisoformat(t.timestamp)
        akun_debit = "Kas" if t.payment_method != "Kasbon" else "Piutang"
        
        # Jurnal Penjualan
        ledger_entries.append({"ts": ts, "account": akun_debit, "description": f"Penjualan #{t.id}", "debit": t.total_amount, "credit": 0})
        ledger_entries.append({"ts": ts, "account": "Penjualan", "description": f"Penjualan #{t.id}", "debit": 0, "credit": t.total_amount})
        
        # Jurnal HPP (Harga Pokok Penjualan) & Persediaan
        hpp = sum((d.cost_price or 0) * (d.quantity or 0) for d in t.details)
        if hpp > 0:
            ledger_entries.append({"ts": ts, "account": "HPP", "description": f"HPP Penjualan #{t.id}", "debit": hpp, "credit": 0})
            ledger_entries.append({"ts": ts, "account": "Persediaan", "description": f"HPP Penjualan #{t.id}", "debit": 0, "credit": hpp})

    # 2. Pengeluaran (Expense)
    expenses = db.query(Expense).all()
    for e in expenses:
        ts = e.timestamp if not isinstance(e.timestamp, str) else datetime.fromisoformat(e.timestamp)
        # Jika belanja bahan baku, maka masuk ke Persediaan. Selain itu masuk ke Beban
        akun_debit = "Persediaan" if e.category == "bahan_baku" else "Beban " + (e.category or "Lainnya").capitalize()
        
        ledger_entries.append({"ts": ts, "account": akun_debit, "description": e.description, "debit": e.amount, "credit": 0})
        ledger_entries.append({"ts": ts, "account": "Kas", "description": e.description, "debit": 0, "credit": e.amount})

    # 3. Pemasukan Tambahan (Income)
    incomes = db.query(Income).all()
    for i in incomes:
        ts = i.timestamp if not isinstance(i.timestamp, str) else datetime.fromisoformat(i.timestamp)
        
        ledger_entries.append({"ts": ts, "account": "Kas", "description": i.description, "debit": i.amount, "credit": 0})
        ledger_entries.append({"ts": ts, "account": "Pemasukan " + (i.source or "Lainnya").capitalize(), "description": i.description, "debit": 0, "credit": i.amount})

    # Urutkan berdasarkan waktu transaksi (terbaru di atas)
    ledger_entries.sort(key=lambda x: x["ts"], reverse=True)
    
    # Format agar siap ditampilkan di Frontend
    formatted_ledger = []
    for entry in ledger_entries:
        ts_str = entry["ts"].strftime("%d-%m-%Y %H:%M")
        formatted_ledger.append({
            "date": ts_str,
            "account": entry["account"],
            "description": entry["description"],
            "debit": entry["debit"],
            "credit": entry["credit"]
        })

    return {
        "status": "success",
        "data": formatted_ledger
    }

# ============================================================
# HUTANG
# ============================================================

@app.post("/api/hutang/{debt_id}/lunas")
def lunasi_hutang(
    debt_id: int,
    request: LunasHutangRequest,
    db: Session = Depends(get_db)
):
    hutang = db.query(Debt).filter(
        Debt.id == debt_id,
        Debt.is_paid == False
    ).first()

    if not hutang:
        raise HTTPException(
            status_code=404,
            detail="Hutang tidak ditemukan atau sudah lunas."
        )

    # Tandai lunas
    hutang.is_paid = True
    hutang.paid_at = datetime.now()
    if request.catatan:
        hutang.notes = request.catatan

    # Catat ke akuntansi sesuai tipe
    if hutang.debt_type == "customer":
        # uang masuk
        catat_pemasukan(
            db,
            deskripsi = f"Pembayaran kasbon {hutang.customer_name}",
            nominal   = hutang.amount,
            sumber    = "bayar_kasbon",
        )
    else:
        # uang keluar
        catat_pengeluaran(
            db,
            deskripsi = f"Bayar hutang ke {hutang.customer_name}",
            nominal   = hutang.amount,
            kategori  = "bayar_hutang",
        )

    db.commit()

    return {
        "status":  "success",
        "message": f"Hutang {hutang.customer_name} berhasil dilunasi.",
        "data": {
            "id":            hutang.id,
            "customer_name": hutang.customer_name,
            "amount":        hutang.amount,
            "debt_type":     hutang.debt_type,
            "paid_at":       hutang.paid_at,
        }
    }

# ============================================================
# PRODUK 
# ============================================================
def validasi_kategori(db: Session, category_id: int | None):
    if category_id is None:
        return
    if not db.query(Category).filter(Category.id == category_id).first():
        raise HTTPException(status_code=404, detail="Kategori tidak ditemukan.")

@app.post("/api/produk")
def tambah_produk(
    request: ProductCreateRequest,
    db: Session = Depends(get_db)
):
    nama = request.name.strip()

    existing = db.query(Product).filter(
        func.lower(Product.name) == nama.lower(),
        Product.is_active == True
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail=f"Produk '{nama}' sudah ada.")

    validasi_kategori(db, request.category_id)

    produk = Product(
        name        = nama,
        category_id = request.category_id,
        item_type   = request.item_type,
        cost_price  = request.cost_price,
        price       = request.price,
        stock       = request.stock,
        min_stock   = request.min_stock,
        unit        = request.unit.strip(),
        description = request.description,
    )
    db.add(produk)
    db.flush()

    if request.stock > 0:
        db.add(InventoryMovement(
            product_id      = produk.id,
            quantity_change = +request.stock,
            stock_after     = request.stock,
            reason          = "opening_stock",
            notes           = "Stok awal saat produk ditambahkan",
        ))

    db.commit()
    db.refresh(produk)

    return {
        "status":  "success",
        "message": "Produk berhasil ditambahkan.",
        "data":    product_to_dict(produk)
    }

@app.put("/api/produk/{product_id}")
def edit_produk(
    product_id: int,
    request: ProductUpdateRequest,
    db: Session = Depends(get_db)
):
    produk = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True
    ).first()

    if not produk:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan.")

    nama = request.name.strip()

    existing = db.query(Product).filter(
        func.lower(Product.name) == nama.lower(),
        Product.id != product_id,
        Product.is_active == True
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail=f"Nama '{nama}' sudah dipakai produk lain.")

    validasi_kategori(db, request.category_id)

    produk.name        = nama
    produk.category_id = request.category_id
    produk.cost_price  = request.cost_price
    produk.price       = request.price
    produk.unit        = request.unit.strip()
    produk.description = request.description
    if request.item_type is not None:
        produk.item_type = request.item_type
    if request.min_stock is not None:
        produk.min_stock = request.min_stock

    db.commit()
    db.refresh(produk)

    return {
        "status":  "success",
        "message": "Produk berhasil diupdate.",
        "data":    product_to_dict(produk)
    }

@app.delete("/api/produk/{product_id}")
def hapus_produk(
    product_id: int,
    db: Session = Depends(get_db)
):
    produk = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True
    ).first()

    if not produk:
        raise HTTPException(
            status_code=404,
            detail="Produk tidak ditemukan."
        )

    # Soft delete — data historis tetap aman
    produk.is_active = False
    db.commit()

    return {
        "status":  "success",
        "message": f"Produk '{produk.name}' berhasil dinonaktifkan.",
    }

# ============================================================
# INVENTORY
# ============================================================
@app.get("/api/inventory")
def get_inventory(
    db: Session = Depends(get_db)
):

    products = db.query(Product).filter(
        Product.is_active == True
    ).order_by(
        Product.id.asc()
    ).all()

    return {
        "status": "success",
        "total": len(products),
        "data": [
            product_to_dict(product)
            for product in products
        ]
    }


# ============================================================
# INVENTORY STATISTICS
# ============================================================

@app.get("/api/inventory/stats")
def get_inventory_stats(
    db: Session = Depends(get_db)
):

    products = db.query(Product).filter(
        Product.is_active == True
    ).all()

    total_produk = len(products)

    stok_per_tipe = {}
    for p in products:
        tipe = p.item_type or "lainnya"
        stok_per_tipe[tipe] = stok_per_tipe.get(tipe, 0) + 1 

    stok_habis = sum(
        1
        for product in products
        if product.stock <= 0
    )

    stok_menipis = sum(
        1 for product in products
        if 0 < product.stock <= product.min_stock
    )

    stok_aman = sum(
        1 for product in products
        if product.stock > product.min_stock
    )

    total_nilai_modal = sum(
        (product.stock or 0) *
        (product.cost_price or 0)
        for product in products
    )

    total_nilai_jual = sum(
        (product.stock or 0) *
        (product.price or 0)
        for product in products
    )

    return {
        "status": "success",
        "data": {
            "total_produk": total_produk,
            "jumlah_per_tipe": stok_per_tipe,
            "stok_habis": stok_habis,
            "stok_menipis": stok_menipis,
            "stok_aman": stok_aman,
            "total_nilai_modal": total_nilai_modal,
            "total_nilai_jual": total_nilai_jual
        }
    }


# ============================================================
# RESTOCK INVENTORY
# ============================================================

@app.post("/api/inventory/{product_id}/restock")
def restock_product(
    product_id: int,
    request: RestockRequest,
    db: Session = Depends(get_db)
):

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True
    ).first()

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Produk tidak ditemukan."
        )

    product.stock += request.quantity

    expense_id = None
    if request.total_harga > 0:
        deskripsi = f"Beli {product.name} {request.quantity} {product.unit}"
        if request.catatan:
            deskripsi += f" — {request.catatan}"
        expense = catat_pengeluaran(db, deskripsi, request.total_harga, "bahan_baku")
        expense_id = expense.id

    catat_movement(
        db,
        product,
        quantity_change = +request.quantity,
        reason          = "purchase",
        reference_id    = expense_id,
        notes           = request.catatan,
    )

    db.commit()
    db.refresh(product)

    return {
        "status": "success",
        "message": "Stok berhasil ditambahkan dan pengeluaran tercatat.",
        "data": product_to_dict(product)
    }

# ============================================================
# KATEGORI
# ============================================================
@app.get("/api/kategori")
def get_kategori(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.name.asc()).all()
    return {
        "status": "success",
        "total": len(categories),
        "data": [{"id": c.id, "name": c.name} for c in categories]
    }

@app.post("/api/kategori")
def tambah_kategori(
    request: CategoryCreateRequest,
    db: Session = Depends(get_db)
):
    nama = request.name.strip()
    if not nama:
        raise HTTPException(status_code=400, detail="Nama kategori tidak boleh kosong.")

    existing = db.query(Category).filter(
        func.lower(Category.name) == nama.lower()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Kategori '{nama}' sudah ada.")

    kategori = Category(name=nama)
    db.add(kategori)
    db.commit()
    db.refresh(kategori)

    return {
        "status": "success",
        "message": "Kategori berhasil ditambahkan.",
        "data": {"id": kategori.id, "name": kategori.name}
    }

# ============================================================
# PENYESUAIAN STOK & RIWAYAT
# ============================================================
@app.post("/api/inventory/{product_id}/adjust")
def adjust_stock(
    product_id: int,
    request: StockAdjustmentRequest,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan.")

    if request.quantity == 0:
        raise HTTPException(status_code=400, detail="Jumlah penyesuaian tidak boleh 0.")

    if request.movement_type == "waste" and request.quantity > 0:
        raise HTTPException(status_code=400, detail="Barang rusak/hilang harus mengurangi stok.")

    new_stock = product.stock + request.quantity
    if new_stock < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Stok tidak boleh negatif. Stok saat ini: {product.stock} {product.unit}."
        )

    product.stock = new_stock

    catat_movement(
        db,
        product,
        quantity_change = request.quantity,
        reason          = request.movement_type,
        notes           = request.reason,
    )

    db.commit()
    db.refresh(product)

    return {
        "status": "success",
        "message": "Stok berhasil disesuaikan.",
        "data": product_to_dict(product)
    }

@app.get("/api/inventory/{product_id}/movements")
def get_movements(
    product_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan.")

    limit = max(1, min(limit, 200))

    movements = db.query(InventoryMovement).filter(
        InventoryMovement.product_id == product_id
    ).order_by(
        InventoryMovement.timestamp.desc(),
        InventoryMovement.id.desc()
    ).limit(limit).all()

    return {
        "status": "success",
        "product": product.name,
        "total": len(movements),
        "data": [
            {
                "id": m.id,
                "timestamp": m.timestamp.isoformat() if hasattr(m.timestamp, "isoformat") else str(m.timestamp),
                "quantity_change": m.quantity_change,
                "stock_after": m.stock_after,
                "reason": m.reason,
                "reference_id": m.reference_id,
                "notes": m.notes,
            }
            for m in movements
        ]
    }

# ============================================================
# HUTANG
# ============================================================

class DebtCreate(BaseModel):
    customer_name: str
    amount: float
    debt_type: str = "customer"
    notes: str = None

@app.get("/api/hutang")
def get_semua_hutang(db: Session = Depends(get_db)):
    from sqlalchemy import desc
    debts = db.query(Debt).order_by(Debt.is_paid.asc(), desc(Debt.timestamp)).all()
    return {
        "status": "success",
        "data": [
            {
                "id": d.id,
                "customer_name": d.customer_name,
                "amount": d.amount,
                "timestamp": d.timestamp.isoformat() if hasattr(d.timestamp, "isoformat") else str(d.timestamp),
                "is_paid": d.is_paid,
                "paid_at": d.paid_at.isoformat() if d.paid_at and hasattr(d.paid_at, "isoformat") else (str(d.paid_at) if d.paid_at else None),
                "notes": d.notes,
                "debt_type": d.debt_type
            }
            for d in debts
        ]
    }

@app.post("/api/hutang")
def catat_hutang_baru(req: DebtCreate, db: Session = Depends(get_db)):
    baru = Debt(
        customer_name=req.customer_name,
        amount=req.amount,
        debt_type=req.debt_type,
        notes=req.notes
    )
    db.add(baru)
    db.commit()
    return {"status": "success", "message": "Catatan hutang berhasil ditambahkan."}

@app.put("/api/hutang/{debt_id}/lunas")
def lunasi_hutang(debt_id: int, db: Session = Depends(get_db)):
    hutang = db.query(Debt).filter(Debt.id == debt_id).first()
    if not hutang:
        raise HTTPException(status_code=404, detail="Hutang tidak ditemukan")
    
    hutang.is_paid = True
    hutang.paid_at = datetime.now()
    
    # Otomatis catat sebagai pemasukan ke Akuntansi jika kasbon pelanggan dibayar
    if hutang.debt_type == "customer":
        pemasukan = Income(
            description=f"Pelunasan Kasbon - {hutang.customer_name}",
            amount=hutang.amount,
            source="Pelunasan Hutang"
        )
        db.add(pemasukan)
    
    db.commit()
    return {"status": "success", "message": "Hutang berhasil dilunasi."}
