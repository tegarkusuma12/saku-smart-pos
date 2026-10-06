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
// ======================================
// FASE 4: CRUD Pemasukan & Pengeluaran
// ======================================

// Helper fetch API
async function apiPost(endpoint, data) {
    try {
        const res = await fetch(API_BASE_URL + endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });
        return await res.json();
    } catch (e) {
        console.error(e);
        return { status: "error" };
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const formIn = document.getElementById("formPemasukan");
    const formEx = document.getElementById("formPengeluaran");

    if (formIn) {
        formIn.addEventListener("submit", async function(e) {
            e.preventDefault();
            const tgl = document.getElementById("inTgl").value;
            let sourceVal = document.getElementById("inSumber").value;
            if (sourceVal === "custom") {
                sourceVal = document.getElementById("inSumberCustom").value;
            }
            const payload = {
                source: sourceVal,
                description: document.getElementById("inKet").value,
                amount: parseFloat(document.getElementById("inJumlah").value)
            };
            if (tgl) payload.timestamp = new Date(tgl).toISOString();

            const res = await apiPost("/api/akuntansi/income", payload);
            if (res.status === "success") {
                bootstrap.Modal.getInstance(document.getElementById('modalPemasukan')).hide();
                formIn.reset();
                Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'Berhasil dicatat', showConfirmButton: false, timer: 2000 });
                loadLedger();
            } else {
                Swal.fire("Error", "Gagal menyimpan data", "error");
            }
        });
    }

    if (formEx) {
        formEx.addEventListener("submit", async function(e) {
            e.preventDefault();
            const tgl = document.getElementById("exTgl").value;
            let catVal = document.getElementById("exKategori").value;
            if (catVal === "custom") {
                catVal = document.getElementById("exKategoriCustom").value;
            }
            const payload = {
                category: catVal,
                description: document.getElementById("exKet").value,
                amount: parseFloat(document.getElementById("exJumlah").value)
            };
            if (tgl) payload.timestamp = new Date(tgl).toISOString();

            const res = await apiPost("/api/akuntansi/expense", payload);
            if (res.status === "success") {
                bootstrap.Modal.getInstance(document.getElementById('modalPengeluaran')).hide();
                formEx.reset();
                Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'Berhasil dicatat', showConfirmButton: false, timer: 2000 });
                loadLedger();
            } else {
                Swal.fire("Error", "Gagal menyimpan data", "error");
            }
        });
    }
});


function toggleCustomInput(selectElem, customInputId) {
    const customInput = document.getElementById(customInputId);
    if (selectElem.value === "custom") {
        customInput.classList.remove("d-none");
        customInput.required = true;
        customInput.focus();
    } else {
        customInput.classList.add("d-none");
        customInput.required = false;
        customInput.value = "";
    }
}


