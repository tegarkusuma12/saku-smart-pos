import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from src.ai.agent import run_agent
st.set_page_config(page_title="AI Assistant - SAKU", page_icon="🤖", layout="wide")
st.title("🤖 AI Assistant")
st.caption("Catat keuangan & tanya kondisi bisnis pakai bahasa sehari-hari.")
st.markdown("---")

# ── CONTOH PENGGUNAAN ──────────────────────────────────
with st.expander("💡 Contoh yang bisa kamu tanyakan"):
    st.markdown("""
    **Catat Pengeluaran:**
    - *"tadi beli tepung 2kg sama gula, totalnya 85ribu"*
    - *"bayar listrik 150rb"*
    - *"gaji karyawan bulan ini 1.5jt"*
    
    **Catat Hutang:**
    - *"si Budi kasbon 25rb"*
    - *"beli stok ke supplier, bayar nanti 500rb"*
    
    **Tanya Kondisi Bisnis:**
    - *"bulan ini aku untung berapa?"*
    - *"produk apa yang paling laris minggu ini?"*
    - *"hutang yang belum lunas ada berapa?"*
    """)

# ── CHAT UI ────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Halo! Aku SAKU Assistant 👋 Kamu bisa catat pengeluaran, hutang, atau tanya kondisi keuangan usahamu langsung di sini."
        }
    ]

# Tampilkan riwayat chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Input chat
user_input = st.chat_input("Ketik di sini... contoh: 'bayar listrik 150rb'")

if user_input:
    # Tampilkan pesan user
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Sedang berpikir..."):
            # Kirim semua history kecuali pesan user terakhir
            response = run_agent(
                user_input=user_input,
                chat_history=st.session_state.messages[:-1]
            )
            st.write(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })