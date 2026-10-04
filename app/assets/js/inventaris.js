let inventory = [];
let categories = [];
let restockTotalTouched = false;
const modalCache = {};

const MOVEMENT_LABELS = {
    purchase: "Pembelian",
    sale: "Penjualan",
    adjustment: "Koreksi Stok",
    waste: "Rusak / Hilang",
    opening_stock: "Stok Awal"
};

/* ============================================================
HELPER
============================================================ */
function getModal(id) {
    if (!modalCache[id]) {
        modalCache[id] = new bootstrap.Modal(document.getElementById(id));
    }
    return modalCache[id];
}

function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const el = document.createElement("div");
    el.className = `toast align-items-center text-bg-${type} border-0`;
    el.setAttribute("role", "alert");
    el.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${escapeHtml(message)}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>`;
    container.appendChild(el);
    el.addEventListener("hidden.bs.toast", () => el.remove());
    new bootstrap.Toast(el, { delay: 4000 }).show();
}

// FastAPI mengirim detail berupa string (HTTPException) atau array (validasi 422)
function getErrorMessage(result, fallback) {
    if (!result || !result.detail) return fallback;
    if (typeof result.detail === "string") return result.detail;
    if (Array.isArray(result.detail)) return result.detail.map(d => d.msg).join(", ");
    return fallback;
}

async function apiRequest(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        headers: { "Content-Type": "application/json" },
        ...options
    });

    let result = null;
    try {
        result = await response.json();
    } catch (_) { /* respons bukan JSON */ }

    if (!response.ok) {
        throw new Error(getErrorMessage(result, `Server error (${response.status})`));
    }
    return result;
}

function formatRupiah(value) {
    return new Intl.NumberFormat("id-ID", {
        style: "currency",
        currency: "IDR",
        maximumFractionDigits: 0
    }).format(value || 0);
}

function formatNumber(value) {
    return new Intl.NumberFormat("id-ID", { maximumFractionDigits: 2 }).format(value || 0);
}

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function findProduct(id) {
    return inventory.find(item => item.id === id);
}

/* ============================================================
INITIALIZATION
============================================================ */
document.addEventListener("DOMContentLoaded", async function () {
    setupInventoryEvents();
    await Promise.all([loadCategories(), loadInventory()]);
});

function setupInventoryEvents() {
    document.getElementById("inventorySearch")?.addEventListener("input", renderInventory);
    document.getElementById("stockFilter")?.addEventListener("change", renderInventory);

    document.getElementById("addProductButton")?.addEventListener("click", () => openProductModal());

    document.getElementById("productForm")?.addEventListener("submit", async e => {
        e.preventDefault();
        await saveProduct();
    });

    document.getElementById("productCategory")?.addEventListener("change", e => {
        document.getElementById("newCategoryGroup")
            .classList.toggle("d-none", e.target.value !== "__new__");
    });

    // Restock
    document.getElementById("restockForm")?.addEventListener("submit", async e => {
        e.preventDefault();
        await submitRestock();
    });
    document.getElementById("restockQuantity")?.addEventListener("input", e => {
        if (restockTotalTouched) return;
        const product = findProduct(parseInt(document.getElementById("restockProductId").value));
        const qty = parseFloat(e.target.value) || 0;
        document.getElementById("restockTotal").value = Math.round(qty * (product?.cost_price || 0));
    });
    document.getElementById("restockTotal")?.addEventListener("input", () => {
        restockTotalTouched = true;
    });

    // Penyesuaian
    document.getElementById("adjustForm")?.addEventListener("submit", async e => {
        e.preventDefault();
        await submitAdjust();
    });
    document.getElementById("adjustType")?.addEventListener("change", e => {
        document.getElementById("adjustHelp").textContent = e.target.value === "waste"
            ? "Isi jumlah yang rusak/hilang (otomatis mengurangi stok)."
            : "Positif menambah stok, negatif mengurangi stok.";
    });
}

/* ============================================================
KATEGORI
============================================================ */
async function loadCategories() {
    try {
        const result = await apiRequest("/api/kategori");
        categories = result.data || [];
    } catch (error) {
        console.error("Gagal memuat kategori:", error);
        showToast("Gagal memuat daftar kategori.", "warning");
    }
    renderCategoryOptions(null);
}

function renderCategoryOptions(selectedId) {
    const select = document.getElementById("productCategory");
    if (!select) return;

    select.innerHTML =
        `<option value="">- Tanpa kategori -</option>` +
        categories.map(c =>
            `<option value="${c.id}" ${c.id === selectedId ? "selected" : ""}>${escapeHtml(c.name)}</option>`
        ).join("") +
        `<option value="__new__">+ Tambah kategori baru...</option>`;
}

/* ============================================================
LOAD INVENTORY
============================================================ */
async function loadInventory() {
    try {
        showLoading();
        const result = await apiRequest("/api/inventory");
        inventory = result.data || [];
        renderInventory();
        await loadInventoryStats();
    } catch (error) {
        console.error("Gagal mengambil data inventory:", error);
        showError("Gagal mengambil data inventaris dari server.");
    }
}

async function loadInventoryStats() {
    try {
        const result = await apiRequest("/api/inventory/stats");
        const stats = result.data;
        if (!stats) return;

        const setText = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };
        setText("totalProducts", stats.total_produk);
        setText("lowStockProducts", stats.stok_menipis);
        setText("outOfStockProducts", stats.stok_habis);
    } catch (error) {
        console.error("Gagal mengambil statistik inventory:", error);
    }
}

/* ============================================================
RENDER INVENTORY
============================================================ */
function renderInventory() {
    const table = document.getElementById("inventoryTable");
    if (!table) return;

    const searchValue = document.getElementById("inventorySearch")?.value.toLowerCase().trim() || "";
    const filterValue = document.getElementById("stockFilter")?.value || "all";

    const filtered = inventory.filter(item => {
        const haystack = [
            item.name,
            generateProductCode(item.id),
            item.category
        ].map(v => (v || "").toLowerCase());

        const matchesSearch = haystack.some(v => v.includes(searchValue));
        const matchesFilter = filterValue === "all" || item.status === filterValue;
        return matchesSearch && matchesFilter;
    });

    if (filtered.length === 0) {
        table.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4 text-muted">
                    <i class="fa-solid fa-box-open me-2"></i>Tidak ada produk yang sesuai.
                </td>
            </tr>`;
        return;
    }

    table.innerHTML = filtered.map(item => `
        <tr>
            <td>${generateProductCode(item.id)}</td>
            <td>
                <strong>${escapeHtml(item.name)}</strong>
                ${item.item_type && item.item_type !== "produk_dijual"
                    ? `<div class="small text-muted">${escapeHtml(item.item_type.replace("_", " "))}</div>` : ""}
            </td>
            <td>${escapeHtml(item.category || "-")}</td>
            <td>${formatNumber(item.stock)} ${escapeHtml(item.unit || "pcs")}</td>
            <td>${formatRupiah(item.price)}</td>
            <td><span class="stock-badge ${getStockBadgeClass(item.status)}">${escapeHtml(item.status)}</span></td>
            <td class="text-end">
                <div class="btn-group btn-group-sm">
                    <button type="button" class="btn btn-outline-primary" onclick="openRestockModal(${item.id})" title="Restock">
                        <i class="fa-solid fa-plus"></i>
                    </button>
                    <button type="button" class="btn btn-outline-secondary" onclick="openAdjustModal(${item.id})" title="Penyesuaian stok">
                        <i class="fa-solid fa-sliders"></i>
                    </button>
                    <button type="button" class="btn btn-outline-secondary" onclick="openHistoryModal(${item.id})" title="Riwayat stok">
                        <i class="fa-solid fa-clock-rotate-left"></i>
                    </button>
                    <button type="button" class="btn btn-outline-secondary" onclick="openProductModal(${item.id})" title="Edit">
                        <i class="fa-solid fa-pen"></i>
                    </button>
                    <button type="button" class="btn btn-outline-danger" onclick="deleteProduct(${item.id})" title="Nonaktifkan">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>`).join("");
}

function getStockBadgeClass(status) {
    if (status === "Menipis") return "stock-low";
    if (status === "Habis") return "stock-empty";
    return "stock-safe";
}

function generateProductCode(id) {
    return `PRD-${String(id).padStart(3, "0")}`;
}

/* ============================================================
TAMBAH / EDIT PRODUK
============================================================ */
function openProductModal(productId = null) {
    document.getElementById("productForm").reset();
    document.getElementById("productId").value = "";
    document.getElementById("newCategoryGroup").classList.add("d-none");
    document.getElementById("productStock").disabled = false;
    document.getElementById("productStockHelp").classList.add("d-none");
    document.getElementById("productModalTitle").textContent = "Tambah Produk Baru";
    renderCategoryOptions(null);

    if (productId !== null) {
        const p = findProduct(productId);
        if (!p) {
            showToast("Produk tidak ditemukan.", "danger");
            return;
        }

        document.getElementById("productModalTitle").textContent = "Edit Produk";
        document.getElementById("productId").value = p.id;
        document.getElementById("productName").value = p.name;
        document.getElementById("productType").value = p.item_type || "produk_dijual";
        renderCategoryOptions(p.category_id);
        document.getElementById("productCost").value = p.cost_price ?? 0;
        document.getElementById("productPrice").value = p.price ?? 0;
        document.getElementById("productStock").value = p.stock;
        document.getElementById("productStock").disabled = true;
        document.getElementById("productStockHelp").classList.remove("d-none");
        document.getElementById("productMinStock").value = p.min_stock ?? 5;
        document.getElementById("productUnit").value = p.unit || "pcs";
        document.getElementById("productDescription").value = p.description || "";
    }

    getModal("productModal").show();
}

async function saveProduct() {
    const id = document.getElementById("productId").value;
    const isEdit = id !== "";
    const submitBtn = document.getElementById("productSubmit");
    submitBtn.disabled = true;

    try {
        // Kategori (bisa membuat baru)
        const categoryValue = document.getElementById("productCategory").value;
        let categoryId = null;

        if (categoryValue === "__new__") {
            const newName = document.getElementById("newCategoryName").value.trim();
            if (!newName) throw new Error("Nama kategori baru wajib diisi.");

            const created = await apiRequest("/api/kategori", {
                method: "POST",
                body: JSON.stringify({ name: newName })
            });
            categoryId = created.data.id;
            await loadCategories();
        } else if (categoryValue !== "") {
            categoryId = parseInt(categoryValue);
        }

        const payload = {
            name: document.getElementById("productName").value.trim(),
            category_id: categoryId,
            item_type: document.getElementById("productType").value,
            cost_price: parseFloat(document.getElementById("productCost").value) || 0,
            price: parseFloat(document.getElementById("productPrice").value) || 0,
            min_stock: parseFloat(document.getElementById("productMinStock").value) || 0,
            unit: document.getElementById("productUnit").value.trim(),
            description: document.getElementById("productDescription").value.trim() || null
        };

        if (!isEdit) {
            payload.stock = parseFloat(document.getElementById("productStock").value) || 0;
        }

        const result = await apiRequest(isEdit ? `/api/produk/${id}` : "/api/produk", {
            method: isEdit ? "PUT" : "POST",
            body: JSON.stringify(payload)
        });

        getModal("productModal").hide();
        showToast(result.message || "Produk berhasil disimpan.");
        await loadInventory();
    } catch (error) {
        console.error("Gagal menyimpan produk:", error);
        showToast(error.message, "danger");
    } finally {
        submitBtn.disabled = false;
    }
}

/* ============================================================
HAPUS (NONAKTIFKAN) PRODUK
============================================================ */
async function deleteProduct(productId) {
    const p = findProduct(productId);
    if (!p) return;

    const ok = confirm(`Nonaktifkan produk "${p.name}"?\nRiwayat transaksi tetap tersimpan.`);
    if (!ok) return;

    try {
        const result = await apiRequest(`/api/produk/${productId}`, { method: "DELETE" });
        showToast(result.message || "Produk dinonaktifkan.");
        await loadInventory();
    } catch (error) {
        console.error("Gagal menghapus produk:", error);
        showToast(error.message, "danger");
    }
}

/* ============================================================
RESTOCK
============================================================ */
function openRestockModal(productId) {
    const p = findProduct(productId);
    if (!p) {
        showToast("Produk tidak ditemukan.", "danger");
        return;
    }

    restockTotalTouched = false;
    document.getElementById("restockForm").reset();
    document.getElementById("restockProductId").value = p.id;
    document.getElementById("restockProductName").textContent = p.name;
    document.getElementById("restockTotal").value = 0;
    getModal("restockModal").show();
}

async function submitRestock() {
    const id = document.getElementById("restockProductId").value;
    const submitBtn = document.getElementById("restockSubmit");
    submitBtn.disabled = true;

    try {
        const result = await apiRequest(`/api/inventory/${id}/restock`, {
            method: "POST",
            body: JSON.stringify({
                quantity: parseFloat(document.getElementById("restockQuantity").value),
                total_harga: parseFloat(document.getElementById("restockTotal").value) || 0,
                catatan: document.getElementById("restockNote").value.trim() || null
            })
        });

        getModal("restockModal").hide();
        showToast(result.message || "Stok berhasil ditambahkan.");
        await loadInventory();
    } catch (error) {
        console.error("Gagal restock:", error);
        showToast(error.message, "danger");
    } finally {
        submitBtn.disabled = false;
    }
}

/* ============================================================
PENYESUAIAN STOK
============================================================ */
function openAdjustModal(productId) {
    const p = findProduct(productId);
    if (!p) {
        showToast("Produk tidak ditemukan.", "danger");
        return;
    }

    document.getElementById("adjustForm").reset();
    document.getElementById("adjustHelp").textContent = "Positif menambah stok, negatif mengurangi stok.";
    document.getElementById("adjustProductId").value = p.id;
    document.getElementById("adjustProductName").textContent = p.name;
    document.getElementById("adjustCurrentStock").textContent = `${formatNumber(p.stock)} ${p.unit || "pcs"}`;
    getModal("adjustModal").show();
}

async function submitAdjust() {
    const id = document.getElementById("adjustProductId").value;
    const type = document.getElementById("adjustType").value;
    const submitBtn = document.getElementById("adjustSubmit");
    submitBtn.disabled = true;

    try {
        let quantity = parseFloat(document.getElementById("adjustQuantity").value);
        if (!quantity) throw new Error("Jumlah penyesuaian tidak boleh 0.");
        if (type === "waste") quantity = -Math.abs(quantity);

        const result = await apiRequest(`/api/inventory/${id}/adjust`, {
            method: "POST",
            body: JSON.stringify({
                quantity: quantity,
                movement_type: type,
                reason: document.getElementById("adjustReason").value.trim()
            })
        });

        getModal("adjustModal").hide();
        showToast(result.message || "Stok berhasil disesuaikan.");
        await loadInventory();
    } catch (error) {
        console.error("Gagal menyesuaikan stok:", error);
        showToast(error.message, "danger");
    } finally {
        submitBtn.disabled = false;
    }
}

/* ============================================================
RIWAYAT STOK
============================================================ */
async function openHistoryModal(productId) {
    const p = findProduct(productId);
    if (!p) {
        showToast("Produk tidak ditemukan.", "danger");
        return;
    }

    const tbody = document.getElementById("historyTable");
    document.getElementById("historyProductName").textContent = p.name;
    tbody.innerHTML = `
        <tr><td colspan="5" class="text-center py-4 text-muted">
            <i class="fa-solid fa-spinner fa-spin me-2"></i>Memuat riwayat...
        </td></tr>`;
    getModal("historyModal").show();

    try {
        const result = await apiRequest(`/api/inventory/${productId}/movements`);
        const rows = result.data || [];

        if (!rows.length) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">Belum ada pergerakan stok.</td></tr>`;
            return;
        }

        tbody.innerHTML = rows.map(m => {
            const change = m.quantity_change;
            const changeClass = change > 0 ? "text-success" : "text-danger";
            const sign = change > 0 ? "+" : "";
            const date = new Date(m.timestamp).toLocaleString("id-ID", {
                day: "2-digit", month: "short", year: "numeric",
                hour: "2-digit", minute: "2-digit"
            });

            return `
                <tr>
                    <td class="small">${escapeHtml(date)}</td>
                    <td>${escapeHtml(MOVEMENT_LABELS[m.reason] || m.reason)}</td>
                    <td class="text-end fw-bold ${changeClass}">${sign}${formatNumber(change)}</td>
                    <td class="text-end">${formatNumber(m.stock_after)}</td>
                    <td class="small text-muted">${escapeHtml(m.notes || "-")}</td>
                </tr>`;
        }).join("");
    } catch (error) {
        console.error("Gagal memuat riwayat:", error);
        tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-danger">${escapeHtml(error.message)}</td></tr>`;
    }
}

/* ============================================================
LOADING & ERROR
============================================================ */
function showLoading() {
    const table = document.getElementById("inventoryTable");
    if (!table) return;

    table.innerHTML = `
        <tr>
            <td colspan="7" class="text-center py-4 text-muted">
                <i class="fa-solid fa-spinner fa-spin me-2"></i>Memuat data inventaris...
            </td>
        </tr>`;
}

function showError(message) {
    const table = document.getElementById("inventoryTable");
    if (!table) return;

    table.innerHTML = `
        <tr>
            <td colspan="7" class="text-center py-4 text-danger">
                <i class="fa-solid fa-circle-exclamation me-2"></i>${escapeHtml(message)}
            </td>
        </tr>`;
}