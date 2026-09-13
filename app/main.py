import sys
import os

# Tambahkan root directory ke path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from database.connection import engine, Base

# Inisialisasi database saat app pertama dijalankan
Base.metadata.create_all(bind=engine)

# Konfigurasi halaman
st.set_page_config(
    page_title="SAKU - Sistem Akuntansi Kasir Usaha",
    page_icon="💰",
    layout="wide"
)

# Halaman utama / landing
st.title("💰 SAKU")
st.subheader("Sistem Akuntansi Kasir Usaha")
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("🧾 **Kasir**\nInput transaksi penjualan harian")

with col2:
    st.info("📊 **Dashboard**\nLihat laporan & grafik penjualan")

with col3:
    st.info("🤖 **AI Assistant**\nCatat keuangan lewat chat")

st.markdown("---")
st.caption("Pilih menu di sidebar untuk mulai.")