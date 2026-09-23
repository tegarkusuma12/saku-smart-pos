from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database.connection import get_db
from database.models import Product, Transaction, TransactionDetail, Debt
from src.ai.agent import run_agent
from src.akuntansi.pengeluaran import catat_pengeluaran


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
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
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
    cost_price: float = Field(..., ge=0)
    price: float = Field(..., ge=0)
    stock: int = Field(0, ge=0)
    unit: str = Field("pcs", min_length=1)
    description: str | None = None


class ProductUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    category_id: int | None = None
    cost_price: float = Field(..., ge=0)
    price: float = Field(..., ge=0)
    unit: str = Field("pcs", min_length=1)
    description: str | None = None


class StockAdjustmentRequest(BaseModel):
    quantity: int
    reason: str = Field(..., min_length=1)

class TransactionItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class TransactionRequest(BaseModel):
    items: list[TransactionItemRequest]
    payment_method: str = Field(..., pattern="^(Cash|QRIS|Kasbon)$")
    customer_name: str | None = None   # wajib 
    notes: str | None = None
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
        "unit": product.unit,
        "description": product.description,
        "is_active": product.is_active,
        "status": get_stock_status(product.stock, product.min_stock),
    }


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

    deskripsi = f"Beli {product.name} {request.quantity} {product.unit}"
    if request.catatan:
        deskripsi += f" — {request.catatan}"
    catat_pengeluaran(db, deskripsi, request.total_harga, "bahan_baku")

    db.commit()
    db.refresh(product)

    return {
        "status": "success",
        "message": "Stok berhasil ditambahkan dan pengeluaran tercatat.",
        "data": product_to_dict(product)
    }
