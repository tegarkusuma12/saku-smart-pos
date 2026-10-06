document.addEventListener("DOMContentLoaded", async function () {
    const canvas = document.getElementById("salesChart");
    if (!canvas) return;

    let myChart = null;

    try {
        // 1. Ambil Data History (Aktual) dulu agar UI cepat tampil
        const resStats = await fetch(API_BASE_URL + "/api/dashboard/stats");
        const data = await resStats.json();

        // 2. Format Helper
        const formatRp = (num) => "Rp" + (num || 0).toLocaleString("id-ID");

        // 3. Update Stats Atas
        document.getElementById("valTotalPenjualan").innerText = formatRp(data.total_revenue);
        document.getElementById("valTotalPengeluaran").innerText = formatRp(data.total_expense);
        document.getElementById("valTotalLaba").innerText = formatRp(data.total_profit);
        document.getElementById("valTotalTransaksi").innerText = data.total_transactions || 0;

        // 4. LOGIC CHART (Render Awal)
        const combinedLabels = [...(data.chart_labels || [])];
        const actualData = [...(data.chart_data || [])];
        
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

        myChart = new Chart(canvas, {
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
                prodContainer.innerHTML += '<div class="top-product"><div class="product-rank">' + p.rank + '</div><div class="product-info"><strong>' + p.name + '</strong><small>' + p.sold + ' terjual</small></div><strong>' + formatRp(p.revenue) + '</strong></div>';
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
                
                let html = '<tr>';
                html += '<td>' + t.id + '</td>';
                html += '<td>' + timeStr + '</td>';
                html += '<td>Kasir 1</td>';
                html += '<td>' + t.method + '</td>';
                html += '<td><span class="badge text-bg-success">' + t.status + '</span></td>';
                html += '<td class="text-end">Rp' + (t.total || 0).toLocaleString('id-ID') + '</td>';
                html += '</tr>';
                trxContainer.innerHTML += html;
            });
        }

        // 7. Ambil ML Forecast Asynchronously tanpa nge-block UI
        fetch(API_BASE_URL + "/api/ml/forecast?days=7").then(res => res.json()).then(forecastJson => {
            if (forecastJson && forecastJson.status === "success") {
                const forecastLabels = forecastJson.data.map(item => {
                    const d = new Date(item.date);
                    return d.toLocaleDateString('id-ID', { weekday: 'short', day: '2-digit', month: 'short' });
                });
                const forecastValues = forecastJson.data.map(item => item.predicted_revenue);

                if (forecastValues.length > 0 && data.chart_data && data.chart_data.length > 0) {
                    const lastActualValue = data.chart_data[data.chart_data.length - 1];
                    const predictedData = [...Array(data.chart_labels.length - 1).fill(null), lastActualValue, ...forecastValues];
                    
                    myChart.data.labels = [...data.chart_labels, ...forecastLabels];
                    myChart.data.datasets.push({
                        label: "Prediksi ML",
                        data: predictedData,
                        borderWidth: 3,
                        tension: 0.4,
                        fill: false,
                        borderDash: [5, 5],
                        borderColor: "#f97316",
                        backgroundColor: "transparent"
                    });
                    
                    // Panjangkan data aktual dengan null
                    myChart.data.datasets[0].data = [...data.chart_data, ...Array(forecastLabels.length).fill(null)];
                    myChart.update();
                }
            }
        }).catch(e => {
            console.log("ML Forecast belum tersedia atau gagal dimuat.", e);
        });

    } catch (error) {
        console.error("Gagal memuat dashboard:", error);
    }
});
