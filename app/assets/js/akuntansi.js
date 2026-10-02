let ledger = [];

document.addEventListener("DOMContentLoaded", async function () {
    await loadLedger();
});

// Load Ledger dari Backend
async function loadLedger() {
    try {
        const table = document.getElementById("ledgerTable");
        if(table) table.innerHTML = `<tr><td colspan="5" class="text-center py-4"><i class="fa-solid fa-spinner fa-spin me-2"></i> Memuat data buku besar...</td></tr>`;
        
        const response = await fetch(`${API_BASE_URL}/api/akuntansi/ledger`);
        const result = await response.json();
        
        if (response.ok && result.status === "success") {
            ledger = result.data;
            renderLedger();
            calculateSummary();
        } else {
            console.error("Gagal mengambil data ledger.");
        }
    } catch (err) {
        console.error("Error fetching ledger:", err);
    }
}

function renderLedger() {
    const table = document.getElementById("ledgerTable");
    if (!table) return;

    if (!ledger.length) {
        table.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">Belum ada riwayat transaksi.</td></tr>`;
        return;
    }

    table.innerHTML = ledger.map(function (item) {
        return `
            <tr>
                <td>${item.date}</td>
                <td><strong>${item.account}</strong></td>
                <td>${item.description}</td>
                <td class="text-end">${item.debit > 0 ? formatRupiah(item.debit) : "-"}</td>
                <td class="text-end">${item.credit > 0 ? formatRupiah(item.credit) : "-"}</td>
            </tr>
        `;
    }).join("");
}

function calculateSummary() {
    const totalDebit = ledger.reduce((sum, item) => sum + item.debit, 0);
    const totalCredit = ledger.reduce((sum, item) => sum + item.credit, 0);

    const cash = ledger.filter(item => item.account === "Kas").reduce((sum, item) => sum + item.debit - item.credit, 0);
    const stock = ledger.filter(item => item.account === "Persediaan").reduce((sum, item) => sum + item.debit - item.credit, 0);
    const equity = totalDebit - totalCredit + cash + stock;

    const cashElement = document.getElementById("cashValue");
    const stockElement = document.getElementById("stockValue");
    const equityElement = document.getElementById("equityValue");

    if (cashElement) cashElement.textContent = formatRupiah(cash);
    if (stockElement) stockElement.textContent = formatRupiah(stock);
    if (equityElement) equityElement.textContent = formatRupiah(equity);
}

function formatRupiah(value) {
    return new Intl.NumberFormat("id-ID", {
        style: "currency",
        currency: "IDR",
        maximumFractionDigits: 0
    }).format(value);
}

function exportCSV() {
    let csv = "Tanggal,Akun,Keterangan,Debit,Kredit\n";
    ledger.forEach(function (item) {
        csv += `${item.date},"${item.account}","${item.description}",${item.debit},${item.credit}\n`;
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "laporan-akuntansi.csv";
    link.click();
    URL.revokeObjectURL(url);
}