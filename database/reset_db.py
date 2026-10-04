from database.connection import engine, Base
from database.models import Category, Product, Transaction, TransactionDetail, InventoryMovement, Expense, Income, Debt

print("🚨 Menghapus semua tabel di database Neon...")
# Perintah ini akan menghapus semua tabel beserta isinya
Base.metadata.drop_all(bind=engine)
print("✅ Database berhasil dikosongkan ke pengaturan pabrik!")