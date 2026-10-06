document.addEventListener("DOMContentLoaded", async function () {
    const canvas = document.getElementById("salesChart");
    if (!canvas) return;

    try {
        // 1. Ambil Data History (Aktual)
        const resStats = await fetch(API_BASE_URL + "/api/dashboard/stats");
        const data = await resStats.json();

        // Ambil ML Forecast (Bisa gagal jika model belum di-train)
        let forecastLabels = [];
        let forecastValues = [];
        try {
            const resForecast = await fetch(API_BASE_URL + "/api/ml/forecast?days=7");
            if (resForecast.ok) {
                const forecastJson = await resForecast.json();
                forecastLabels = forecastJson.data.map(item => {
                    const d = new Date(item.date);
                    return d.toLocaleDateString('id-ID', { weekday: 'short', day: '2-digit', month: 'short' });
                });
                forecastValues = forecastJson.data.map(item => item.predicted_revenue);
            }
        } catch (e) {
            console.log("ML Forecast belum tersedia, melewati grafik prediksi.");
        }

        // 2. Format Helper
        const formatRp = (num) => "Rp" + (num || 0).toLocaleString("id-ID");

        // 3. Update Stats Atas
        document.getElementById("valTotalPenjualan").innerText = formatRp(data.total_revenue);
        document.getElementById("valTotalPengeluaran").innerText = formatRp(data.total_expense);
        document.getElementById("valTotalLaba").innerText = formatRp(data.total_profit);
        document.getElementById("valTotalTransaksi").innerText = data.total_transactions || 0;

        // 4. LOGIC CHART
        const combinedLabels = [...(data.chart_labels || []), ...forecastLabels];
        const actualData = [...(data.chart_data || []), ...Array(forecastLabels.length || 0).fill(null)];
        
        let datasets = [
            {
                label: "Aktual",
                data: actualData,
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                borderColor: "#3b82f6",
                backgroundColor: "rgba(59, 130, 246, 0.1)"
            }
        ];

        if (forecastValues.length > 0 && data.chart_data && data.chart_data.length > 0) {
            const lastActualValue = data.chart_data[data.chart_data.length - 1];
            const predictedData = [...Array(data.chart_labels.length - 1).fill(null), lastActualValue, ...forecastValues];
            datasets.push({
                label: "Prediksi ML",
                data: predictedData,
                borderWidth: 3,
                tension: 0.4,
                fill: false,
                borderDash: [5, 5],
                borderColor: "#f97316",
                backgroundColor: "transparent"
            });
        }

        new Chart(canvas, {
            type: "line",
            data: { labels: combinedLabels, datasets: datasets },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: true, position: 'bottom' } },
                scales: {
                    y: { beginAtZero: true, ticks: { callback: (value) => "Rp" + (value / 1000000).toFixed(1) + " jt" } }
                }
            }
        });

        // 5. Update Top Products
        const prodContainer = document.getElementById("topProductsContainer");
        if (prodContainer && data.top_products) {
            prodContainer.innerHTML = "";
            data.top_products.forEach((p, index) => {
                prodContainer.innerHTML += \
                    <div class="top-product">
                        <div class="product-rank">\</div>
                        <div class="product-info">
                            <strong>\</strong>
                            <small>\ terjual</small>
                        </div>
                        <strong>\</strong>
                    </div>
                \;
            });
        }

        // 6. Update Recent Transactions
        const trxContainer = document.getElementById("recentTransactionsContainer");
        if (trxContainer && data.recent_transactions) {
            trxContainer.innerHTML = "";
            data.recent_transactions.forEach(t => {
                const d = new Date(t.time);
                let timeStr = t.time;
                if (!isNaN(d.getTime())) {
                    timeStr = String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
                }
                
                trxContainer.innerHTML += `
                    <tr>
                        <td>${t.id}</td>
                        <td>${timeStr}</td>
                        <td>Kasir 1</td>
                        <td>${t.method}</td>
                        <td><span class="badge text-bg-success">${t.status}</span></td>
                        <td class="text-end">Rp${(t.total || 0).toLocaleString('id-ID')}</td>
                    </tr>
                `;
            });
        }

    } catch (error) {
        console.error("Gagal memuat dashboard:", error);
    }
});

