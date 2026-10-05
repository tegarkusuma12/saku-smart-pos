document.addEventListener("DOMContentLoaded", function () {
    const tableBody = document.getElementById("hutangTableBody");
    const formHutang = document.getElementById("formHutang");
    const modalHutangElement = document.getElementById("modalHutang");
    let modalHutang = null;
    
    // Inisialisasi modal jika ada
    if (modalHutangElement) {
        modalHutang = new bootstrap.Modal(modalHutangElement);
    }

    const formatRp = (num) => "Rp" + parseInt(num).toLocaleString("id-ID");
    
    const formatDate = (isoString) => {
        const d = new Date(isoString);
        return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    };

    // Fungsi fetch dengan error handling standar
    async function apiRequest(endpoint, method = "GET", body = null) {
        try {
            const options = { method, headers: { "Content-Type": "application/json" } };
            if (body) options.body = JSON.stringify(body);
            
            const res = await fetch(API_BASE_URL + endpoint, options);
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            return await res.json();
        } catch (error) {
            console.error("API Error:", error);
            Swal.fire("Error!", "Gagal menghubungi server.", "error");
            return null;
        }
    }

    // Fungsi memuat tabel data hutang
    async function loadHutang() {
        const data = await apiRequest("/api/hutang");
        if (!data || !data.data) {
            tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Gagal memuat data</td></tr>`;
            return;
        }

        const hutangList = data.data;
        tableBody.innerHTML = "";
        
        let totalBelumLunas = 0;
        let totalLunas = 0;

        if (hutangList.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted"><i class="bi bi-inbox fs-2 d-block mb-2"></i>Belum ada catatan hutang</td></tr>`;
            return;
        }

        hutangList.forEach(h => {
            // Hitung statistik
            if (h.is_paid) totalLunas += h.amount;
            else totalBelumLunas += h.amount;

            // Render baris tabel
            const tipeBadge = h.debt_type === "supplier" 
                ? `<span class="badge bg-secondary">Supplier</span>` 
                : `<span class="badge bg-info">Pelanggan</span>`;
                
            const statusBadge = h.is_paid 
                ? `<span class="badge bg-success"><i class="bi bi-check-circle me-1"></i>Lunas</span>` 
                : `<span class="badge bg-warning text-dark"><i class="bi bi-clock me-1"></i>Belum Lunas</span>`;

            const btnLunas = h.is_paid 
                ? `<button class="btn btn-sm btn-outline-secondary" disabled>Selesai</button>` 
                : `<button class="btn btn-sm btn-success" onclick="tandaiLunas(${h.id}, '${h.customer_name}')">Lunasi</button>`;

            const rowClass = h.is_paid ? "paid-row" : "unpaid-row";

            tableBody.innerHTML += `
                <tr class="${rowClass}">
                    <td class="ps-4 text-muted small">${formatDate(h.timestamp)}</td>
                    <td>
                        <div class="fw-semibold text-dark">${h.customer_name}</div>
                        <div class="small text-muted">${h.notes || "-"}</div>
                    </td>
                    <td>${tipeBadge}</td>
                    <td class="fw-bold">${formatRp(h.amount)}</td>
                    <td>${statusBadge}</td>
                    <td class="text-center pe-4">${btnLunas}</td>
                </tr>
            `;
        });

        // Update card atas
        document.getElementById("valTotalBelumLunas").innerText = formatRp(totalBelumLunas);
        document.getElementById("valTotalLunas").innerText = formatRp(totalLunas);
    }

    // Fungsi submit hutang baru
    if (formHutang) {
        formHutang.addEventListener("submit", async function(e) {
            e.preventDefault();
            
            const tglVal = document.getElementById("inputTanggal").value;
            const payload = {
                debt_type: document.getElementById("inputTipe").value,
                customer_name: document.getElementById("inputNama").value,
                amount: parseFloat(document.getElementById("inputJumlah").value),
                notes: document.getElementById("inputCatatan").value
            };
            
            // Jika tanggal diisi, format ke ISO string
            if (tglVal) {
                payload.timestamp = new Date(tglVal).toISOString();
            }

            const res = await apiRequest("/api/hutang", "POST", payload);
            if (res && res.status === "success") {
                modalHutang.hide();
                formHutang.reset();
                document.getElementById("inputTanggal").value = "";
                
                Swal.fire({
                    toast: true,
                    position: 'top-end',
                    icon: 'success',
                    title: 'Berhasil dicatat',
                    showConfirmButton: false,
                    timer: 2000
                });
                
                loadHutang();
            }
        });
    }

    // Fungsi global untuk tombol Lunas
    window.tandaiLunas = function(id, nama) {
        Swal.fire({
            title: 'Tandai Lunas?',
            text: `Apakah Anda yakin hutang/kasbon dari ${nama} sudah dibayar lunas?`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Ya, Lunas!',
            cancelButtonText: 'Batal',
            confirmButtonColor: '#10b981'
        }).then(async (result) => {
            if (result.isConfirmed) {
                const res = await apiRequest(`/api/hutang/${id}/lunas`, "PUT");
                if (res && res.status === "success") {
                    Swal.fire({
                        toast: true,
                        position: 'top-end',
                        icon: 'success',
                        title: 'Berhasil dilunasi',
                        showConfirmButton: false,
                        timer: 2000
                    });
                    loadHutang();
                }
            }
        });
    };

    // Muat data saat pertama kali buka
    loadHutang();
});

