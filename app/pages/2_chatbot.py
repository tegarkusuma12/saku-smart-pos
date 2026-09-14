import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from src.ai.agent import run_agent

# ── PAGE CONFIG ───────────────────────────────────────
st.set_page_config(page_title="AI Assistant - SAKU", page_icon="🤖", layout="wide")
st.title("🤖 AI Assistant")
st.caption("Catat keuangan & tanya kondisi bisnis pakai bahasa sehari-hari.")
st.markdown("---")

# ── INIT SESSION STATE ────────────────────────────────
PESAN_AWAL = {
    "role": "assistant",
    "content": (
        "Halo! Aku SAKU Assistant 👋\n\n"
        "Kamu bisa catat pengeluaran, hutang, atau tanya kondisi "
        "keuangan usahamu langsung di sini. Mau mulai dari mana?"
    )
}

if "messages" not in st.session_state:
    st.session_state.messages = [PESAN_AWAL]

# ── SIDEBAR: SPECIAL COMMANDS ─────────────────────────
with st.sidebar:
    st.header("⚙️ Kontrol Chat")
    st.markdown("---")

    # COMMAND 1: Reset Chat
    if st.button("🔄 Reset Chat", use_container_width=True):
        st.session_state.messages = [PESAN_AWAL]
        st.rerun()

    st.caption("Hapus semua riwayat dan mulai percakapan baru.")
    st.markdown("---")

    # COMMAND 2: Export Chat
    chat_export = json.dumps(
        {
            "diekspor_pada": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "jumlah_pesan": len(st.session_state.messages),
            "percakapan": st.session_state.messages,
        },
        ensure_ascii=False,
        indent=2,
    )
    st.download_button(
        label="💾 Export Riwayat Chat",
        data=chat_export,
        file_name=f"saku_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
        use_container_width=True,
    )
    st.caption("Unduh riwayat percakapan dalam format JSON.")
    st.markdown("---")

    # Info statistik percakapan (bonus)
    st.subheader("📊 Statistik")
    total = len(st.session_state.messages)
    user_msg = sum(1 for m in st.session_state.messages if m["role"] == "user")
    st.metric("Total Pesan", total)
    st.metric("Pesanmu", user_msg)

# ── CONTOH PENGGUNAAN ─────────────────────────────────
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

# ── CHAT UI ───────────────────────────────────────────
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

    # Proses & tampilkan respons agent
    with st.chat_message("assistant"):
        with st.spinner("Sedang berpikir..."):
            try:
                response = run_agent(
                    user_input=user_input,
                    chat_history=st.session_state.messages[:-1]
                )
            except Exception as e:
                response = (
                    f"⚠️ Maaf, terjadi kesalahan teknis: {str(e)}\n\n"
                    "Coba lagi ya, atau ketik ulang pesanmu."
                )
        st.write(response)

    st.session_state.messages.append({"role": "assistant", "content": response})