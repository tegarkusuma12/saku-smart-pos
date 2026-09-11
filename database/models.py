from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
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
    
    category = relationship("Category", back_populates="products")
    transaction_details = relationship("TransactionDetail", back_populates="product")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Float, nullable=False)
    payment_method = Column(String) # Cash, QRIS, Kasbon
    
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
    """Tabel untuk mencatat pengeluaran operasional warung/UMKM"""
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)

class Debt(Base):
    """Tabel untuk mencatat kasbon/hutang pelanggan"""
    __tablename__ = "debts"
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_paid = Column(Boolean, default=False)