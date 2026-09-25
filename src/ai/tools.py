import json
from langchain.tools import tool
from database.connection import SessionLocal
from database.models import Transaction, Expense, Income, Debt, Product, TransactionDetail
from src.akuntansi.pengeluaran import catat_pengeluaran
from src.akuntansi.pemasukan import catat_pemasukan
from src.akuntansi.hutang import catat_hutang, get_hutang_belum_lunas
from sqlalchemy import func
from sqlalchemy import desc

# ── TOOLS CATAT DATA ──────────────────────────────────

@tool
def tool_catat_pengeluaran(deskripsi: str, nominal: float, kategori: str | None = None) -> str:
    """
    Gunakan tool ini untuk mencatat pengeluaran operasional warung.
    Contoh: bayar listrik, beli bahan baku, gaji karyawan.
    
    Args:
        deskripsi: Keterangan pengeluaran
        nominal: Jumlah uang yang dikeluarkan
        kategori: Kategori pengeluaran (bahan_baku/listrik/gaji/operasional/lainnya)
    """
    db = SessionLocal()
    try:
        data = catat_pengeluaran(db, deskripsi, nominal, kategori)
        return f"✅ Pengeluaran berhasil dicatat!\n📝 {data.description}\n💸 Rp{data.amount:,.0f}\n🏷️ Kategori: {data.category or 'lainnya'}"
    except ValueError as e:
        return f"❌ Gagal mencatat: {str(e)}"
    finally:
        db.close()

@tool
def tool_catat_pemasukan(deskripsi: str, nominal: float, sumber: str | None = None) -> str:
    """
    Gunakan tool ini untuk mencatat pemasukan di luar transaksi kasir.
    Contoh: pesanan katering, transfer dari pelanggan, pembayaran pesanan khusus.
    
    Args:
        deskripsi: Keterangan pemasukan
        nominal: Jumlah uang yang diterima
        sumber: Sumber pemasukan (katering/transfer/lainnya)
    """
    db = SessionLocal()
    try:
        data = catat_pemasukan(db, deskripsi, nominal, sumber)
        return f"✅ Pemasukan berhasil dicatat!\n📝 {data.description}\n💰 Rp{data.amount:,.0f}\n📌 Sumber: {data.source or 'lainnya'}"
    except ValueError as e:
        return f"❌ Gagal mencatat: {str(e)}"
    finally:
        db.close()

@tool
def tool_catat_hutang(nama: str, nominal: float, tipe: str = "customer") -> str:
    """
    Gunakan tool ini untuk mencatat hutang/kasbon.
    Tipe 'customer' = pelanggan kasbon ke warung.
    Tipe 'supplier' = warung hutang ke supplier.
    
    Args:
        nama: Nama pelanggan atau supplier
        nominal: Jumlah hutang
        tipe: Tipe hutang (customer/supplier)
    """
    db = SessionLocal()
    try:
        data = catat_hutang(db, nama, nominal, tipe)
        label = "pelanggan kasbon" if tipe == "customer" else "hutang ke supplier"
        db.commit()
        return f"✅ Hutang berhasil dicatat!\n👤 {data.customer_name}\n💳 Rp{data.amount:,.0f}\n📌 Tipe: {label}"
    except ValueError as e:
        return f"❌ Gagal mencatat: {str(e)}"
    finally:
        db.close()

# ── TOOLS QUERY DATA ──────────────────────────────────

@tool
def tool_ringkasan_keuangan(periode: str = "bulan_ini") -> str:
    """
    Gunakan tool ini untuk menjawab pertanyaan tentang kondisi keuangan.
    Contoh: 'bulan ini untung berapa?', 'total pengeluaran minggu ini?'
    
    Args:
        periode: Periode waktu (hari_ini/minggu_ini/bulan_ini)
    """
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        now = datetime.now()

        if periode == "hari_ini":
            start = now.replace(hour=0, minute=0, second=0)
        elif periode == "minggu_ini":
            start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # bulan_ini
            start = now.replace(day=1, hour=0, minute=0, second=0)

        # Hitung dari masing-masing tabel
        total_penjualan = db.query(func.sum(Transaction.total_amount)).filter(
            Transaction.timestamp >= start
        ).scalar() or 0

        total_pengeluaran = db.query(func.sum(Expense.amount)).filter(
            Expense.timestamp >= start
        ).scalar() or 0

        total_pemasukan_lain = db.query(func.sum(Income.amount)).filter(
            Income.timestamp >= start
        ).scalar() or 0

        laba = total_penjualan + total_pemasukan_lain - total_pengeluaran

        return f"""📊 Ringkasan Keuangan ({periode.replace('_', ' ')}):
                💰 Total Penjualan    : Rp{total_penjualan:,.0f}
                ➕ Pemasukan Lain     : Rp{total_pemasukan_lain:,.0f}
                💸 Total Pengeluaran  : Rp{total_pengeluaran:,.0f}
                📈 Laba Bersih        : Rp{laba:,.0f}"""
    finally:
        db.close()

@tool
def tool_cek_hutang() -> str:
    """
    Gunakan tool ini untuk mengecek daftar hutang yang belum lunas.
    Contoh: 'siapa saja yang masih kasbon?', 'hutangku ke supplier berapa?'
    """
    db = SessionLocal()
    try:
        hutang_list = get_hutang_belum_lunas(db)
        if not hutang_list:
            return "✅ Tidak ada hutang yang belum lunas!"

        customer = [h for h in hutang_list if h.debt_type == "customer"]
        supplier = [h for h in hutang_list if h.debt_type == "supplier"]

        result = "📋 Daftar Hutang Belum Lunas:\n"

        if customer:
            result += "\n👥 Kasbon Pelanggan:\n"
            for h in customer:
                result += f"  • {h.customer_name}: Rp{h.amount:,.0f}\n"
            result += f"  Total: Rp{sum(h.amount for h in customer):,.0f}\n"

        if supplier:
            result += "\n🏪 Hutang ke Supplier:\n"
            for h in supplier:
                result += f"  • {h.customer_name}: Rp{h.amount:,.0f}\n"
            result += f"  Total: Rp{sum(h.amount for h in supplier):,.0f}\n"

        return result
    except Exception as e:
        return f"❌ Gagal mengambil data: {str(e)}"
    finally:
        db.close()

@tool
def tool_produk_terlaris(limit: int = 5) -> str:
    """
    Gunakan tool ini untuk mengecek produk yang stoknya hampir habis.
    Contoh: 'stok apa yang mau habis?', 'produk apa yang perlu direstok?'
    
    Args:
        threshold: Batas minimum stok yang dianggap kritis (mendukung desimal, misal 2.5 kg)
    """
    db = SessionLocal()
    try:
        hasil = (
            db.query(
                Product.name,
                func.sum(TransactionDetail.quantity).label("total_terjual")
            )
            .join(TransactionDetail, Product.id == TransactionDetail.product_id)
            .group_by(Product.name)
            .order_by(desc("total_terjual"))
            .limit(limit)
            .all()
        )

        if not hasil:
            return "Belum ada data penjualan."

        result = f"🏆 {limit} Produk Terlaris:\n"
        for i, (nama, total) in enumerate(hasil, 1):
            result += f"  {i}. {nama}: {total} terjual\n"
        return result
    except Exception as e:
        return f"❌ Gagal mengambil data: {str(e)}"
    finally:
        db.close()

@tool
def tool_cek_stok_kritis(threshold: float = 5.0) -> str:
    """
    Gunakan tool ini untuk mengecek produk yang stoknya hampir habis.
    Contoh: 'stok apa yang mau habis?', 'produk apa yang perlu direstok?'
    
    Args:
        threshold: Batas minimum stok yang dianggap kritis
    """
    db = SessionLocal()
    try:
        produk_kritis = db.query(Product).filter(
            Product.stock <= threshold,
            Product.is_active == True
        ).all()

        if not produk_kritis:
            return f"✅ Semua stok aman (di atas {threshold} unit)."

        result = f"⚠️ Produk dengan stok ≤ {threshold}:\n"
        for p in produk_kritis:
            result += f"  • {p.name}: sisa {p.stock} {p.unit}\n"
        return result
    except Exception as e:
        return f"❌ Gagal mengambil data: {str(e)}"
    finally:
        db.close()


# Kumpulkan semua tools untuk dipakai di agent
def get_all_tools():
    return [
        tool_catat_pengeluaran,
        tool_catat_pemasukan,
        tool_catat_hutang,
        tool_ringkasan_keuangan,
        tool_cek_hutang,
        tool_produk_terlaris,
        tool_cek_stok_kritis,
    ]