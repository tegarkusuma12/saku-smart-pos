# 🧾 SAKU — AI-Powered POS & Business Analytics for Indonesian UMKM

> Asisten keuangan berbasis AI untuk pelaku UMKM. Catat pengeluaran, hutang, dan tanya kondisi bisnis pakai bahasa sehari-hari.
>
> 📊 **[Notebook: Sales Forecasting](notebooks/sales_forecasting.ipynb)** · 📦 **[Notebook: Inventory Recommendation](notebooks/inventory_recommendation.ipynb)** · 🤖 **[Notebook: Chatbot Demo](notebooks/demo_chatbot.ipynb)**

---

## 📌 Tentang Proyek

**SAKU (Sistem Akuntansi Kasir Usaha)** adalah platform POS (Point of Sale) dan business analytics yang dilengkapi **AI Assistant berbasis LLM**. Dirancang khusus untuk pelaku usaha kecil seperti pemilik warung, pedagang kaki lima, dan UMKM Indonesia.

Proyek ini mendemonstrasikan **end-to-end data science pipeline**:
- 🔧 **Data Engineering** — ETL pipeline, synthetic data generation (120 hari)
- 📊 **Exploratory Data Analysis** — tren penjualan, analisis produk, pola weekend
- 🤖 **Machine Learning** — sales forecasting (Random Forest / XGBoost)
- 💡 **Prescriptive Analytics** — rekomendasi restock otomatis berdasarkan forecast + current stock
- 🗣️ **NLP / LLM Integration** — chatbot bahasa Indonesia yang memahami "bayar listrik 150rb"

### Fitur Unggulan

**Chatbot berbahasa Indonesia** yang memungkinkan pengguna mencatat keuangan dan bertanya tentang bisnis:

```text
Kamu: bayar listrik 150rb
SAKU: ✅ Pengeluaran dicatat! 💸 Rp150.000 🏷️ listrik

Kamu: besok butuh stok apa?
SAKU: 📦 Rekomendasi Restock:
      🔴 Chitato — stok 5, restock 17 unit
      🟠 Telur 1kg — stok 12, sisa ~8 hari
```

### Modul Utama

| Modul | Deskripsi |
|---|---|
| 🛒 Kasir | Transaksi penjualan harian, multi payment (Cash/QRIS/Kasbon) |
| 📒 Akuntansi | Pencatatan pengeluaran, pemasukan, dan hutang |
| 📦 Inventaris | Manajemen stok, restock otomatis, inventory movement tracking |
| 🤖 AI Assistant | Chatbot LLM untuk input & query via bahasa natural |
| 📊 Analytics | Forecasting penjualan, rekomendasi restock, inventory health |

---

## 🏗️ Arsitektur Sistem

```text
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (HTML/CSS/JS)                   │
│              Kasir · Inventaris · Chat · Dashboard              │
└─────────────────────────┬───────────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────────────┐
│                      FastAPI Backend                            │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐     │
│  │ Kasir API│  │ Inventory API│  │ ML Prediction API      │     │
│  │          │  │              │  │ /api/ml/forecast       │     │
│  │          │  │              │  │ /api/ml/restock-rec    │     │
│  └──────────┘  └──────────────┘  └────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              LangChain Agent (SakuBot)                   │   │
│  │  Tools: catat_pengeluaran · ringkasan_keuangan           │   │
│  │         prediksi_penjualan · rekomendasi_restock         │   │
│  └──────────────────────────────┬───────────────────────────┘   │
│                                 │                               │
│  ┌──────────────────┐  ┌────────▼──────────┐                    │
│  │ SQLAlchemy ORM   │  │ Groq LLM API      │                    │
│  │ (7 tabel)        │  │ (openai/gpt-oss)  │                    │
│  └────────┬─────────┘  └───────────────────┘                    │
│           │                                                     │
│  ┌────────▼─────────┐  ┌──────────────────┐                     │
│  │   SQLite DB      │  │ ML Model (pkl)   │                     │
│  │   (saku.db)      │  │ (RF/XGBoost)     │                     │
│  └──────────────────┘  └──────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Science Pipeline

### 1. Data Generation & ETL
- **Synthetic data**: 120 hari data transaksi realistis (weekend/trend patterns) dengan 19 produk warung Indonesia
- **ETL Pipeline** (`src/pipeline/etl.py`): Extract dari SQLite → Transform → Load ke CSV
- **Output**: `daily_sales.csv`, `product_sales.csv`, `inventory_daily.csv`, `financial_summary.csv`

### 2. Exploratory Data Analysis ([notebook](notebooks/01_data_exploration.ipynb))
- Distribusi revenue harian
- Pola penjualan per hari (weekday vs weekend)
- Korelasi antar metrik keuangan

### 3. Sales Analysis ([notebook](notebooks/sales_analysis.ipynb))
- Hari penjualan tertinggi
- Produk yang sering dibeli bersamaan
- Tren revenue & margin analysis

### 4. Inventory Analysis ([notebook](notebooks/inventory_analysis.ipynb))
- Inventory turnover per produk
- Days of stock remaining
- Restock interval patterns

### 5. Sales Forecasting ([notebook](notebooks/sales_forecasting.ipynb))
- **Features**: `day_of_week`, `is_weekend`, `lag_1`, `lag_7`, `rolling_mean_7`, `rolling_mean_14`
- **Models**: Naive baseline → Moving Average → Random Forest → XGBoost
- **Evaluation**: MAE, RMSE, MAPE dengan TimeSeriesSplit
- **Output**: Trained model di `models/sales_forecast.pkl`

### 6. Inventory Recommendation ([notebook](notebooks/inventory_recommendation.ipynb))
- **Prescriptive analytics**: demand forecast × safety factor − current stock = restock qty
- **Urgency levels**: KRITIS / SEGERA / PERLU / AMAN
- Output di-serve via API dan accessible via chatbot

---

## 🤖 AI Chatbot — 9 LangChain Tools

| Tool | Fungsi |
|---|---|
| `catat_pengeluaran` | Catat pengeluaran (listrik, gaji, bahan) |
| `catat_pemasukan` | Catat pemasukan di luar kasir |
| `catat_hutang` | Catat hutang pelanggan/supplier |
| `ringkasan_keuangan` | Ringkasan laba rugi per periode |
| `cek_hutang` | Daftar hutang belum lunas |
| `produk_terlaris` | Ranking produk terlaris |
| `cek_stok_kritis` | Produk yang stoknya menipis |
| `prediksi_penjualan` | 🆕 Prediksi revenue N hari ke depan (ML) |
| `rekomendasi_restock` | 🆕 Rekomendasi restock berdasarkan ML + inventory |

---

## 🛠️ Tech Stack

| Teknologi | Kegunaan |
|---|---|
| Python 3.11 | Bahasa pemrograman utama |
| FastAPI | Backend REST API |
| SQLAlchemy + SQLite | ORM & database |
| LangChain + Groq | LLM agent framework + API provider |
| scikit-learn, XGBoost | Machine learning models |
| Pandas, NumPy | Data processing |
| Matplotlib, Seaborn | Visualisasi |
| HTML/CSS/JS | Frontend UI |
| Docker | Containerization & deployment |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [Groq API Key](https://console.groq.com)

### Setup
```bash
# Clone
git clone https://github.com/tegarkusuma12/saku-smart-pos.git
cd saku-smart-pos

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env → masukkan GROQ_API_KEY

# Generate data & run ETL
python data/dummy/generate_data.py
python -m src.pipeline.etl

# Run API
uvicorn api.main:app --reload
```

### Docker
```bash
docker build -t saku-pos .
docker run -p 8000:8000 --env-file .env saku-pos
```

---

## 🤝 Catatan Penggunaan AI

Proyek ini dikembangkan dengan bantuan AI assistant.

| Bagian | Dikerjakan |
|---|---|
| Konsep, arsitektur & desain sistem | Mandiri |
| `database/models.py` | Mandiri + review AI |
| `src/akuntansi/*.py` | Mandiri + review AI |
| `src/ai/agent.py` | Mandiri + bantuan AI |
| `src/ai/tools.py` | Mandiri + review AI |
| `src/ml/forecasting.py` | Mandiri + bantuan AI |
| `notebooks/*.ipynb` | Mandiri + review AI |
| Frontend HTML/CSS/JS | Mandiri + bantuan AI |
| Debugging & error fixing | Bantuan AI |

---

## 👤 Author

**Tegar Kusuma** — [@tegarkusuma12](https://github.com/tegarkusuma12)