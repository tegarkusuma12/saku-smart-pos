const API_BASE_URL = "http://127.0.0.1:8000";
let inventory = [];

/* ============================================================
INITIALIZATION
============================================================ */
document.addEventListener("DOMContentLoaded", async function () {
    setupInventoryEvents();
    await loadInventory();
});

/* ============================================================
SETUP EVENT
============================================================ */
function setupInventoryEvents() {
    const search = document.getElementById("inventorySearch");
    const filter = document.getElementById("stockFilter");

    if (search) {
        search.addEventListener("input", renderInventory);
    }

    if (filter) {
        filter.addEventListener("change", renderInventory);
    }

    const addProductButton = document.getElementById("addProductButton");
    if (addProductButton) {
        addProductButton.addEventListener("click", function () {
            alert("Fitur tambah produk akan kita buat pada tahap berikutnya.");
        });
    }
}

/* ============================================================
LOAD INVENTORY
============================================================ */
async function loadInventory() {
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE_URL}/api/inventory`);

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        const result = await response.json();

        if (result.status !== "success") {
            throw new Error("API mengembalikan status yang tidak valid.");
        }

        inventory = result.data || [];
        renderInventory();
        await loadInventoryStats();

    } catch (error) {
        console.error("Gagal mengambil data inventory:", error);
        showError("Gagal mengambil data inventaris dari server.");
    }
}

/* ============================================================
LOAD INVENTORY STATS
============================================================ */
async function loadInventoryStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/inventory/stats`);

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        const result = await response.json();

        if (result.status !== "success" || !result.data) {
            throw new Error("Data statistik tidak valid.");
        }

        const stats = result.data;
        const totalProducts = document.getElementById("totalProducts");
        const lowStockProducts = document.getElementById("lowStockProducts");
        const outOfStockProducts = document.getElementById("outOfStockProducts");

        if (totalProducts) {
            totalProducts.textContent = stats.total_produk;
        }

        if (lowStockProducts) {
            lowStockProducts.textContent = stats.stok_menipis;
        }

        if (outOfStockProducts) {
            outOfStockProducts.textContent = stats.stok_habis;
        }

    } catch (error) {
        console.error("Gagal mengambil statistik inventory:", error);
    }
}

/* ============================================================
RENDER INVENTORY
============================================================ */
function renderInventory() {
    const table = document.getElementById("inventoryTable");

    if (!table) {
        return;
    }

    const searchValue = document.getElementById("inventorySearch")?.value.toLowerCase().trim() || "";
    const filterValue = document.getElementById("stockFilter")?.value || "all";

    const filtered = inventory.filter(function (item) {
        const productName = (item.name || "").toLowerCase();
        const productCode = generateProductCode(item.id).toLowerCase();
        const category = (item.category || "").toLowerCase();

        const matchesSearch = productName.includes(searchValue) || productCode.includes(searchValue) || category.includes(searchValue);
        const matchesFilter = filterValue === "all" || item.status === filterValue;

        return matchesSearch && matchesFilter;
    });

    if (filtered.length === 0) {
        table.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4 text-muted">
                    <i class="fa-solid fa-box-open me-2"></i>
                    Tidak ada produk yang sesuai.
                </td>
            </tr>
        `;
        return;
    }

    table.innerHTML = filtered.map(function (item) {
        const badgeClass = getStockBadgeClass(item.status);
        const code = generateProductCode(item.id);

        return `
            <tr>
                <td>${code}</td>
                <td><strong>${escapeHtml(item.name)}</strong></td>
                <td>${escapeHtml(item.category || "-")}</td>
                <td>${item.stock} ${escapeHtml(item.unit || "pcs")}</td>
                <td>${formatRupiah(item.price)}</td>
                <td><span class="stock-badge ${badgeClass}">${escapeHtml(item.status)}</span></td>
                <td class="text-end">
                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="addStock(${item.id})" title="Tambah stok">
                        <i class="fa-solid fa-plus"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

/* ============================================================
STOCK STATUS
============================================================ */
function getStockBadgeClass(status) {
    if (status === "Menipis") {
        return "stock-low";
    }
    if (status === "Habis") {
        return "stock-empty";
    }
    return "stock-safe";
}

/* ============================================================
PRODUCT CODE
============================================================ */
function generateProductCode(id) {
    return `PRD-${String(id).padStart(3, "0")}`;
}

/* ============================================================
RESTOCK
============================================================ */
async function addStock(productId) {
    const product = inventory.find(item => item.id === productId);

    if (!product) {
        alert("Produk tidak ditemukan.");
        return;
    }

    const input = prompt(`Masukkan jumlah stok yang ingin ditambahkan untuk "${product.name}":`, "10");

    if (input === null) {
        return;
    }

    const quantity = Number(input);

    if (!Number.isInteger(quantity) || quantity <= 0) {
        alert("Jumlah stok harus berupa angka bulat lebih dari 0.");
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/inventory/${productId}/restock`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                quantity: quantity
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Gagal melakukan restock.");
        }

        if (result.status !== "success") {
            throw new Error(result.message || "Gagal melakukan restock.");
        }

        alert(`Stok ${product.name} berhasil ditambahkan ${quantity} ${product.unit || "pcs"}.`);
        
        await loadInventory();

    } catch (error) {
        console.error("Gagal melakukan restock:", error);
        alert(`Restock gagal: ${error.message}`);
    }
}

/* ============================================================
LOADING
============================================================ */
function showLoading() {
    const table = document.getElementById("inventoryTable");
    
    if (!table) {
        return;
    }

    table.innerHTML = `
        <tr>
            <td colspan="7" class="text-center py-4 text-muted">
                <i class="fa-solid fa-spinner fa-spin me-2"></i>
                Memuat data inventaris...
            </td>
        </tr>
    `;
}

/* ============================================================
ERROR
============================================================ */
function showError(message) {
    const table = document.getElementById("inventoryTable");
    
    if (!table) {
        return;
    }

    table.innerHTML = `
        <tr>
            <td colspan="7" class="text-center py-4 text-danger">
                <i class="fa-solid fa-circle-exclamation me-2"></i>
                ${escapeHtml(message)}
            </td>
        </tr>
    `;
}

/* ============================================================
FORMAT RUPIAH
============================================================ */
function formatRupiah(value) {
    return new Intl.NumberFormat("id-ID", {
        style: "currency",
        currency: "IDR",
        maximumFractionDigits: 0
    }).format(value || 0);
}

/* ============================================================
ESCAPE HTML
============================================================ */
function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}