const ledger = [
  { date: "20/09/2026", description: "Penjualan harian", debit: 1250000, credit: 0 },
  { date: "20/09/2026", description: "Pembelian stok", debit: 0, credit: 450000 },
  { date: "19/09/2026", description: "Bayar listrik", debit: 0, credit: 150000 },
  { date: "19/09/2026", description: "Penjualan harian", debit: 980000, credit: 0 }
];

const money = value => new Intl.NumberFormat("id-ID", {
  style: "currency",
  currency: "IDR",
  maximumFractionDigits: 0
}).format(value);

function renderLedger() {
  const table = document.getElementById("ledgerTable");
  if (!table) return;

  table.innerHTML = ledger.map(row => `
    <tr>
      <td class="px-4 py-3 text-nowrap">${row.date}</td>
      <td class="px-4 py-3">${row.description}</td>
      <td class="px-4 py-3 text-end text-success fw-semibold">${row.debit ? money(row.debit) : "-"}</td>
      <td class="px-4 py-3 text-end text-danger fw-semibold">${row.credit ? money(row.credit) : "-"}</td>
    </tr>
  `).join("");

  const cash = ledger.reduce((sum, row) => sum + row.debit - row.credit, 0);
  const stock = 3500000;
  const liability = 750000;
  const equity = cash + stock - liability;

  const set = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.textContent = money(value);
  };

  set("valAssetCash", cash);
  set("valAssetStock", stock);
  set("valLiability", liability);
  set("valEquity", equity);
}

function exportCSV() {
  const header = ["Tanggal", "Deskripsi", "Debit", "Kredit"];
  const rows = ledger.map(row => [row.date, row.description, row.debit, row.credit]);
  const csv = [header, ...rows].map(row => row.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "laporan-saku.csv";
  link.click();
  URL.revokeObjectURL(url);
}

document.addEventListener("DOMContentLoaded", renderLedger);