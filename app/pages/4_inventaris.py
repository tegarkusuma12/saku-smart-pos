import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
from database.connection import SessionLocal
from database.models import Product

st.set_page_config(page_title="Inventaris - SAKU", page_icon="📦", layout="wide")
st.title("📦 Manajemen Stok & Inventaris")
st.markdown("---")

db = SessionLocal()

# Ambil data produk
produk_list = db.query(Product).all()

col1, col2 = st.columns([1, 2])

# ── KOLOM KIRI: Form Input (Tambah Baru & Restok) ──
with col1:
    tab1, tab2 = st.tabs(["➕ Produk Baru", "📦 Restok Barang"])
    
    # Form Tambah Produk Baru
    with tab1:
        with st.form("form_tambah_produk"):
            st.subheader("Daftarkan Produk Baru")
            nama_baru = st.text_input("Nama Produk")
            harga_baru = st.number_input("Harga Jual (Rp)", min_value=0, step=500)
            stok_awal = st.number_input("Stok Awal", min_value=0, step=1)
            
            submit_baru = st.form_submit_button("Simpan Produk", type="primary", use_container_width=True)
            
            if submit_baru:
                if not nama_baru:
                    st.error("Nama produk tidak boleh kosong!")
                else:
                    produk_baru = Product(
                        name=nama_baru,
                        price=harga_baru,
                        stock=stok_awal,
                        is_active=True # Asumsi ada kolom ini, hapus baris ini jika tidak ada di models.py
                    )
                    db.add(produk_baru)
                    db.commit()
                    st.success(f"Produk '{nama_baru}' berhasil ditambahkan!")
                    st.rerun()

    # Form Restok (Tambah Stok Produk Lama)
    with tab2:
        with st.form("form_restok"):
            st.subheader("Tambah Stok Barang")
            if not produk_list:
                st.info("Belum ada produk untuk di-restok.")
                st.form_submit_button("Simpan Stok", disabled=True)
            else:
                produk_options = {p.name: p for p in produk_list}
                pilihan_restok = st.selectbox("Pilih Produk", options=list(produk_options.keys()))
                tambah_stok = st.number_input("Jumlah Tambahan Stok", min_value=1, step=1, value=10)
                
                submit_restok = st.form_submit_button("Tambah Stok", type="primary", use_container_width=True)
                
                if submit_restok:
                    produk_dipilih = produk_options[pilihan_restok]
                    produk_dipilih.stock += tambah_stok
                    db.commit()
                    st.success(f"Stok '{produk_dipilih.name}' berhasil ditambah {tambah_stok}. Total sekarang: {produk_dipilih.stock}")
                    st.rerun()

# ── KOLOM KANAN: Tabel Data Inventaris ──
with col2:
    st.subheader("📋 Daftar Barang Saat Ini")
    
    if not produk_list:
        st.info("Belum ada data barang di database.")
    else:
        # Konversi ke Pandas DataFrame untuk tampilan tabel yang rapi
        df_produk = pd.DataFrame([{
            "ID": p.id,
            "Nama Produk": p.name,
            "Harga": p.price,
            "Stok": p.stock,
            "Status": "Kritis" if p.stock <= 5 else "Aman"
        } for p in produk_list])
        
        # Highlight warna untuk stok kritis
        def highlight_kritis(val):
            color = '#ff4b4b' if val == 'Kritis' else ''
            return f'color: {color}'
        
        st.dataframe(
            df_produk.style.map(highlight_kritis, subset=['Status']),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Harga": st.column_config.NumberColumn(format="Rp %d")
            }
        )

db.close()