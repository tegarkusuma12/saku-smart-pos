document.addEventListener("DOMContentLoaded", async function () {
    const canvas = document.getElementById("salesChart");
    if (!canvas) return;

    try {
        // 1. Ambil Data History (Aktual) dan ML Forecast (Prediksi)
        const resStats = await fetch("http://127.0.0.1:8000/api/dashboard/stats");
        const data = await resStats.json();

        const resForecast = await fetch("http://127.0.0.1:8000/api/ml/forecast?days=7");
        const forecastJson = await resForecast.json();

        // 2. Format Helper
        const formatRp = (num) => "Rp" + num.toLocaleString("id-ID");

        // 3. Update Stats Atas
        document.getElementById("valTotalPenjualan").innerText = formatRp(data.total_revenue);
        document.getElementById("valTotalPengeluaran").innerText = formatRp(data.total_expense);
        document.getElementById("valTotalLaba").innerText = formatRp(data.total_profit);
        document.getElementById("valTotalTransaksi").innerText = data.total_transactions;

        // 4. LOGIC CHART: GABUNGAN AKTUAL + PREDIKSI ML
        
        // Format tanggal prediksi dari API (contoh: "2026-09-26" -> "Sab, 26 Sep")
        const forecastLabels = forecastJson.data.map(item => {
            const d = new Date(item.date);
            return d.toLocaleDateString('id-ID', { weekday: 'short', day: '2-digit', month: 'short' });
        });
        const forecastValues = forecastJson.data.map(item => item.predicted_revenue);

        // Gabungkan Label X (7 Hari Aktual + 7 Hari Prediksi)
        const combinedLabels = [...data.chart_labels, ...forecastLabels];
        
        // Dataset 1: Aktual (Data histori + sisanya kosong)
        const actualData = [...data.chart_data, ...Array(7).fill(null)];
        
        // Dataset 2: Prediksi (Kosong di awal, disambung dari titik akhir aktual)
        const lastActualValue = data.chart_data[data.chart_data.length - 1];
        const predictedData = [...Array(6).fill(null), lastActualValue, ...forecastValues];

        // Render Chart
        new Chart(canvas, {
            type: "line",
            data: {
                labels: combinedLabels,
                datasets: [
                    {
                        label: "Aktual",
                        data: actualData,
                        borderWidth: 3,
                        tension: 0.4,
                        fill: true,
                        borderColor: "#3b82f6", // Biru
                        backgroundColor: "rgba(59, 130, 246, 0.1)"
                    },
                    {
                        label: "Prediksi ML",
                        data: predictedData,
                        borderWidth: 3,
                        tension: 0.4,
                        fill: false,
                        borderDash: [5, 5], // Efek garis putus-putus
                        borderColor: "#f97316", // Oranye
                        backgroundColor: "transparent"
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { display: true, position: 'bottom' } // Tampilkan legend
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => "Rp" + (value / 1000000).toFixed(1) + " jt"
                        }
                    }
                }
            }
        });

        // 5. Update Top Products
        const prodContainer = document.getElementById("topProductsContainer");
        prodContainer.innerHTML = "";
        data.top_products.forEach(p => {
            prodContainer.innerHTML += `
                <div class="top-product">
                    <div class="product-rank">${p.rank}</div>
                    <div class="product-info">
                        <strong>${p.name}</strong>
                        <small>${p.sold} terjual</small>
                    </div>
                    <strong>${formatRp(p.revenue)}</strong>
                </div>
            `;
        });

        // 6. Update Recent Transactions
        const trxContainer = document.getElementById("recentTransactionsContainer");
        trxContainer.innerHTML = "";
        data.recent_transactions.forEach(t => {
            trxContainer.innerHTML += `
                <tr>
                    <td>${t.id}</td>
                    <td>${t.time}</td>
                    <td>${t.cashier}</td>
                    <td>${t.method}</td>
                    <td><span class="badge text-bg-success">${t.status}</span></td>
                    <td class="text-end">${formatRp(t.total)}</td>
                </tr>
            `;
        });

    } catch (error) {
        console.error("Gagal memuat dashboard:", error);
    }
});