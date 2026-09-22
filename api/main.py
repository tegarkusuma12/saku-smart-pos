from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database.connection import get_db
from database.models import Product, Category
from src.ai.agent import run_agent


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
    quantity: int = Field(
        ...,
        gt=0,
        description="Jumlah stok yang ditambahkan"
    )

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

class ChatRequest(BaseModel):
    message: str
    chat_history: list[dict] = Field(default_factory=list)

# ============================================================
# HELPER
# ============================================================

def get_stock_status(stock: int) -> str:

    if stock <= 0:
        return "Habis"

    elif stock <= 10:
        return "Menipis"

    else:
        return "Aman"


def product_to_dict(product: Product):

    return {
        "id": product.id,
        "name": product.name,
        "category_id": product.category_id,
        "category": product.category.name if product.category else None,
        "cost_price": product.cost_price,
        "price": product.price,
        "stock": product.stock,
        "unit": product.unit,
        "description": product.description,
        "is_active": product.is_active,
        "status": get_stock_status(product.stock),
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

    total_stok = sum(
        product.stock or 0
        for product in products
    )

    stok_habis = sum(
        1
        for product in products
        if product.stock <= 0
    )

    stok_menipis = sum(
        1
        for product in products
        if 0 < product.stock <= 10
    )

    stok_aman = sum(
        1
        for product in products
        if product.stock > 10
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
            "total_stok": total_stok,
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

    db.commit()
    db.refresh(product)

    return {
        "status": "success",
        "message": "Stok berhasil ditambahkan.",
        "data": product_to_dict(product)
    }
