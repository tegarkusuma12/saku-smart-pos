const products = [
  { id: 1, name: "Indomie Goreng", price: 3500, icon: "fa-bowl-food" },
  { id: 2, name: "Aqua 600ml", price: 3500, icon: "fa-bottle-water" },
  { id: 3, name: "Teh Botol", price: 4000, icon: "fa-mug-hot" },
  { id: 4, name: "Kopi Sachet", price: 2500, icon: "fa-mug-saucer" },
  { id: 5, name: "Roti Cokelat", price: 7000, icon: "fa-bread-slice" },
  { id: 6, name: "Telur 1 Butir", price: 3000, icon: "fa-egg" },
  { id: 7, name: "Sabun Mandi", price: 6500, icon: "fa-pump-soap" },
  { id: 8, name: "Minyak 1 Liter", price: 18000, icon: "fa-oil-can" }
];

let cart = [];

const rupiah = value => new Intl.NumberFormat("id-ID", {
  style: "currency",
  currency: "IDR",
  maximumFractionDigits: 0
}).format(value);

function renderProducts(list = products) {
  const grid = document.getElementById("productGrid");
  if (!grid) return;

  grid.innerHTML = list.length ? list.map(product => `
    <div class="col-6 col-sm-4 col-lg-3">
      <button class="product-card w-100 text-start p-3" onclick="addToCart(${product.id})">
        <div class="product-icon mb-3"><i class="fas ${product.icon}"></i></div>
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
  if (item.qty <= 0) cart = cart.filter(product => product.id !== id);
  renderCart();
}

function getTotals() {
  const subtotal = cart.reduce((sum, item) => sum + item.price * item.qty, 0);
  const discountRate = Number(document.getElementById("inputDiscount")?.value || 0);
  const taxRate = Number(document.getElementById("inputTax")?.value || 0);
  const discount = subtotal * discountRate / 100;
  const taxable = subtotal - discount;
  const tax = taxable * taxRate / 100;
  return { subtotal, discount, tax, total: taxable + tax };
}

function renderCart() {
  const container = document.getElementById("cartItems");
  if (!container) return;

  container.innerHTML = cart.length ? cart.map(item => `
    <div class="cart-item mb-2">
      <div class="d-flex justify-content-between gap-2">
        <div>
          <div class="fw-semibold">${item.name}</div>
          <small class="text-muted">${rupiah(item.price)} / item</small>
        </div>
        <div class="text-end fw-bold">${rupiah(item.price * item.qty)}</div>
      </div>
      <div class="d-flex justify-content-between align-items-center mt-2">
        <div class="qty-control">
          <button onclick="changeQty(${item.id}, -1)">−</button>
          <span>${item.qty}</span>
          <button onclick="changeQty(${item.id}, 1)">+</button>
        </div>
        <button class="btn btn-sm btn-link text-danger p-0" onclick="changeQty(${item.id}, -${item.qty})">
          Hapus
        </button>
      </div>
    </div>
  `).join("") : '<div class="text-center text-muted py-5"><i class="fas fa-cart-shopping fa-2x mb-2 d-block"></i>Keranjang masih kosong.</div>';

  const totals = getTotals();
  document.getElementById("valSubtotal").textContent = rupiah(totals.subtotal);
  document.getElementById("valDiscount").textContent = "-" + rupiah(totals.discount);
  document.getElementById("valTax").textContent = rupiah(totals.tax);
  document.getElementById("valTotal").textContent = rupiah(totals.total);
}

function checkout() {
  if (!cart.length) {
    alert("Keranjang masih kosong.");
    return;
  }
  document.getElementById("actionCheckout")?.classList.add("d-none");
  document.getElementById("actionSuccess")?.classList.remove("d-none");
  document.getElementById("actionSuccess")?.classList.add("d-flex");
}

function newTransaction() {
  cart = [];
  document.getElementById("actionCheckout")?.classList.remove("d-none");
  document.getElementById("actionSuccess")?.classList.add("d-none");
  document.getElementById("actionSuccess")?.classList.remove("d-flex");
  renderCart();
}

document.addEventListener("DOMContentLoaded", () => {
  renderProducts();
  renderCart();

  document.getElementById("searchInput")?.addEventListener("input", e => {
    const keyword = e.target.value.toLowerCase();
    renderProducts(products.filter(item => item.name.toLowerCase().includes(keyword)));
  });

  ["inputDiscount", "inputTax"].forEach(id => {
    document.getElementById(id)?.addEventListener("input", renderCart);
  });

  document.getElementById("btnPay")?.addEventListener("click", checkout);
  document.getElementById("btnNew")?.addEventListener("click", newTransaction);
});