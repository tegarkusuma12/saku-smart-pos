# database/models.py
import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base

class ItemType(str, enum.Enum):
    PRODUK_DIJUAL = "produk_dijual"
    BAHAN_BAKU    = "bahan_baku"
    KEMASAN       = "kemasan"
    PERLENGKAPAN  = "perlengkapan"
    LAINNYA       = "lainnya"

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    item_type   = Column(
        SAEnum(ItemType),
        default=ItemType.PRODUK_DIJUAL,
        nullable=False
    )
    cost_price  = Column(Float, default=0.0)
    price       = Column(Float, nullable=True) 
    stock       = Column(Float, default=0.0)
    min_stock   = Column(Float, default=5.0)
    unit        = Column(String(30), default="pcs")
    description = Column(String(255), nullable=True)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  
    category            = relationship("Category", back_populates="products")
    transaction_details = relationship("TransactionDetail", back_populates="product")
    movements           = relationship("InventoryMovement", back_populates="product")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now())
    total_amount = Column(Float, nullable=False)
    payment_method = Column(String)  # Cash, QRIS, Kasbon
    notes = Column(String, nullable=True)
    details = relationship("TransactionDetail", back_populates="transaction")

class TransactionDetail(Base):
    __tablename__ = "transaction_details"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    cost_price = Column(Float, nullable=False)    
    selling_price = Column(Float, nullable=False) 
    subtotal = Column(Float, nullable=False)
    transaction = relationship("Transaction", back_populates="details")
    product = relationship("Product", back_populates="transaction_details")

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id         = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    timestamp = Column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        index=True
        )
    quantity_change = Column(Float, nullable=False)  
    stock_after     = Column(Float, nullable=False) 

    reason       = Column(String(50), nullable=False)
    # nilai: "purchase" | "sale" | "adjustment" | "waste" | "opening_stock"

    reference_id = Column(Integer, nullable=True)
    # isi transaction.id kalau reason=sale
    # isi expense.id kalau reason=purchase
    # null kalau manual

    notes   = Column(String(255), nullable=True)
    product = relationship("Product", back_populates="movements")

class Expense(Base):
    """Pengeluaran operasional warung/UMKM"""
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now())
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String)  # "bahan_baku", "listrik", "gaji", "lainnya"

class Income(Base):
    """Pemasukan di luar transaksi kasir"""
    __tablename__ = "incomes"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now())
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    source = Column(String)  # "katering", "transfer", dll

class Debt(Base):
    """Hutang pelanggan (kasbon) atau hutang warung ke supplier"""
    __tablename__ = "debts"
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    is_paid = Column(Boolean, default=False)
    paid_at = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)
    debt_type = Column(String, default="customer")  # "customer" atau "supplier"