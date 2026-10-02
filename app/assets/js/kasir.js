let products = [];
let cart = [];

const rupiah = value => new Intl.NumberFormat("id-ID", {
  style: "currency",
  currency: "IDR",
  maximumFractionDigits: 0
}).format(value);

// 1. Fetch data dari API Kasir
async function loadProducts() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/kasir`);
    const result = await response.json();
    if (result.status === "success") {
      products = result.data;
      renderProducts();
    }
  } catch (err) {
    console.error("Gagal load produk:", err);
  }
}

function renderProducts(list = products) {
  const grid = document.getElementById("productGrid");
  if (!grid) return;

  grid.innerHTML = list.length ? list.map(product => `
    <div class="col-6 col-sm-4 col-lg-3">
      <button class="product-card w-100 text-start p-3" onclick="addToCart(${product.id})">
        <div class="product-icon mb-3"><i class="fas fa-box"></i></div>
        <div class="fw-bold text-dark">${product.name}</div>
        <div class="text-primary fw-semibold mt-1">${rupiah(product.price)}</div>
      </button>
    </div>
  `).join("") : '<div class="col-12 text-center text-muted py-5">Produk tidak ditemukan.</div>';
}

function addToCart(id) {
  const product = products.find(item => item.id === id);
  if (!product) return;

  const existing = cart.find(item => item.id === id);
  if (existing) existing.qty += 1;
  else cart.push({ ...product, qty: 1 });

  renderCart();
}

function changeQty(id, delta) {
  const item = cart.find(product => product.id === id);
  if (!item) return;

  item.qty += delta;
  if (item.qty <= 0) cart = cart.filter(p => p.id !== id);

  renderCart();
}

function renderCart() {
  const cartList = document.getElementById("cartList");
  const cartTotal = document.getElementById("cartTotal");
  const btnCheckout = document.getElementById("btnCheckout");
  if (!cartList) return;

  if (!cart.length) {
    cartList.innerHTML = '<div class="text-center text-muted py-5">Keranjang kosong.</div>';
    cartTotal.textContent = "Rp0";
    if (btnCheckout) btnCheckout.disabled = true;
    return;
  }

  cartList.innerHTML = cart.map(item => `
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div>
        <div class="fw-bold">${item.name}</div>
        <div class="text-primary">${rupiah(item.price)}</div>
      </div>
      <div class="d-flex align-items-center gap-2">
        <button class="btn btn-sm btn-outline-secondary" onclick="changeQty(${item.id}, -1)">-</button>
        <span class="fw-bold" style="width:20px;text-align:center;">${item.qty}</span>
        <button class="btn btn-sm btn-outline-secondary" onclick="changeQty(${item.id}, 1)">+</button>
      </div>
    </div>
  `).join("");

  const subtotal = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
  const discount = parseFloat(document.getElementById("inputDiscount")?.value || 0);
  const tax = parseFloat(document.getElementById("inputTax")?.value || 0);
  const total = subtotal - discount + tax;

  cartTotal.textContent = rupiah(total);
  if (btnCheckout) btnCheckout.disabled = false;
}

// 2. Checkout via POST API
async function checkout() {
  if (!cart.length) {
    alert("Keranjang masih kosong.");
    return;
  }
  
  // Format payload sesuai request schema FastAPI backend
  const payload = {
      items: cart.map(item => ({ product_id: item.id, quantity: item.qty })),
      payment_method: "Cash",
      customer_name: null,
      notes: "Transaksi dari Kasir Web"
  };

  try {
      const btn = document.getElementById("btnCheckout");
      if (btn) { btn.disabled = true; btn.textContent = "Memproses..."; }
      
      const response = await fetch(`${API_BASE_URL}/api/kasir/transaksi`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
      });
      const result = await response.json();
      
      if (response.ok && result.status === "success") {
          document.getElementById("actionCheckout")?.classList.add("d-none");
          document.getElementById("actionSuccess")?.classList.remove("d-none");
          document.getElementById("actionSuccess")?.classList.add("d-flex");
      } else {
          alert("Gagal memproses transaksi: " + (result.detail || "Error Server"));
          if (btn) { btn.disabled = false; btn.innerHTML = "Proses Bayar"; }
      }
  } catch (err) {
      console.error(err);
      alert("Terjadi kesalahan jaringan.");
  }
}

function newTransaction() {
  cart = [];
  document.getElementById("actionCheckout")?.classList.remove("d-none");
  document.getElementById("actionSuccess")?.classList.add("d-none");
  document.getElementById("actionSuccess")?.classList.remove("d-flex");
  // Reset UI & refresh produk biar stok up-to-date
  document.getElementById("searchInput").value = "";
  if(document.getElementById("inputDiscount")) document.getElementById("inputDiscount").value = "";
  if(document.getElementById("inputTax")) document.getElementById("inputTax").value = "";
  const btn = document.getElementById("btnCheckout");
  if(btn) btn.innerHTML = "Proses Bayar";
  
  loadProducts();
  renderCart();
}

document.addEventListener("DOMContentLoaded", () => {
  loadProducts(); // Panggil data dari API saat halaman dimuat

  document.getElementById("searchInput")?.addEventListener("input", e => {
    const keyword = e.target.value.toLowerCase();
    renderProducts(products.filter(item => item.name.toLowerCase().includes(keyword)));
  });

  ["inputDiscount", "inputTax"].forEach(id => {
    document.getElementById(id)?.addEventListener("input", renderCart);
  });
});