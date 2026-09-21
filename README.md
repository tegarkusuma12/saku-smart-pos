# 🧾 SAKU — Sistem Akuntansi Kasir Usaha

> Asisten keuangan berbasis AI untuk pelaku UMKM. Catat pengeluaran, hutang, dan tanya kondisi bisnis pakai bahasa sehari-hari.

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
| 📦 Inventaris | Manajemen stok barang dan pemantauan ketersediaan produk |
| 🤖 AI Assistant | Chatbot LLM untuk input & query keuangan via bahasa natural |

---

## 🤖 Tema Chatbot

**Asisten Kasir UMKM** — chatbot yang membantu pemilik warung/usaha kecil mencatat keuangan dan menjawab pertanyaan bisnis tanpa perlu memahami istilah akuntansi.

Chatbot ini menggunakan **LangChain Agent** dengan tools yang terhubung langsung ke database, sehingga setiap percakapan bisa langsung memengaruhi data nyata di aplikasi.

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

## 🛠️ Teknologi yang Digunakan

| Teknologi | Kegunaan |
|---|---|
| Python 3.11 | Bahasa pemrograman utama |
| LangChain | Framework agent & tool calling |
| Groq API | LLM provider |
| SQLAlchemy | ORM untuk database |
| SQLite | Database lokal (development) |
| PostgreSQL / Supabase | Database production |
| Streamlit | UI/UX & deployment |
| FastAPI | Server backend |
| HTML, CSS, JS | Komponen UI tambahan |

## 🤝 Catatan Penggunaan AI

Proyek ini dikembangkan dengan bantuan **Claude (Anthropic)** sebagai AI assistant.

| Bagian | Dikerjakan |
|---|---|
| Konsep, arsitektur & desain sistem | Mandiri |
| `database/models.py` | Mandiri + review AI |
| `src/akuntansi/*.py` | Mandiri + review AI |
| `src/ai/agent.py` | Mandiri + bantuan AI |
| `src/ai/prompts.py` | Mandiri |
| `src/ai/tools.py` | Mandiri + review AI |
| `app/pages/2_chatbot.py` | Bantuan AI |
| `notebooks/demo_chatbot.ipynb` | Mandiri + review AI |
| Debugging & error fixing | Bantuan AI |

---

## 📄 Lisensi

Proyek ini dibuat untuk keperluan **portofolio akademik dan pengembangan diri**.
Bebas digunakan sebagai referensi dengan mencantumkan kredit.

---

## 👤 Author

**Tegar Kusuma** — [@tegarkusuma12](https://github.com/tegarkusuma12)