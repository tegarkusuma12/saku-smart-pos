# src/pipeline/etl.py
import os
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH      = os.path.join(BASE_DIR, "saku.db")
RAW_DIR      = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR= os.path.join(BASE_DIR, "data", "processed")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}")


# ── EXTRACT ───────────────────────────────────────────────────────────────────

def extract():
    """Ekstrak semua tabel dari SQLite ke data/raw/ sebagai CSV."""

    tables = {
        "products":             "SELECT * FROM products",
        "transactions":         "SELECT * FROM transactions",
        "transaction_details":  "SELECT * FROM transaction_details",
        "expenses":             "SELECT * FROM expenses",
        "incomes":              "SELECT * FROM incomes",
        "debts":                "SELECT * FROM debts",
        "inventory_movements":  "SELECT * FROM inventory_movements",
    }

    dfs = {}
    for name, query in tables.items():
        df = pd.read_sql(query, engine)
        df.to_csv(os.path.join(RAW_DIR, f"{name}.csv"), index=False)
        dfs[name] = df
        print(f"  [extract] {name}: {len(df)} rows")

    return dfs


# ── TRANSFORM ─────────────────────────────────────────────────────────────────

def transform(dfs: dict):
    """Buat analytical datasets di data/processed/."""

    transactions   = dfs["transactions"].copy()
    details        = dfs["transaction_details"].copy()
    products       = dfs["products"].copy()
    expenses       = dfs["expenses"].copy()
    incomes        = dfs["incomes"].copy()
    movements      = dfs["inventory_movements"].copy()

    # Parse timestamps
    transactions["timestamp"] = pd.to_datetime(transactions["timestamp"])
    expenses["timestamp"]     = pd.to_datetime(expenses["timestamp"])
    incomes["timestamp"]      = pd.to_datetime(incomes["timestamp"])
    movements["timestamp"]    = pd.to_datetime(movements["timestamp"])

    transactions["date"]  = transactions["timestamp"].dt.date
    expenses["date"]      = expenses["timestamp"].dt.date
    incomes["date"]       = incomes["timestamp"].dt.date
    movements["date"]     = movements["timestamp"].dt.date

    # ── 1. daily_sales.csv ────────────────────────────────────────────────────
    # Ringkasan penjualan per hari — input utama forecasting
    daily_sales = (
        transactions
        .groupby("date")
        .agg(
            total_revenue    = ("total_amount", "sum"),
            total_transaksi  = ("id", "count"),
        )
        .reset_index()
        .sort_values("date")
    )
    daily_sales.to_csv(os.path.join(PROCESSED_DIR, "daily_sales.csv"), index=False)
    print(f"  [transform] daily_sales: {len(daily_sales)} rows")

    # ── 2. product_sales.csv ──────────────────────────────────────────────────
    # Performa per produk — untuk product segmentation dan ranking
    product_sales = (
        details
        .merge(products[["id", "name", "item_type", "cost_price"]], 
               left_on="product_id", right_on="id", suffixes=("", "_prod"))
        .groupby(["product_id", "name"])
        .agg(
            total_qty      = ("quantity", "sum"),
            total_revenue  = ("subtotal", "sum"),
            total_hpp      = ("cost_price", lambda x: (x * details.loc[x.index, "quantity"]).sum()),
            avg_harga_jual = ("selling_price", "mean"),
        )
        .reset_index()
    )
    product_sales["gross_profit"] = product_sales["total_revenue"] - product_sales["total_hpp"]
    product_sales["margin_pct"]   = (
        product_sales["gross_profit"] / product_sales["total_revenue"] * 100
    ).round(2)
    product_sales = product_sales.sort_values("total_revenue", ascending=False)
    product_sales.to_csv(os.path.join(PROCESSED_DIR, "product_sales.csv"), index=False)
    print(f"  [transform] product_sales: {len(product_sales)} rows")

        # ── 3. inventory_daily.csv ────────────────────────────────────────────────
    movements_named = movements.merge(
        products[["id", "name", "unit"]], 
        left_on="product_id", right_on="id"
    )

    # Sort kronologis per produk dulu
    movements_named = movements_named.sort_values(["product_id", "timestamp"])

    # Reconstruct stock_akhir dari cumsum 
    movements_named["stock_akhir"] = (
        movements_named.groupby("product_id")["quantity_change"].cumsum()
    )

    inventory_daily = (
        movements_named
        .groupby(["date", "product_id", "name", "unit"])
        .agg(
            net_change  = ("quantity_change", "sum"),
            stock_akhir = ("stock_akhir", "last"),
        )
        .reset_index()
        .sort_values(["product_id", "date"])
    )
    inventory_daily.to_csv(os.path.join(PROCESSED_DIR, "inventory_daily.csv"), index=False)
    print(f"  [transform] inventory_daily: {len(inventory_daily)} rows")

    # ── 4. financial_summary.csv ──────────────────────────────────────────────
    # Ringkasan keuangan per hari — untuk laporan laba rugi
    daily_revenue = (
        transactions.groupby("date")["total_amount"].sum()
        .reset_index().rename(columns={"total_amount": "revenue"})
    )
    daily_expense = (
        expenses.groupby("date")["amount"].sum()
        .reset_index().rename(columns={"amount": "expense"})
    )
    daily_income = (
        incomes.groupby("date")["amount"].sum()
        .reset_index().rename(columns={"amount": "income_lain"})
    )

    financial = (
        daily_revenue
        .merge(daily_expense,  on="date", how="outer")
        .merge(daily_income,   on="date", how="outer")
        .fillna(0)
        .sort_values("date")
    )
    financial["laba_kotor"] = financial["revenue"] - financial["expense"]
    financial["laba_bersih"] = financial["laba_kotor"] + financial["income_lain"]
    financial.to_csv(os.path.join(PROCESSED_DIR, "financial_summary.csv"), index=False)
    print(f"  [transform] financial_summary: {len(financial)} rows")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def run_etl():
    print(f"\n{'='*50}")
    print(f"SAKU ETL Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    print("\n[1/2] Extracting...")
    dfs = extract()

    print("\n[2/2] Transforming...")
    transform(dfs)

    print(f"\n✅ ETL selesai.")
    print(f"   Raw      → {RAW_DIR}")
    print(f"   Processed → {PROCESSED_DIR}")


if __name__ == "__main__":
    run_etl()