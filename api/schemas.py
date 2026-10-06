from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from database.models import ItemType

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

class ExpenseCreate(BaseModel):
    description: str
    amount: float
    category: str
    timestamp: datetime = None

class IncomeCreate(BaseModel):
    description: str
    amount: float
    source: str
    timestamp: datetime = None

class DebtCreate(BaseModel):
    customer_name: str
    amount: float
    debt_type: str = "customer"
    notes: str | None = None
    timestamp: datetime | None = None
