import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from database.connection import SessionLocal
from database.models import Product
from src.kasir.transaksi import proses_checkout

st.set_page_config(page_title="Kasir - SAKU", page_icon="🧾", layout="wide")
st.title("🧾 Kasir")
st.markdown("---")

db = SessionLocal()

# Ambil produk yang masih aktif & ada stoknya
produk_list = db.query(Product).filter(
    Product.is_active == True,
    Product.stock > 0
).all()

if not produk_list:
    st.warning("Belum ada produk tersedia. Tambahkan produk terlebih dahulu.")
    db.close()
    st.stop()

# Inisialisasi keranjang di session state
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []

# Layout 2 kolom
col_kiri, col_kanan = st.columns([3, 2])

# ── KOLOM KIRI: Pilih Produk ──────────────────────────
with col_kiri:
    st.subheader("Pilih Produk")

    produk_options = {f"{p.name} (Stok: {p.stock}) - Rp{p.price:,.0f}": p for p in produk_list}
    pilihan = st.selectbox("Produk", options=list(produk_options.keys()))
    produk_dipilih = produk_options[pilihan]

    qty = st.number_input(
        "Jumlah", 
        min_value=1, 
        max_value=produk_dipilih.stock, 
        value=1
    )

    if st.button("➕ Tambah ke Keranjang", use_container_width=True):
        # Cek apakah produk sudah ada di keranjang
        existing = next(
            (item for item in st.session_state.keranjang 
             if item["product_id"] == produk_dipilih.id), 
            None
        )
        if existing:
            existing["qty"] += qty
        else:
            st.session_state.keranjang.append({
                "product_id": produk_dipilih.id,
                "nama": produk_dipilih.name,
                "harga": produk_dipilih.price,
                "qty": qty
            })
        st.success(f"✅ {produk_dipilih.name} ditambahkan!")

# ── KOLOM KANAN: Keranjang & Checkout ─────────────────
with col_kanan:
    st.subheader("🛒 Keranjang")

    if not st.session_state.keranjang:
        st.info("Keranjang masih kosong.")
    else:
        total = 0
        for i, item in enumerate(st.session_state.keranjang):
            subtotal = item["harga"] * item["qty"]
            total += subtotal
            col_nama, col_hapus = st.columns([4, 1])
            with col_nama:
                st.write(f"**{item['nama']}** x{item['qty']} = Rp{subtotal:,.0f}")
            with col_hapus:
                if st.button("🗑️", key=f"hapus_{i}"):
                    st.session_state.keranjang.pop(i)
                    st.rerun()

        st.markdown("---")
        st.subheader(f"Total: Rp{total:,.0f}")

        metode = st.selectbox("Metode Pembayaran", ["Cash", "QRIS", "Kasbon"])

        col_bayar, col_reset = st.columns(2)

        with col_bayar:
            if st.button("💳 Proses Bayar", use_container_width=True, type="primary"):
                result = proses_checkout(
                    db=db,
                    keranjang=[{"product_id": i["product_id"], "qty": i["qty"]} 
                               for i in st.session_state.keranjang],
                    payment_method=metode
                )
                if result["status"] == "success":
                    st.success(f"✅ Transaksi berhasil! Total: Rp{result['total_amount']:,.0f}")
                    st.session_state.keranjang = []
                    st.rerun()
                else:
                    st.error(f"❌ {result['message']}")

        with col_reset:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.keranjang = []
                st.rerun()

db.close()