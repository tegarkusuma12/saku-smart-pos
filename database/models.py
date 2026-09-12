from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base

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
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    unit = Column(String, default="pcs")
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    category = relationship("Category", back_populates="products")
    transaction_details = relationship("TransactionDetail", back_populates="product")

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
    subtotal = Column(Float, nullable=False)
    transaction = relationship("Transaction", back_populates="details")
    product = relationship("Product", back_populates="transaction_details")

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