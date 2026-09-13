import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
from database.connection import SessionLocal
from database.models import Transaction, TransactionDetail, Product, Expense, Income, Debt

st.set_page_config(page_title="Dashboard - SAKU", page_icon="📊", layout="wide")
st.title("📊 Dashboard")
st.markdown("---")

db = SessionLocal()

# ── METRIK UTAMA ───────────────────────────────────────
st.subheader("Ringkasan Keuangan")

# Ambil semua data
transaksi = db.query(Transaction).all()
pengeluaran = db.query(Expense).all()
pemasukan = db.query(Income).all()
hutang_belum_lunas = db.query(Debt).filter(Debt.is_paid == False).all()

total_penjualan = sum(t.total_amount for t in transaksi)
total_pengeluaran = sum(e.amount for e in pengeluaran)
total_pemasukan_lain = sum(i.amount for i in pemasukan)
total_hutang = sum(d.amount for d in hutang_belum_lunas)
laba_bersih = total_penjualan + total_pemasukan_lain - total_pengeluaran

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Penjualan", f"Rp{total_penjualan:,.0f}")
col2.metric("📉 Total Pengeluaran", f"Rp{total_pengeluaran:,.0f}")
col3.metric("📈 Laba Bersih", f"Rp{laba_bersih:,.0f}")
col4.metric("⚠️ Hutang Belum Lunas", f"Rp{total_hutang:,.0f}")

st.markdown("---")

# ── GRAFIK PENJUALAN HARIAN ────────────────────────────
st.subheader("📈 Tren Penjualan Harian")

if transaksi:
    df_trx = pd.DataFrame([{
        "tanggal": t.timestamp.date(),
        "total": t.total_amount
    } for t in transaksi])

    df_harian = df_trx.groupby("tanggal")["total"].sum().reset_index()
    df_harian = df_harian.sort_values("tanggal")
    df_harian.columns = ["Tanggal", "Total Penjualan"]
    df_harian = df_harian.set_index("Tanggal")

    st.line_chart(df_harian)
else:
    st.info("Belum ada data transaksi.")

st.markdown("---")

# ── 2 KOLOM: PRODUK TERLARIS + PENGELUARAN ────────────
col_kiri, col_kanan = st.columns(2)

# Produk Terlaris
with col_kiri:
    st.subheader("🏆 Produk Terlaris")

    details = db.query(TransactionDetail).all()
    if details:
        df_detail = pd.DataFrame([{
            "product_id": d.product_id,
            "qty": d.quantity
        } for d in details])

        # Gabungkan dengan nama produk
        produk_map = {p.id: p.name for p in db.query(Product).all()}
        df_detail["nama"] = df_detail["product_id"].map(produk_map)
        df_terlaris = df_detail.groupby("nama")["qty"].sum().reset_index()
        df_terlaris.columns = ["Produk", "Total Terjual"]
        df_terlaris = df_terlaris.sort_values("Total Terjual", ascending=False).head(5)
        df_terlaris = df_terlaris.set_index("Produk")

        st.bar_chart(df_terlaris)
    else:
        st.info("Belum ada data penjualan.")

# Pengeluaran per Kategori
with col_kanan:
    st.subheader("💸 Pengeluaran per Kategori")

    if pengeluaran:
        df_expense = pd.DataFrame([{
            "kategori": e.category or "lainnya",
            "amount": e.amount
        } for e in pengeluaran])

        df_kategori = df_expense.groupby("kategori")["amount"].sum().reset_index()
        df_kategori.columns = ["Kategori", "Total"]
        df_kategori = df_kategori.sort_values("Total", ascending=False)
        df_kategori = df_kategori.set_index("Kategori")

        st.bar_chart(df_kategori)
    else:
        st.info("Belum ada data pengeluaran.")

st.markdown("---")

# ── STOK KRITIS ────────────────────────────────────────
st.subheader("⚠️ Stok Kritis (Stok ≤ 5)")

produk_kritis = db.query(Product).filter(
    Product.stock <= 5,
    Product.is_active == True
).all()

if produk_kritis:
    df_kritis = pd.DataFrame([{
        "Produk": p.name,
        "Stok": p.stock,
        "Harga": f"Rp{p.price:,.0f}"
    } for p in produk_kritis])
    st.dataframe(df_kritis, use_container_width=True)
else:
    st.success("✅ Semua stok aman.")

db.close()