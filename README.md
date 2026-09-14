# 🧾 SAKU — Sistem Akuntansi Kasir Usaha

> Asisten keuangan berbasis AI untuk pelaku UMKM Indonesia. Catat pengeluaran, hutang, dan tanya kondisi bisnis pakai bahasa sehari-hari.

---

## 📌 Tentang Proyek

**SAKU (Sistem Akuntansi Kasir Usaha)** adalah aplikasi POS (Point of Sale) dan akuntansi sederhana yang dilengkapi dengan **AI Assistant berbasis LLM**. Dirancang khusus untuk pelaku usaha kecil seperti pemilik warung, pedagang kaki lima, dan UMKM Indonesia yang tidak memiliki latar belakang akuntansi.

Fitur unggulan SAKU adalah **chatbot berbahasa Indonesia** yang memungkinkan pengguna mencatat keuangan hanya dengan mengetik kalimat natural seperti:

- _"tadi bayar listrik 150rb"_
- _"si Budi kasbon 25ribu"_
- _"bulan ini aku untung berapa?"_

### Modul Utama
| Modul | Deskripsi |
|---|---|
| 🛒 Kasir | Transaksi penjualan harian |
| 📒 Akuntansi | Pencatatan pengeluaran, pemasukan, dan hutang |
| 🤖 AI Assistant | Chatbot LLM untuk input & query keuangan via bahasa natural |

---

## 🤖 Tema Chatbot

**Asisten Kasir UMKM** — chatbot yang membantu pemilik warung/usaha kecil mencatat keuangan dan menjawab pertanyaan bisnis tanpa perlu memahami istilah akuntansi.

Chatbot ini menggunakan **LangChain Agent** dengan tools yang terhubung langsung ke database, sehingga setiap percakapan bisa langsung memengaruhi data nyata di aplikasi.

---

## 🚀 Cara Menjalankan

### Prasyarat
- Python 3.11+
- API Key dari [Groq Console](https://console.groq.com) (gratis)

### 1. Clone Repository
```bash
git clone https://github.com/tegarkusuma12/saku-smart-pos.git
cd saku-smart-pos
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup API Key
```bash
cp .env.example .env
```
Buka file `.env`, lalu isi:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
```

### 4. Jalankan Demo Chatbot (Notebook)
Buka file `notebooks/demo_chatbot.ipynb` di VSCode atau Jupyter, lalu jalankan semua sel secara berurutan.

> Sel pertama akan otomatis membuat tabel database dan mengisi data dummy.

Perintah yang tersedia di dalam chat:
| Perintah | Fungsi |
|---|---|
| `exit` | Keluar dari sesi chat |
| `reset` | Hapus riwayat percakapan |
| `history` | Tampilkan riwayat chat |
| `export` | Simpan riwayat ke file JSON |

### 5. Jalankan Aplikasi Web (Opsional)
```bash
streamlit run app/main.py
```

---

## 💬 Contoh Percakapan

```
SAKU: Halo! Aku SAKU Assistant 👋 Ada yang bisa aku bantu?

Kamu: bayar listrik 150rb

SAKU: ✅ Pengeluaran berhasil dicatat!
      📝 bayar listrik
      💸 Rp150.000
      🏷️ Kategori: listrik

Kamu: si Budi kasbon 25ribu

SAKU: ✅ Hutang berhasil dicatat!
      👤 Budi
      💳 Rp25.000
      📌 Tipe: pelanggan kasbon

Kamu: bulan ini aku untung berapa?

SAKU: 📊 Ringkasan Keuangan (bulan ini):
      💰 Total Penjualan    : Rp1.250.000
      ➕ Pemasukan Lain     : Rp200.000
      💸 Total Pengeluaran  : Rp450.000
      📈 Laba Bersih        : Rp1.000.000
```

---

## 🗂️ Struktur Kode

```
saku-smart-pos/
├── app/
│   ├── main.py                  # Entry point Streamlit
│   └── pages/
│       ├── 1_kasir.py           # Halaman kasir/POS
│       ├── 2_chatbot.py         # Halaman AI Assistant (Streamlit UI)
│       └── 3_dashboard.py       # Halaman dashboard & laporan
├── database/
│   ├── connection.py            # Koneksi SQLAlchemy ke SQLite
│   └── models.py                # Model tabel (Transaction, Expense, dll.)
├── src/
│   ├── ai/
│   │   ├── agent.py             # LangChain agent & konfigurasi LLM
│   │   ├── prompts.py           # System prompt SAKU Assistant
│   │   └── tools.py             # Tools yang dipakai agent (catat/query DB)
│   └── akuntansi/
│       ├── pengeluaran.py       # Logic pencatatan pengeluaran
│       ├── pemasukan.py         # Logic pencatatan pemasukan
│       ├── hutang.py            # Logic pencatatan hutang
│       ├── stok.py              # Logic manajemen stok
│       └── transaksi.py         # Logic transaksi kasir
├── data/
│   └── dummy/
│       └── generate_data.py     # Script generate data dummy
├── notebooks/
│   └── demo_chatbot.ipynb       # Demo chatbot interaktif
├── .env.example                 # Template konfigurasi API key
├── requirements.txt
└── README.md
```

### Alur Kerja AI Chatbot
```
User input (bahasa natural)
        ↓
  LangChain Agent (agent.py)
        ↓
  System Prompt (prompts.py)  +  Chat History
        ↓
  LLM: openai/gpt-oss-20b via Groq API
        ↓
  Pilih Tool yang sesuai (tools.py)
        ↓
  Eksekusi Tool → akses Database (SQLite)
        ↓
  Respons balik ke user
```

---

## 🛠️ Teknologi yang Digunakan

| Teknologi | Kegunaan |
|---|---|
| Python 3.11 | Bahasa pemrograman utama |
| LangChain | Framework agent & tool calling |
| Groq API (`openai/gpt-oss-20b`) | LLM provider |
| SQLAlchemy | ORM untuk database |
| SQLite | Database lokal (development) |
| Streamlit | Tampilan web app |

---

## 🤝 Catatan Penggunaan AI

Proyek ini dikembangkan dengan bantuan **Claude (Anthropic)** sebagai AI assistant.

| Bagian | Dikerjakan |
|---|---|
| Arsitektur & desain sistem | Mandiri |
| `database/models.py` | Mandiri + review AI |
| `src/akuntansi/*.py` | Mandiri + review AI |
| `src/ai/agent.py` | Mandiri + bantuan AI |
| `src/ai/prompts.py` | Mandiri |
| `src/ai/tools.py` | Mandiri + review AI |
| `app/pages/2_chatbot.py` | Bantuan AI |
| `notebooks/demo_chatbot.ipynb` | Bantuan AI |
| Debugging & error fixing | Kolaborasi |

---

## 👤 Author

**Tegar Kusuma** — [@tegarkusuma12](https://github.com/tegarkusuma12)