/* =========================================================
   Fouad Farm — frontend app
   Vanilla JS, no build step (served as static files behind
   nginx, which proxies /inventory, /orders, /reports to the
   FastAPI backend on the same origin).
   ========================================================= */

const STRINGS = {
  en: {
    brand: "Fouad Farm",
    nav_dashboard: "Dashboard",
    nav_inventory: "Products & Batches",
    nav_pos: "New Order",
    nav_orders: "Orders",
    nav_reports: "Reports",
    sidebar_note: "Nursery inventory & point of sale",
    stat_products: "Active products",
    stat_stock: "Units in stock",
    stat_orders_today: "Orders today",
    stat_revenue_today: "Revenue today",
    add_product: "Add product",
    add_batch: "Add batch",
    trash_fifo: "Trash stock (FIFO)",
    col_product: "Product",
    col_price: "Unit price",
    col_stock: "In stock",
    col_actions: "",
    no_products: "No products yet",
    no_products_sub: "Add your first product to start tracking batches.",
    no_batches: "No batches logged for this product yet.",
    batch_location: "Quarter / Foot / Line",
    batch_entered: "Entered",
    batch_remaining: "remaining",
    edit: "Edit",
    delete: "Delete",
    save: "Save",
    cancel: "Cancel",
    close: "Close",
    confirm_delete_product: "Delete this product? This can't be undone from here.",
    confirm_delete_batch: "Remove this batch lot?",
    product_name: "Product name",
    unit_price: "Unit price",
    date_entered: "Date entered",
    quantity: "Quantity",
    quarter: "Quarter",
    foot: "Foot",
    line: "Line",
    total_to_trash: "Units to trash",
    pos_pick_products: "Tap a product to add it to the order",
    pos_out_of_stock: "Out of stock",
    ticket_title: "Current order",
    ticket_empty: "No items yet — pick a product to start the order.",
    customer_name: "Customer name",
    payment_method: "Payment method",
    payment_amount: "Amount paid now",
    price_override: "Override total (optional)",
    place_order: "Place order",
    order_placed: "Order placed",
    total: "Total",
    orders_filter_all: "All orders",
    order_items_count: "items",
    cancel_order: "Cancel order",
    order_cancelled: "Order cancelled",
    confirm_cancel_order: "Cancel this order and return stock to inventory?",
    reports_batches: "Batches",
    reports_customers: "Customers",
    reports_ranking: "Top products",
    reports_search: "Search orders",
    search_customer_placeholder: "Search by customer name…",
    units_sold: "units sold",
    revenue: "revenue",
    items_bought: "items bought",
    no_data: "No data for this period yet.",
    loading: "Loading…",
    error_generic: "Something went wrong. Please try again.",
    required_field: "This field is required.",
    none: "Regular",
    deposit: "Deposit",
    stat_paid_total: "Collected (all time)",
    stat_unpaid_orders: "Unpaid orders",
    recent_orders: "Recent orders",
    top_customers: "Top customers",
    no_orders_yet: "No orders yet.",
    order_paid: "Paid",
    order_remaining: "Remaining",
    status_paid: "Paid",
    status_partial: "Partial",
    status_unpaid: "Unpaid",
    customer_spent: "Total spent",
    customer_paid: "Total paid",
    customer_order_count: "Orders",
    view_history: "View order history",
    order_history_for: "Order history —",
    search_product_placeholder: "Filter by product name…",
    search_payment_method: "Payment method",
    search_payment_status: "Payment status",
    filter_all: "All",
    filter_paid: "Fully paid",
    filter_unpaid: "Not fully paid",
    date_from: "From",
    date_to: "To",
    edit_order: "Edit",
    pay_order: "Pay",
    order_header: "Order details",
    current_items: "Items",
    remove: "Remove",
    add_item: "Add item",
    add: "Add",
    select_product: "Select a product…",
    payment_recorded: "Payment recorded",
    order_updated: "Order updated",
    amount_due: "Amount due",
    fully_paid_already: "This order is already fully paid.",
  },
  ar: {
    brand: "مزرعة فؤاد",
    nav_dashboard: "لوحة التحكم",
    nav_inventory: "المنتجات والدفعات",
    nav_pos: "طلب جديد",
    nav_orders: "الطلبات",
    nav_reports: "التقارير",
    sidebar_note: "إدارة مخزون المشتل ونقطة البيع",
    stat_products: "المنتجات النشطة",
    stat_stock: "الوحدات المتوفرة",
    stat_orders_today: "طلبات اليوم",
    stat_revenue_today: "إيرادات اليوم",
    add_product: "إضافة منتج",
    add_batch: "إضافة دفعة",
    trash_fifo: "إتلاف مخزون (FIFO)",
    col_product: "المنتج",
    col_price: "سعر الوحدة",
    col_stock: "المتوفر",
    col_actions: "",
    no_products: "لا توجد منتجات بعد",
    no_products_sub: "أضف أول منتج لبدء تتبع الدفعات.",
    no_batches: "لا توجد دفعات مسجلة لهذا المنتج بعد.",
    batch_location: "القطعة / القدم / الخط",
    batch_entered: "تاريخ الإدخال",
    batch_remaining: "متبقٍ",
    edit: "تعديل",
    delete: "حذف",
    save: "حفظ",
    cancel: "إلغاء",
    close: "إغلاق",
    confirm_delete_product: "حذف هذا المنتج؟ لا يمكن التراجع عن هذا من هنا.",
    confirm_delete_batch: "إزالة هذه الدفعة؟",
    product_name: "اسم المنتج",
    unit_price: "سعر الوحدة",
    date_entered: "تاريخ الإدخال",
    quantity: "الكمية",
    quarter: "القطعة",
    foot: "القدم",
    line: "الخط",
    total_to_trash: "عدد الوحدات المراد إتلافها",
    pos_pick_products: "اضغط على منتج لإضافته إلى الطلب",
    pos_out_of_stock: "نفدت الكمية",
    ticket_title: "الطلب الحالي",
    ticket_empty: "لا توجد عناصر بعد — اختر منتجًا لبدء الطلب.",
    customer_name: "اسم الزبون",
    payment_method: "طريقة الدفع",
    payment_amount: "المبلغ المدفوع الآن",
    price_override: "تجاوز الإجمالي (اختياري)",
    place_order: "تنفيذ الطلب",
    order_placed: "تم تنفيذ الطلب",
    total: "الإجمالي",
    orders_filter_all: "كل الطلبات",
    order_items_count: "عناصر",
    cancel_order: "إلغاء الطلب",
    order_cancelled: "تم إلغاء الطلب",
    confirm_cancel_order: "إلغاء هذا الطلب وإعادة المخزون؟",
    reports_batches: "الدفعات",
    reports_customers: "الزبائن",
    reports_ranking: "الأكثر مبيعًا",
    reports_search: "بحث في الطلبات",
    search_customer_placeholder: "ابحث باسم الزبون…",
    units_sold: "وحدة مباعة",
    revenue: "الإيرادات",
    items_bought: "عناصر مشتراة",
    no_data: "لا توجد بيانات لهذه الفترة بعد.",
    loading: "جارٍ التحميل…",
    error_generic: "حدث خطأ ما. يرجى المحاولة مرة أخرى.",
    required_field: "هذا الحقل مطلوب.",
    none: "عادي",
    deposit: "عربون",
    stat_paid_total: "المُحصَّل (كل الفترات)",
    stat_unpaid_orders: "طلبات غير مدفوعة",
    recent_orders: "أحدث الطلبات",
    top_customers: "أفضل الزبائن",
    no_orders_yet: "لا توجد طلبات بعد.",
    order_paid: "المدفوع",
    order_remaining: "المتبقي",
    status_paid: "مدفوع",
    status_partial: "جزئي",
    status_unpaid: "غير مدفوع",
    customer_spent: "إجمالي الشراء",
    customer_paid: "إجمالي المدفوع",
    customer_order_count: "الطلبات",
    view_history: "عرض سجل الطلبات",
    order_history_for: "سجل الطلبات —",
    search_product_placeholder: "تصفية باسم المنتج…",
    search_payment_method: "طريقة الدفع",
    search_payment_status: "حالة الدفع",
    filter_all: "الكل",
    filter_paid: "مدفوع بالكامل",
    filter_unpaid: "غير مدفوع بالكامل",
    date_from: "من",
    date_to: "إلى",
    edit_order: "تعديل",
    pay_order: "دفع",
    order_header: "تفاصيل الطلب",
    current_items: "العناصر",
    remove: "إزالة",
    add_item: "إضافة عنصر",
    add: "إضافة",
    select_product: "اختر منتجًا…",
    payment_recorded: "تم تسجيل الدفعة",
    order_updated: "تم تحديث الطلب",
    amount_due: "المبلغ المستحق",
    fully_paid_already: "هذا الطلب مدفوع بالكامل بالفعل.",
  }
};

const state = {
  lang: localStorage.getItem("fouad_lang") || "en",
  view: "dashboard",
  products: [],
  openProductId: null,
  batchesByProduct: {},
  cart: {},          // product_id -> { product, qty }
  orders: [],
  ordersLoaded: false,
  reportsTab: "batches",
};

function t(key){ return STRINGS[state.lang][key] || STRINGS.en[key] || key; }
function money(v){ return Number(v ?? 0).toFixed(2); }

/**
 * Quarter/Foot/Line is a right-to-left-read location code: "Quarter" should
 * be the first value encountered when reading right-to-left (matching where
 * its label sits in the Arabic header). Plain digit/slash text always
 * renders in literal left-to-right order regardless of page direction, so
 * for Arabic we build the string in reverse field order instead of relying
 * on CSS/bidi tricks.
 */
function formatLocation(b){
  const q = escapeHTML(b.quarter), f = escapeHTML(b.foot), l = escapeHTML(b.line);
  return state.lang === "ar" ? `${l}/${f}/${q}` : `${q}/${f}/${l}`;
}

/* ---------------- API client ---------------- */

async function api(method, path, body){
  let res;
  try{
    res = await fetch(path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (err){
    toast(t("error_generic"), true);
    throw err;
  }
  let data = null;
  try{ data = await res.json(); } catch(_e){ /* no body */ }
  if (!res.ok){
    const message = (data && data.detail) ? data.detail : t("error_generic");
    toast(message, true);
    throw new Error(message);
  }
  return data;
}

const apiGet = (path) => api("GET", path);
const apiPost = (path, body) => api("POST", path, body);
const apiPatch = (path, body) => api("PATCH", path, body);
const apiDelete = (path) => api("DELETE", path);

/* ---------------- toast ---------------- */

function toast(message, isError){
  const stack = document.getElementById("toast-stack");
  const el = document.createElement("div");
  el.className = "toast" + (isError ? " is-error" : "");
  el.textContent = message;
  stack.appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

/* ---------------- modal ---------------- */

function openModal(html){
  document.getElementById("modal-box").innerHTML = html;
  document.getElementById("modal-backdrop").classList.add("is-open");
}
function closeModal(){
  document.getElementById("modal-backdrop").classList.remove("is-open");
  document.getElementById("modal-box").innerHTML = "";
}
document.getElementById("modal-backdrop").addEventListener("click", (e) => {
  if (e.target.id === "modal-backdrop") closeModal();
});

/* ---------------- shell / nav / language ---------------- */

function applyLanguage(){
  document.documentElement.lang = state.lang;
  document.documentElement.dir = state.lang === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach(el => {
    el.textContent = t(el.getAttribute("data-i18n"));
  });
  document.querySelectorAll(".lang-btn").forEach(btn => {
    btn.classList.toggle("is-active", btn.dataset.lang === state.lang);
  });
  document.getElementById("view-title").textContent = t("nav_" + state.view);
  const today = new Date();
  document.getElementById("today-date").textContent = today.toISOString().slice(0, 10);
}

document.getElementById("lang-toggle").addEventListener("click", (e) => {
  const btn = e.target.closest(".lang-btn");
  if (!btn) return;
  state.lang = btn.dataset.lang;
  localStorage.setItem("fouad_lang", state.lang);
  applyLanguage();
  renderView();
});

document.getElementById("nav").addEventListener("click", (e) => {
  const btn = e.target.closest(".nav-item");
  if (!btn) return;
  state.view = btn.dataset.view;
  document.querySelectorAll(".nav-item").forEach(b => b.classList.toggle("is-active", b === btn));
  document.getElementById("view-title").textContent = t("nav_" + state.view);
  document.getElementById("sidebar").classList.remove("is-open");
  renderView();
});

document.getElementById("menu-toggle").addEventListener("click", () => {
  document.getElementById("sidebar").classList.toggle("is-open");
});

/* ---------------- data loading ---------------- */

async function loadProducts(){
  const res = await apiGet("/inventory/products");
  state.products = (res && res.data) || [];
}

async function loadBatches(productId){
  const res = await apiGet(`/inventory/batches?product_id=${productId}`);
  state.batchesByProduct[productId] = (res && res.data) || [];
}

async function loadOrders(){
  const res = await apiGet("/orders");
  state.orders = (res && res.data) || [];
  state.ordersLoaded = true;
}

/* ---------------- view router ---------------- */

const root = () => document.getElementById("view-root");

async function renderView(){
  const r = root();
  r.innerHTML = `<div class="empty-state">${t("loading")}</div>`;
  try{
    if (state.view === "dashboard") await renderDashboard();
    else if (state.view === "inventory") await renderInventory();
    else if (state.view === "pos") await renderPOS();
    else if (state.view === "orders") await renderOrders();
    else if (state.view === "reports") await renderReports();
  } catch(err){
    r.innerHTML = `<div class="empty-state">${t("error_generic")}</div>`;
  }
}

/* ---------------- Dashboard ---------------- */

async function renderDashboard(){
  await loadProducts();
  if (!state.ordersLoaded) await loadOrders();

  const totalStock = state.products.reduce((sum, p) => sum + Number(p.quantity || 0), 0);
  const todayStr = new Date().toISOString().slice(0, 10);
  const todaysOrders = state.orders.filter(o => String(o.order_date).slice(0,10) === todayStr);
  const revenueToday = todaysOrders.reduce((sum, o) => sum + Number(o.total_amount || 0), 0);
  const paidTotal = state.orders.reduce((sum, o) => sum + Number(o.total_paid || 0), 0);
  const unpaidOrders = state.orders.filter(o => !o.is_fully_paid);

  const recent = [...state.orders].sort((a,b) => (b.order_id||0) - (a.order_id||0)).slice(0, 5);

  const customerMap = buildCustomerSummary(state.orders);
  const topCustomers = Object.values(customerMap).sort((a,b) => b.totalSpent - a.totalSpent).slice(0, 5);
  const maxSpent = Math.max(1, ...topCustomers.map(c => c.totalSpent));

  root().innerHTML = `
    <div class="stat-grid">
      <div class="stat-card"><div class="stat-label">${t("stat_products")}</div><div class="stat-value">${state.products.length}</div></div>
      <div class="stat-card"><div class="stat-label">${t("stat_stock")}</div><div class="stat-value">${totalStock}</div></div>
      <div class="stat-card"><div class="stat-label">${t("stat_orders_today")}</div><div class="stat-value accent">${todaysOrders.length}</div></div>
      <div class="stat-card"><div class="stat-label">${t("stat_revenue_today")}</div><div class="stat-value accent">${money(revenueToday)}</div></div>
      <div class="stat-card"><div class="stat-label">${t("stat_paid_total")}</div><div class="stat-value">${money(paidTotal)}</div></div>
      <div class="stat-card"><div class="stat-label">${t("stat_unpaid_orders")}</div><div class="stat-value danger">${unpaidOrders.length}</div></div>
    </div>

    <div class="section-head"><h2>${t("recent_orders")}</h2></div>
    <div id="dash-recent">${recent.length ? recent.map(orderCardHTML).join("") : `<div class="empty-state">${t("no_orders_yet")}</div>`}</div>

    <div class="section-head" style="margin-top:22px;"><h2>${t("top_customers")}</h2></div>
    <div class="card" style="margin-bottom: 26px;">
      ${topCustomers.length ? topCustomers.map(c => `
        <div class="rank-row">
          <div class="rank-name">${escapeHTML(c.customerName)}</div>
          <div class="rank-bar-track"><div class="rank-bar-fill" style="width:${(c.totalSpent/maxSpent)*100}%"></div></div>
          <div class="rank-value">${money(c.totalSpent)}</div>
        </div>
      `).join("") : `<div class="empty-state">${t("no_data")}</div>`}
    </div>

    <div class="section-head"><h2>${t("nav_inventory")}</h2></div>
    ${productsTableHTML(state.products.slice(0, 8))}
  `;

  wireOrderCards(document.getElementById("dash-recent"), () => renderDashboard());
}

function buildCustomerSummary(orders){
  const map = {};
  orders.forEach(o => {
    if (!map[o.customer_name]){
      map[o.customer_name] = { customerName: o.customer_name, totalSpent: 0, totalPaid: 0, orderCount: 0, orders: [] };
    }
    const entry = map[o.customer_name];
    entry.totalSpent += Number(o.total_amount || 0);
    entry.totalPaid += Number(o.total_paid || 0);
    entry.orderCount += 1;
    entry.orders.push(o);
  });
  return map;
}

function stockBadge(qty){
  qty = Number(qty || 0);
  if (qty <= 0) return `<span class="badge badge-out">0</span>`;
  if (qty < 20) return `<span class="badge badge-low">${qty}</span>`;
  return `<span class="badge badge-ok">${qty}</span>`;
}

function productsTableHTML(products){
  if (!products.length){
    return `<div class="empty-state"><strong>${t("no_products")}</strong>${t("no_products_sub")}</div>`;
  }
  const rows = products.map(p => `
    <tr>
      <td>${escapeHTML(p.product_name)}</td>
      <td class="num">${money(p.unit_price)}</td>
      <td>${stockBadge(p.quantity)}</td>
    </tr>
  `).join("");
  return `<div class="card"><table>
    <thead><tr><th>${t("col_product")}</th><th>${t("col_price")}</th><th>${t("col_stock")}</th></tr></thead>
    <tbody>${rows}</tbody>
  </table></div>`;
}

/* ---------------- Inventory (Products & Batches) ---------------- */

async function renderInventory(){
  await loadProducts();
  root().innerHTML = `
    <div class="section-head">
      <h2>${t("nav_inventory")}</h2>
      <div style="display:flex; gap:8px;">
        <button class="btn btn-ghost btn-sm" id="btn-trash-fifo">${t("trash_fifo")}</button>
        <button class="btn btn-primary btn-sm" id="btn-add-product">${t("add_product")}</button>
      </div>
    </div>
    <div id="product-list"></div>
  `;
  document.getElementById("btn-add-product").addEventListener("click", openAddProductModal);
  document.getElementById("btn-trash-fifo").addEventListener("click", openTrashFifoModal);
  renderProductList();
}

function renderProductList(){
  const list = document.getElementById("product-list");
  if (!state.products.length){
    list.innerHTML = `<div class="empty-state"><strong>${t("no_products")}</strong>${t("no_products_sub")}</div>`;
    return;
  }
  list.innerHTML = state.products.map(p => productRowHTML(p)).join("");

  list.querySelectorAll(".product-row-head").forEach(head => {
    head.addEventListener("click", async (e) => {
      if (e.target.closest("[data-action]")) return;
      const row = head.closest(".product-row");
      const pid = Number(row.dataset.id);
      const isOpen = row.classList.contains("is-open");
      list.querySelectorAll(".product-row.is-open").forEach(r => r.classList.remove("is-open"));
      if (!isOpen){
        row.classList.add("is-open");
        if (!state.batchesByProduct[pid]) await loadBatches(pid);
        row.querySelector(".batches-panel").innerHTML = batchesPanelHTML(pid);
        wireBatchPanel(pid, row);
      }
    });
  });

  list.querySelectorAll("[data-action='edit-product']").forEach(btn => {
    btn.addEventListener("click", (e) => { e.stopPropagation(); openEditProductModal(Number(btn.dataset.id)); });
  });
  list.querySelectorAll("[data-action='delete-product']").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm(t("confirm_delete_product"))) return;
      await apiDelete(`/inventory/products/${btn.dataset.id}`);
      await loadProducts();
      renderProductList();
    });
  });
}

function productRowHTML(p){
  return `
  <div class="product-row" data-id="${p.id}">
    <div class="product-row-head">
      <svg class="chevron" viewBox="0 0 24 24" fill="none"><path d="M9 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span class="product-name">${escapeHTML(p.product_name)}</span>
      <span class="product-price num">${money(p.unit_price)}</span>
      ${stockBadge(p.quantity)}
      <div class="field-actions">
        <button class="btn btn-ghost btn-sm" data-action="edit-product" data-id="${p.id}">${t("edit")}</button>
        <button class="btn btn-danger btn-sm" data-action="delete-product" data-id="${p.id}">${t("delete")}</button>
      </div>
    </div>
    <div class="batches-panel"></div>
  </div>`;
}

function batchesPanelHTML(productId){
  const batches = state.batchesByProduct[productId] || [];
  const head = `<div class="section-head" style="margin-bottom:8px;"><span style="font-size:0.8rem; color:var(--ink-soft); font-weight:600;">${t("batch_location")}</span>
    <button class="btn btn-accent btn-sm" data-action="add-batch" data-pid="${productId}">${t("add_batch")}</button></div>`;
  if (!batches.length) return head + `<div class="empty-state">${t("no_batches")}</div>`;

  const rows = batches.map(b => {
    const remaining = Math.max(0, Number(b.count) - Number(b.trashed));
    const pct = b.count > 0 ? Math.round((remaining / b.count) * 100) : 0;
    return `
    <div class="field-row" data-batch-id="${b.product_batch_id}">
      <div class="field-loc"><span class="loc-code">${formatLocation(b)}</span></div>
      <div class="field-bar"><div class="field-bar-fill" style="width:${pct}%"></div></div>
      <div class="field-count"><span class="num" dir="ltr">${remaining}/${b.count}</span> ${t("batch_remaining")}</div>
      <div class="field-date" dir="ltr">${b.date_entered}</div>
      <div class="field-actions">
        <button class="btn btn-ghost btn-sm" data-action="edit-batch" data-id="${b.product_batch_id}">${t("edit")}</button>
        <button class="btn btn-danger btn-sm" data-action="delete-batch" data-id="${b.product_batch_id}">${t("delete")}</button>
      </div>
    </div>`;
  }).join("");
  return head + rows;
}

function wireBatchPanel(productId, row){
  const panel = row.querySelector(".batches-panel");
  panel.querySelector("[data-action='add-batch']").addEventListener("click", (e) => {
    e.stopPropagation();
    openAddBatchModal(productId);
  });
  panel.querySelectorAll("[data-action='edit-batch']").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const batch = (state.batchesByProduct[productId] || []).find(b => b.product_batch_id === Number(btn.dataset.id));
      openEditBatchModal(productId, batch);
    });
  });
  panel.querySelectorAll("[data-action='delete-batch']").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm(t("confirm_delete_batch"))) return;
      await apiDelete(`/inventory/batches/${btn.dataset.id}`);
      await loadBatches(productId);
      await loadProducts();
      panel.innerHTML = batchesPanelHTML(productId);
      wireBatchPanel(productId, row);
      renderProductList();
    });
  });
}

function openAddProductModal(){
  openModal(`
    <h3>${t("add_product")}</h3>
    <div class="field"><label>${t("product_name")}</label><input id="f-name" /></div>
    <div class="field"><label>${t("unit_price")}</label><input id="f-price" type="number" step="0.01" min="0" /></div>
    <div class="modal-actions">
      <button class="btn btn-ghost" id="m-cancel">${t("cancel")}</button>
      <button class="btn btn-primary" id="m-save">${t("save")}</button>
    </div>
  `);
  document.getElementById("m-cancel").addEventListener("click", closeModal);
  document.getElementById("m-save").addEventListener("click", async () => {
    const name = document.getElementById("f-name").value.trim();
    const price = document.getElementById("f-price").value;
    if (!name || !price){ toast(t("required_field"), true); return; }
    await apiPost("/inventory/products", { product_name: name, unit_price: Number(price) });
    closeModal();
    await loadProducts();
    renderProductList();
  });
}

function openEditProductModal(id){
  const p = state.products.find(x => x.id === id);
  if (!p) return;
  openModal(`
    <h3>${t("edit")} — ${escapeHTML(p.product_name)}</h3>
    <div class="field"><label>${t("product_name")}</label><input id="f-name" value="${escapeHTML(p.product_name)}" /></div>
    <div class="field"><label>${t("unit_price")}</label><input id="f-price" type="number" step="0.01" min="0" value="${p.unit_price}" /></div>
    <div class="modal-actions">
      <button class="btn btn-ghost" id="m-cancel">${t("cancel")}</button>
      <button class="btn btn-primary" id="m-save">${t("save")}</button>
    </div>
  `);
  document.getElementById("m-cancel").addEventListener("click", closeModal);
  document.getElementById("m-save").addEventListener("click", async () => {
    const name = document.getElementById("f-name").value.trim();
    const price = document.getElementById("f-price").value;
    await apiPatch(`/inventory/products/${id}`, { product_name: name, unit_price: Number(price) });
    closeModal();
    await loadProducts();
    renderProductList();
  });
}

function openAddBatchModal(productId){
  openModal(`
    <h3>${t("add_batch")}</h3>
    <div class="field"><label>${t("date_entered")}</label><input id="f-date" type="date" value="${new Date().toISOString().slice(0,10)}" /></div>
    <div class="field"><label>${t("quantity")}</label><input id="f-count" type="number" min="1" /></div>
    <div class="field-row">
      <div class="field"><label>${t("quarter")}</label><input id="f-quarter" /></div>
      <div class="field"><label>${t("foot")}</label><input id="f-foot" /></div>
      <div class="field"><label>${t("line")}</label><input id="f-line" /></div>
    </div>
    <div class="modal-actions">
      <button class="btn btn-ghost" id="m-cancel">${t("cancel")}</button>
      <button class="btn btn-primary" id="m-save">${t("save")}</button>
    </div>
  `);
  document.getElementById("m-cancel").addEventListener("click", closeModal);
  document.getElementById("m-save").addEventListener("click", async () => {
    const payload = {
      product_id: productId,
      date_entered: document.getElementById("f-date").value,
      count: Number(document.getElementById("f-count").value),
      quarter: document.getElementById("f-quarter").value.trim(),
      foot: document.getElementById("f-foot").value.trim(),
      line: document.getElementById("f-line").value.trim(),
    };
    if (!payload.count || !payload.quarter || !payload.foot || !payload.line){ toast(t("required_field"), true); return; }
    await apiPost("/inventory/batches", payload);
    closeModal();
    await loadBatches(productId);
    await loadProducts();
    renderProductList();
    const row = document.querySelector(`.product-row[data-id="${productId}"]`);
    if (row){ row.classList.add("is-open"); row.querySelector(".batches-panel").innerHTML = batchesPanelHTML(productId); wireBatchPanel(productId, row); }
  });
}

function openEditBatchModal(productId, batch){
  openModal(`
    <h3>${t("edit")}</h3>
    <div class="field"><label>${t("quantity")}</label><input id="f-count" type="number" min="0" value="${batch.count}" /></div>
    <div class="field-row">
      <div class="field"><label>${t("quarter")}</label><input id="f-quarter" value="${escapeHTML(batch.quarter)}" /></div>
      <div class="field"><label>${t("foot")}</label><input id="f-foot" value="${escapeHTML(batch.foot)}" /></div>
      <div class="field"><label>${t("line")}</label><input id="f-line" value="${escapeHTML(batch.line)}" /></div>
    </div>
    <div class="modal-actions">
      <button class="btn btn-ghost" id="m-cancel">${t("cancel")}</button>
      <button class="btn btn-primary" id="m-save">${t("save")}</button>
    </div>
  `);
  document.getElementById("m-cancel").addEventListener("click", closeModal);
  document.getElementById("m-save").addEventListener("click", async () => {
    await apiPatch(`/inventory/batches/${batch.product_batch_id}`, {
      count: Number(document.getElementById("f-count").value),
      quarter: document.getElementById("f-quarter").value.trim(),
      foot: document.getElementById("f-foot").value.trim(),
      line: document.getElementById("f-line").value.trim(),
    });
    closeModal();
    await loadBatches(productId);
    await loadProducts();
    renderProductList();
    const row = document.querySelector(`.product-row[data-id="${productId}"]`);
    if (row){ row.classList.add("is-open"); row.querySelector(".batches-panel").innerHTML = batchesPanelHTML(productId); wireBatchPanel(productId, row); }
  });
}

function openTrashFifoModal(){
  const options = state.products.map(p => `<option value="${p.id}">${escapeHTML(p.product_name)}</option>`).join("");
  openModal(`
    <h3>${t("trash_fifo")}</h3>
    <div class="field"><label>${t("col_product")}</label><select id="f-product">${options}</select></div>
    <div class="field"><label>${t("total_to_trash")}</label><input id="f-total" type="number" min="1" /></div>
    <div class="modal-actions">
      <button class="btn btn-ghost" id="m-cancel">${t("cancel")}</button>
      <button class="btn btn-danger" id="m-save">${t("trash_fifo")}</button>
    </div>
  `);
  document.getElementById("m-cancel").addEventListener("click", closeModal);
  document.getElementById("m-save").addEventListener("click", async () => {
    const productId = Number(document.getElementById("f-product").value);
    const total = Number(document.getElementById("f-total").value);
    if (!total){ toast(t("required_field"), true); return; }
    await apiPost("/inventory/trash-fifo", { product_id: productId, total_to_trash: total });
    closeModal();
    await loadProducts();
    delete state.batchesByProduct[productId];
    renderProductList();
  });
}

/* ---------------- POS / New order ---------------- */

async function renderPOS(){
  await loadProducts();
  root().innerHTML = `
    <div class="pos-layout">
      <div>
        <div class="section-head"><h2>${t("nav_pos")}</h2></div>
        <p style="color:var(--ink-soft); font-size:0.85rem; margin-top:-8px;">${t("pos_pick_products")}</p>
        <div class="product-grid" id="pos-grid"></div>
      </div>
      <div class="ticket" id="ticket"></div>
    </div>
  `;
  renderPosGrid();
  renderTicket();
}

function renderPosGrid(){
  const grid = document.getElementById("pos-grid");
  grid.innerHTML = state.products.map(p => {
    const stock = Number(p.quantity || 0);
    const inCart = state.cart[p.id]?.qty || 0;
    const disabled = stock <= inCart;
    return `
    <button class="product-tile" data-id="${p.id}" ${disabled ? "disabled" : ""}>
      <span class="t-name">${escapeHTML(p.product_name)}</span>
      <span class="t-price num">${money(p.unit_price)}</span>
      <span class="t-stock">${disabled ? t("pos_out_of_stock") : stock + " " + t("batch_remaining")}</span>
    </button>`;
  }).join("");
  grid.querySelectorAll(".product-tile").forEach(btn => {
    btn.addEventListener("click", () => {
      const p = state.products.find(x => x.id === Number(btn.dataset.id));
      const existing = state.cart[p.id];
      state.cart[p.id] = { product: p, qty: (existing?.qty || 0) + 1 };
      renderPosGrid();
      renderTicket();
    });
  });
}

function renderTicket(){
  const box = document.getElementById("ticket");
  const items = Object.values(state.cart);
  const total = items.reduce((sum, it) => sum + Number(it.product.unit_price) * it.qty, 0);

  const lines = items.length ? items.map(it => `
    <div class="ticket-line" data-id="${it.product.id}">
      <span class="l-name">${escapeHTML(it.product.product_name)}</span>
      <button class="qty-btn" data-action="dec">−</button>
      <input class="l-qty-input num" type="number" min="1" max="${it.product.quantity}" value="${it.qty}" />
      <button class="qty-btn" data-action="inc">+</button>
      <span class="l-total num">${money(it.product.unit_price * it.qty)}</span>
    </div>
  `).join("") : `<div class="empty-state">${t("ticket_empty")}</div>`;

  box.innerHTML = `
    <div class="ticket-head">${t("ticket_title")}</div>
    ${lines}
    ${items.length ? `<div class="ticket-total"><span>${t("total")}</span><span class="num">${money(total)}</span></div>` : ""}
    <div class="field" style="margin-top:16px;"><label>${t("customer_name")}</label><input id="pos-customer" /></div>
    <div class="field-row">
      <div class="field"><label>${t("payment_method")}</label>
        <select id="pos-pay-method"><option value="Regular">${t("none")}</option><option value="Deposit">${t("deposit")}</option></select>
      </div>
      <div class="field"><label>${t("payment_amount")}</label><input id="pos-pay-amount" type="number" step="0.01" min="0" /></div>
    </div>
    <div class="field"><label>${t("price_override")}</label><input id="pos-override" type="number" step="0.01" min="0" /></div>
    <button class="btn btn-accent" id="pos-place" style="width:100%;" ${items.length ? "" : "disabled"}>${t("place_order")}</button>
  `;

  box.querySelectorAll(".qty-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const line = btn.closest(".ticket-line");
      const pid = Number(line.dataset.id);
      const entry = state.cart[pid];
      const stock = Number(entry.product.quantity || 0);
      if (btn.dataset.action === "inc" && entry.qty < stock) entry.qty++;
      if (btn.dataset.action === "dec"){ entry.qty--; if (entry.qty <= 0) delete state.cart[pid]; }
      renderPosGrid();
      renderTicket();
    });
  });

  box.querySelectorAll(".l-qty-input").forEach(input => {
    input.addEventListener("change", () => {
      const line = input.closest(".ticket-line");
      const pid = Number(line.dataset.id);
      const entry = state.cart[pid];
      const stock = Number(entry.product.quantity || 0);
      let value = Math.floor(Number(input.value));
      if (!value || value <= 0){ delete state.cart[pid]; renderPosGrid(); renderTicket(); return; }
      if (value > stock){ value = stock; toast(t("pos_out_of_stock"), true); }
      entry.qty = value;
      renderPosGrid();
      renderTicket();
    });
  });

  const placeBtn = document.getElementById("pos-place");
  if (placeBtn){
    placeBtn.addEventListener("click", async () => {
      const customer = document.getElementById("pos-customer").value.trim();
      if (!customer){ toast(t("required_field"), true); return; }
      const payMethod = document.getElementById("pos-pay-method").value;
      const payAmount = document.getElementById("pos-pay-amount").value;
      const override = document.getElementById("pos-override").value;
      const payload = {
        customer_name: customer,
        items: Object.values(state.cart).map(it => ({ product_id: it.product.id, quantity: it.qty })),
      };
      if (payAmount) { payload.payment_method = payMethod; payload.payment_amount = Number(payAmount); }
      if (override) payload.price_override = Number(override);
      await apiPost("/orders", payload);
      toast(t("order_placed"));
      state.cart = {};
      state.ordersLoaded = false;
      await loadProducts();
      renderPosGrid();
      renderTicket();
    });
  }
}

/* ---------------- Orders ---------------- */

async function renderOrders(){
  await loadOrders();
  root().innerHTML = `
    <div class="section-head"><h2>${t("nav_orders")}</h2></div>
    <div id="orders-list"></div>
  `;
  const list = document.getElementById("orders-list");
  if (!state.orders.length){
    list.innerHTML = `<div class="empty-state">${t("no_data")}</div>`;
    return;
  }
  const sorted = [...state.orders].sort((a,b) => (b.order_id||0) - (a.order_id||0));
  list.innerHTML = sorted.map(orderCardHTML).join("");
  wireOrderCards(list, () => renderOrders());
}

function paymentMethodLabel(method){
  if (!method) return "";
  if (method === "Regular") return t("none");
  if (method === "Deposit") return t("deposit");
  return method;
}

function orderStatusBadge(o){
  if (o.is_fully_paid) return `<span class="badge badge-ok">${t("status_paid")}</span>`;
  if (Number(o.total_paid || 0) > 0) return `<span class="badge badge-low">${t("status_partial")}</span>`;
  return `<span class="badge badge-out">${t("status_unpaid")}</span>`;
}

function orderCardHTML(o){
  const itemsSummary = (o.items || []).map(it => `${escapeHTML(it.product_name)} ×${it.quantity}`).join(", ");
  const hasPaymentInfo = o.total_paid !== undefined;
  return `
  <div class="order-card" data-order-id="${o.order_id}">
    <div class="order-card-head">
      <span class="order-cust">${escapeHTML(o.customer_name)}</span>
      <span class="order-meta">${o.order_date} · #${o.order_id ?? "—"}</span>
    </div>
    <div class="order-items">${itemsSummary}</div>
    ${hasPaymentInfo ? `
    <div class="order-items">
      <span class="num">${t("order_paid")}: ${money(o.total_paid)}</span>
      &nbsp;·&nbsp;
      <span class="num">${t("order_remaining")}: ${money(o.remaining_balance)}</span>
      &nbsp;${orderStatusBadge(o)}
      ${(o.payment_methods && o.payment_methods.length) ? `&nbsp;·&nbsp;<span>${t("payment_method")}: ${o.payment_methods.map(paymentMethodLabel).join(" + ")}</span>` : ""}
    </div>` : ""}
    <div class="order-foot">
      <span class="num" style="font-weight:700;">${money(o.total_amount)}</span>
      <div style="display:flex; gap:6px;">
        ${(hasPaymentInfo && !o.is_fully_paid) ? `<button class="btn btn-accent btn-sm" data-action="pay-order" data-id="${o.order_id}">${t("pay_order")}</button>` : ""}
        <button class="btn btn-ghost btn-sm" data-action="edit-order" data-id="${o.order_id}">${t("edit_order")}</button>
        <button class="btn btn-danger btn-sm" data-action="cancel-order" data-id="${o.order_id}">${t("cancel_order")}</button>
      </div>
    </div>
  </div>`;
}

/** Wires cancel/edit/pay buttons for any container full of order-card elements. */
function wireOrderCards(container, onChange){
  container.querySelectorAll("[data-action='cancel-order']").forEach(btn => {
    btn.addEventListener("click", async () => {
      if (!confirm(t("confirm_cancel_order"))) return;
      await apiPost(`/orders/${btn.dataset.id}/cancel`);
      toast(t("order_cancelled"));
      state.ordersLoaded = false;
      if (onChange) onChange(); else renderView();
    });
  });
  container.querySelectorAll("[data-action='edit-order']").forEach(btn => {
    btn.addEventListener("click", () => openEditOrderModal(Number(btn.dataset.id), onChange));
  });
  container.querySelectorAll("[data-action='pay-order']").forEach(btn => {
    btn.addEventListener("click", () => openPayOrderModal(Number(btn.dataset.id), onChange));
  });
}

/* ---------------- Edit order / Pay order ---------------- */

function openPayOrderModal(orderId, onChange){
  const order = state.orders.find(o => o.order_id === orderId);
  if (!order){ toast(t("error_generic"), true); return; }
  if (order.is_fully_paid){ toast(t("fully_paid_already")); return; }
  openModal(`
    <h3>${t("pay_order")} — #${orderId}</h3>
    <p style="color:var(--ink-soft); font-size:0.85rem;">${t("amount_due")}: <span class="num" style="font-weight:700;">${money(order.remaining_balance)}</span></p>
    <div class="field"><label>${t("payment_method")}</label>
      <select id="pay-method"><option value="Regular">${t("none")}</option><option value="Deposit">${t("deposit")}</option></select>
    </div>
    <div class="field"><label>${t("payment_amount")}</label><input id="pay-amount" type="number" step="0.01" min="0.01" value="${Number(order.remaining_balance).toFixed(2)}" /></div>
    <div class="modal-actions">
      <button class="btn btn-ghost" id="m-cancel">${t("cancel")}</button>
      <button class="btn btn-accent" id="m-save">${t("pay_order")}</button>
    </div>
  `);
  document.getElementById("m-cancel").addEventListener("click", closeModal);
  document.getElementById("m-save").addEventListener("click", async () => {
    const amount = Number(document.getElementById("pay-amount").value);
    if (!amount || amount <= 0){ toast(t("required_field"), true); return; }
    await apiPost(`/orders/${orderId}/payments`, {
      payment_method: document.getElementById("pay-method").value,
      amount,
    });
    toast(t("payment_recorded"));
    closeModal();
    state.ordersLoaded = false;
    await loadOrders();
    if (onChange) onChange(); else renderView();
  });
}

function openEditOrderModal(orderId, onChange){
  const order = state.orders.find(o => o.order_id === orderId);
  if (!order){ toast(t("error_generic"), true); return; }

  // Local editable copy of the item list: [{product_id, product_name, quantity}]
  const editItems = order.items.map(it => ({ product_id: it.product_id, product_name: it.product_name, quantity: it.quantity }));

  const renderModalBody = () => `
    <h3>${t("edit_order")} — #${orderId}</h3>
    <div class="field"><label>${t("customer_name")}</label><input id="eo-customer" value="${escapeHTML(order.customer_name)}" /></div>
    <div class="field"><label>${t("price_override")}</label><input id="eo-override" type="number" step="0.01" min="0" placeholder="${money(order.total_amount)}" /></div>

    <div class="field"><label>${t("current_items")}</label></div>
    <div id="eo-items">
      ${editItems.map((it, idx) => `
        <div class="field-row" data-idx="${idx}" style="align-items:center; margin-bottom:8px;">
          <span style="flex:1; font-size:0.88rem;">${escapeHTML(it.product_name)}</span>
          <input class="eo-qty num" type="number" min="1" value="${it.quantity}" style="width:70px; border:1px solid var(--border-strong); border-radius:6px; padding:6px;" />
          <button class="btn btn-danger btn-sm" data-action="eo-remove" data-idx="${idx}">${t("remove")}</button>
        </div>
      `).join("")}
    </div>

    <div class="field-row" style="align-items:end;">
      <div class="field" style="flex:2;"><label>${t("add_item")}</label>
        <select id="eo-add-product">
          <option value="">${t("select_product")}</option>
          ${state.products.map(p => `<option value="${p.id}">${escapeHTML(p.product_name)}</option>`).join("")}
        </select>
      </div>
      <div class="field" style="flex:1;"><label>${t("quantity")}</label><input id="eo-add-qty" type="number" min="1" value="1" /></div>
      <button class="btn btn-ghost btn-sm" id="eo-add-btn" style="margin-bottom:12px;">${t("add")}</button>
    </div>

    <div class="modal-actions">
      <button class="btn btn-ghost" id="m-cancel">${t("cancel")}</button>
      <button class="btn btn-primary" id="m-save">${t("save")}</button>
    </div>
  `;

  const wire = () => {
    document.getElementById("m-cancel").addEventListener("click", closeModal);

    document.querySelectorAll(".eo-qty").forEach(input => {
      input.addEventListener("change", (e) => {
        const idx = Number(e.target.closest("[data-idx]").dataset.idx);
        editItems[idx].quantity = Math.max(1, Math.floor(Number(input.value) || 1));
      });
    });

    document.querySelectorAll("[data-action='eo-remove']").forEach(btn => {
      btn.addEventListener("click", () => {
        editItems.splice(Number(btn.dataset.idx), 1);
        openModal(renderModalBody());
        wire();
      });
    });

    document.getElementById("eo-add-btn").addEventListener("click", () => {
      const select = document.getElementById("eo-add-product");
      const pid = Number(select.value);
      if (!pid) return;
      const product = state.products.find(p => p.id === pid);
      const qty = Math.max(1, Math.floor(Number(document.getElementById("eo-add-qty").value) || 1));
      const existing = editItems.find(it => it.product_id === pid);
      if (existing) existing.quantity += qty;
      else editItems.push({ product_id: pid, product_name: product.product_name, quantity: qty });
      openModal(renderModalBody());
      wire();
    });

    document.getElementById("m-save").addEventListener("click", async () => {
      if (!editItems.length){ toast(t("required_field"), true); return; }
      const newCustomer = document.getElementById("eo-customer").value.trim();
      const overrideVal = document.getElementById("eo-override").value;

      await apiPatch(`/orders/${orderId}/items`, editItems.map(it => ({ product_id: it.product_id, quantity: it.quantity })));
      await apiPatch(`/orders/${orderId}/header`, {
        customer_name: newCustomer || undefined,
        price_override: overrideVal ? Number(overrideVal) : undefined,
      });

      toast(t("order_updated"));
      closeModal();
      state.ordersLoaded = false;
      await loadOrders();
      if (onChange) onChange(); else renderView();
    });
  };

  openModal(renderModalBody());
  wire();
}

/* ---------------- Reports ---------------- */

async function renderReports(){
  root().innerHTML = `
    <div class="tabs" id="report-tabs">
      <button class="tab-btn" data-tab="batches">${t("reports_batches")}</button>
      <button class="tab-btn" data-tab="customers">${t("reports_customers")}</button>
      <button class="tab-btn" data-tab="ranking">${t("reports_ranking")}</button>
      <button class="tab-btn" data-tab="search">${t("reports_search")}</button>
    </div>
    <div id="report-body" class="card">${t("loading")}</div>
  `;
  document.querySelectorAll("#report-tabs .tab-btn").forEach(btn => {
    btn.classList.toggle("is-active", btn.dataset.tab === state.reportsTab);
    btn.addEventListener("click", () => {
      state.reportsTab = btn.dataset.tab;
      document.querySelectorAll("#report-tabs .tab-btn").forEach(b => b.classList.toggle("is-active", b === btn));
      loadReportTab();
    });
  });
  loadReportTab();
}

async function loadReportTab(){
  const body = document.getElementById("report-body");
  body.innerHTML = t("loading");
  const tab = state.reportsTab;

  if (tab === "batches"){
    const res = await apiGet("/reports/batches?only_available=true");
    const data = (res && res.data) || [];
    body.innerHTML = data.length ? `<table><thead><tr>
        <th>${t("col_product")}</th><th>${t("batch_location")}</th><th>${t("col_stock")}</th><th>${t("batch_entered")}</th>
      </tr></thead><tbody>${data.map(b => `
        <tr><td>${escapeHTML(b.product_name)}</td><td>${formatLocation(b)}</td>
        <td class="num" dir="ltr">${Math.max(0,b.count-b.trashed)}/${b.count}</td><td class="num" dir="ltr">${b.date_entered}</td></tr>
      `).join("")}</tbody></table>` : `<div class="empty-state">${t("no_data")}</div>`;
  }

  else if (tab === "customers"){
    if (!state.ordersLoaded) await loadOrders();
    const customerMap = buildCustomerSummary(state.orders);
    const customers = Object.values(customerMap).sort((a,b) => b.totalSpent - a.totalSpent);
    body.innerHTML = customers.length ? customers.map((c, idx) => `
      <div class="rank-row customer-row" data-idx="${idx}" style="cursor:pointer;">
        <div class="rank-name">${escapeHTML(c.customerName)}</div>
        <div style="flex:1; display:flex; gap:16px; font-size:0.82rem; color:var(--ink-soft);">
          <span class="num">${t("customer_spent")}: ${money(c.totalSpent)}</span>
          <span class="num">${t("customer_paid")}: ${money(c.totalPaid)}</span>
          <span>${t("customer_order_count")}: ${c.orderCount}</span>
        </div>
      </div>`).join("") : `<div class="empty-state">${t("no_data")}</div>`;

    body.querySelectorAll(".customer-row").forEach(row => {
      row.addEventListener("click", () => {
        const c = customers[Number(row.dataset.idx)];
        openModal(`
          <h3>${t("order_history_for")} ${escapeHTML(c.customerName)}</h3>
          <div id="customer-history-list">${c.orders.map(orderCardHTML).join("")}</div>
          <div class="modal-actions"><button class="btn btn-ghost" id="m-close">${t("close")}</button></div>
        `);
        document.getElementById("m-close").addEventListener("click", closeModal);
        wireOrderCards(document.getElementById("customer-history-list"), () => { closeModal(); loadReportTab(); });
      });
    });
  }

  else if (tab === "ranking"){
    const res = await apiGet("/reports/products/ranking");
    const data = (res && res.data) || [];
    const max = Math.max(1, ...data.map(p => p.total_quantity_sold));
    body.innerHTML = data.length ? data.map(p => `
      <div class="rank-row">
        <div class="rank-name">${escapeHTML(p.product_name)}</div>
        <div class="rank-bar-track"><div class="rank-bar-fill" style="width:${(p.total_quantity_sold/max)*100}%"></div></div>
        <div class="rank-value">${p.total_quantity_sold} ${t("units_sold")}</div>
      </div>`).join("") : `<div class="empty-state">${t("no_data")}</div>`;
  }

  else if (tab === "search"){
    body.innerHTML = `
      <div class="field-row">
        <div class="field"><label>${t("reports_search")}</label><input id="search-customer" placeholder="${t('search_customer_placeholder')}" /></div>
        <div class="field"><label>${t("col_product")}</label><input id="search-product" placeholder="${t('search_product_placeholder')}" /></div>
      </div>
      <div class="field-row">
        <div class="field"><label>${t("search_payment_method")}</label>
          <select id="search-pay-method">
            <option value="">${t("filter_all")}</option>
            <option value="Regular">${t("none")}</option>
            <option value="Deposit">${t("deposit")}</option>
          </select>
        </div>
        <div class="field"><label>${t("search_payment_status")}</label>
          <select id="search-pay-status">
            <option value="">${t("filter_all")}</option>
            <option value="paid">${t("filter_paid")}</option>
            <option value="unpaid">${t("filter_unpaid")}</option>
          </select>
        </div>
      </div>
      <div class="field-row">
        <div class="field"><label>${t("date_from")}</label><input id="search-date-from" type="date" /></div>
        <div class="field"><label>${t("date_to")}</label><input id="search-date-to" type="date" /></div>
      </div>
      <div id="search-results"></div>
    `;
    const customerInput = document.getElementById("search-customer");
    const productInput = document.getElementById("search-product");
    const methodSelect = document.getElementById("search-pay-method");
    const statusSelect = document.getElementById("search-pay-status");
    const dateFrom = document.getElementById("search-date-from");
    const dateTo = document.getElementById("search-date-to");
    const results = document.getElementById("search-results");

    let timer = null;
    const runSearch = () => {
      clearTimeout(timer);
      timer = setTimeout(async () => {
        const params = new URLSearchParams();
        if (customerInput.value.trim()) params.set("customer_name", customerInput.value.trim());
        if (productInput.value.trim()) params.set("product_name", productInput.value.trim());
        if (methodSelect.value) params.set("payment_method", methodSelect.value);
        if (statusSelect.value) params.set("payment_status", statusSelect.value);
        if (dateFrom.value) params.set("start_date", dateFrom.value);
        if (dateTo.value) params.set("end_date", dateTo.value);
        if (![...params.keys()].length){ results.innerHTML = ""; return; }
        const res = await apiGet(`/reports/orders/search?${params.toString()}`);
        const data = (res && res.data) || [];
        results.innerHTML = data.length ? data.map(orderCardHTML).join("") : `<div class="empty-state">${t("no_data")}</div>`;
        wireOrderCards(results);
      }, 350);
    };
    [customerInput, productInput].forEach(el => el.addEventListener("input", runSearch));
    [methodSelect, statusSelect, dateFrom, dateTo].forEach(el => el.addEventListener("change", runSearch));
  }
}

/* ---------------- utils ---------------- */

function escapeHTML(str){
  return String(str ?? "").replace(/[&<>"']/g, (c) => ({ "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;" }[c]));
}

/* ---------------- init ---------------- */

document.querySelectorAll(".lang-btn").forEach(b => b.classList.toggle("is-active", b.dataset.lang === state.lang));
applyLanguage();
renderView();
