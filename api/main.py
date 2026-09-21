from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Product


app = FastAPI(
    title="SAKU Smart POS API",
    description="Backend API untuk SAKU Smart POS",
    version="1.0.0",
)


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
def test_database(db: Session = Depends(get_db)):
    total_products = db.query(Product).count()

    return {
        "status": "success",
        "database": "connected",
        "total_products": total_products
    }

# ============================================================
# INVENTORY
# ============================================================

@app.get("/api/inventory")
def get_inventory(db: Session = Depends(get_db)):
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