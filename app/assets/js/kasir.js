// ── Helpers ──
let products = [];
let cart = [];

const rupiah = value => new Intl.NumberFormat("id-ID", {
  style: "currency",
  currency: "IDR",
  maximumFractionDigits: 0
}).format(value);

function getTotalCart() {
  const subtotal = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
  const discount = parseFloat(document.getElementById("inputDiscount")?.value || 0);
  const tax = parseFloat(document.getElementById("inputTax")?.value || 0);
  return subtotal - discount + tax;
}

// ── 1. Fetch data dari API Kasir ──
async function loadProducts() {
  try {
    const response = await fetch(API_BASE_URL + "/api/kasir");
    const result = await response.json();
    if (result.status === "success") {
      products = result.data;
      renderProducts();
    }
  } catch (err) {
    console.error("Gagal load produk:", err);
  }
}

function renderProducts(list) {
  if (!list) list = products;
  const grid = document.getElementById("productGrid");
  if (!grid) return;

  if (!list.length) {
    grid.innerHTML = '<div class="col-12 text-center text-muted py-5">Produk tidak ditemukan.</div>';
    return;
  }

  var html = "";
  for (var i = 0; i < list.length; i++) {
    var p = list[i];
    html += '<div class="col-6 col-sm-4 col-lg-3">';
    html += '<button class="product-card w-100 text-start p-3" onclick="addToCart(' + p.id + ')">';
    html += '<div class="product-icon mb-3"><i class="fas fa-box"></i></div>';
    html += '<div class="fw-bold text-dark">' + p.name + '</div>';
    html += '<div class="text-primary fw-semibold mt-1">' + rupiah(p.price) + '</div>';
    html += '</button>';
    html += '</div>';
  }
  grid.innerHTML = html;
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
  const cartList = document.getElementById("cartItems");
  const cartTotal = document.getElementById("total");
  const btnCheckout = document.getElementById("checkoutBtn");
  const subtotalEl = document.getElementById("subtotal");
  const cartCountEl = document.getElementById("cartCount");

  if (!cartList) return;

  var totalQty = cart.reduce(function(sum, item) { return sum + item.qty; }, 0);
  if (cartCountEl) cartCountEl.textContent = totalQty;

  if (!cart.length) {
    cartList.innerHTML = '<div class="text-center text-muted py-5"><i class="fa-solid fa-cart-shopping fa-2x mb-3"></i><p class="mb-0">Keranjang masih kosong</p></div>';
    if (cartTotal) cartTotal.textContent = "Rp0";
    if (subtotalEl) subtotalEl.textContent = "Rp0";
    if (btnCheckout) btnCheckout.disabled = true;
    return;
  }

  var html = "";
  for (var i = 0; i < cart.length; i++) {
    var item = cart[i];
    html += '<div class="d-flex justify-content-between align-items-center mb-3">';
    html += '<div>';
    html += '<div class="fw-bold">' + item.name + '</div>';
    html += '<div class="text-primary">' + rupiah(item.price) + '</div>';
    html += '</div>';
    html += '<div class="d-flex align-items-center gap-2">';
    html += '<button class="btn btn-sm btn-outline-secondary" onclick="changeQty(' + item.id + ', -1)">-</button>';
    html += '<span class="fw-bold" style="width:20px;text-align:center;">' + item.qty + '</span>';
    html += '<button class="btn btn-sm btn-outline-secondary" onclick="changeQty(' + item.id + ', 1)">+</button>';
    html += '</div>';
    html += '</div>';
  }
  cartList.innerHTML = html;

  var subtotal = cart.reduce(function(sum, item) { return sum + (item.price * item.qty); }, 0);
  var total = getTotalCart();

  if (subtotalEl) subtotalEl.textContent = rupiah(subtotal);
  if (cartTotal) cartTotal.textContent = rupiah(total);
  if (btnCheckout) btnCheckout.disabled = false;
}

// ── 2. Checkout via Modal ──
function openPaymentModal() {
  if (!cart.length) {
    Swal.fire("Oops", "Keranjang belanja masih kosong!", "warning");
    return;
  }
  var total = getTotalCart();
  document.getElementById("payTotalAmount").innerText = rupiah(total);
  document.getElementById("payMethod").value = "Cash";
  document.getElementById("payReceived").value = "";
  document.getElementById("payChange").innerText = "Rp 0";
  document.getElementById("payCustomerName").value = "";
  document.getElementById("payNotes").value = "";
  togglePaymentFields();

  var modal = new bootstrap.Modal(document.getElementById("modalPayment"));
  modal.show();
}

function togglePaymentFields() {
  var method = document.getElementById("payMethod").value;
  var cashBlock = document.getElementById("payCashBlock");
  var custBlock = document.getElementById("payCustomerBlock");

  if (method === "Cash") {
    cashBlock.classList.remove("d-none");
    custBlock.classList.add("d-none");
  } else if (method === "Kasbon") {
    cashBlock.classList.add("d-none");
    custBlock.classList.remove("d-none");
  } else {
    cashBlock.classList.add("d-none");
    custBlock.classList.add("d-none");
  }
}

function setCash(val) {
  var total = getTotalCart();
  var input = document.getElementById("payReceived");
  if (val === "pas") {
    input.value = total;
  } else {
    input.value = val;
  }
  calculateChange();
}

function calculateChange() {
  var total = getTotalCart();
  var received = parseInt(document.getElementById("payReceived").value) || 0;
  var change = received - total;
  var changeEl = document.getElementById("payChange");
  if (change < 0) {
    changeEl.innerText = "Kurang " + rupiah(Math.abs(change));
    changeEl.className = "fw-bold text-danger fs-5";
  } else {
    changeEl.innerText = rupiah(change);
    changeEl.className = "fw-bold text-success fs-5";
  }
}

async function submitPayment() {
  var method = document.getElementById("payMethod").value;
  var notes = document.getElementById("payNotes").value || "Transaksi Kasir Web";
  var customerName = null;
  var total = getTotalCart();

  if (method === "Kasbon") {
    customerName = document.getElementById("payCustomerName").value.trim();
    if (!customerName) {
      Swal.fire("Oops", "Nama pelanggan wajib diisi untuk Kasbon!", "warning");
      return;
    }
  } else if (method === "Cash") {
    var received = parseInt(document.getElementById("payReceived").value) || 0;
    if (received < total) {
      Swal.fire("Oops", "Uang diterima kurang dari total tagihan!", "warning");
      return;
    }
  }

  var payload = {
    items: cart.map(function(item) { return { product_id: item.id, quantity: item.qty }; }),
    payment_method: method,
    customer_name: customerName,
    notes: notes
  };

  try {
    Swal.fire({ title: "Memproses...", allowOutsideClick: false, didOpen: function() { Swal.showLoading(); } });

    var response = await fetch(API_BASE_URL + "/api/kasir/transaksi", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    var result = await response.json();

    if (response.ok && result.status === "success") {
      bootstrap.Modal.getInstance(document.getElementById("modalPayment")).hide();
      Swal.fire({
        icon: "success",
        title: "Transaksi Berhasil!",
        text: "Data telah disimpan ke buku besar.",
        confirmButtonText: "Transaksi Baru"
      }).then(function() {
        newTransaction();
      });
    } else {
      Swal.fire("Gagal", result.detail || "Error Server", "error");
    }
  } catch (err) {
    console.error(err);
    Swal.fire("Error", "Terjadi kesalahan jaringan.", "error");
  }
}

// ── 3. Reset ──
function newTransaction() {
  cart = [];
  var searchEl = document.getElementById("productSearch");
  if (searchEl) searchEl.value = "";
  if (document.getElementById("inputDiscount")) document.getElementById("inputDiscount").value = "";
  if (document.getElementById("inputTax")) document.getElementById("inputTax").value = "";
  var btn = document.getElementById("checkoutBtn");
  if (btn) btn.innerHTML = '<i class="fa-solid fa-check me-2"></i> Checkout';

  loadProducts();
  renderCart();
}

// ── Init ──
document.addEventListener("DOMContentLoaded", function() {
  loadProducts();

  var searchInput = document.getElementById("productSearch");
  if (searchInput) {
    searchInput.addEventListener("input", function(e) {
      var keyword = e.target.value.toLowerCase();
      renderProducts(products.filter(function(item) {
        return item.name.toLowerCase().includes(keyword);
      }));
    });
  }

  ["inputDiscount", "inputTax"].forEach(function(id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener("input", renderCart);
  });
});
