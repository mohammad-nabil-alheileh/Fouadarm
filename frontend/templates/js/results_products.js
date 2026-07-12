const API_BASE_URL = 'http://127.0.0.1:5000'; // ✅ Retained your custom Port 5000 configuration

document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const fromDate = urlParams.get('from');
    const toDate = urlParams.get('to');

    // 1. تحديث نصوص الفترة الزمنية في العنوان
    const metaSpan = document.querySelector('.results-meta h3 span');
    if (metaSpan) {
        metaSpan.textContent = `من ${fromDate || 'غير محدد'} إلى ${toDate || 'غير محدد'}`;
    }

    // 2. تفعيل التظليل التلقائي للقائمة الجانبية (Active Menu Fix)
    const menuItems = document.querySelectorAll('.menu-item');
    const currentPageFile = window.location.pathname.split('/').pop();

    menuItems.forEach(item => {
        const itemHref = item.getAttribute('href');
        const itemPageFile = itemHref.split('/').pop();

        if ((itemHref === '/' || itemHref === '') && (currentPageFile === '' || currentPageFile === 'index.html')) {
            item.classList.add('active');
        } else if (itemPageFile !== '' && currentPageFile === itemPageFile) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // 3. التحقق من التواريخ وبدء جلب البيانات واحتسابها
    if (fromDate && toDate) {
        fetchAndAggregateProductSales(fromDate, toDate);
    } else {
        renderEmptyState("الرجاء تحديد التواريخ بشكل صحيح من صفحة البحث.");
    }
});

async function fetchAndAggregateProductSales(from, to) {
    const tbody = document.querySelector('table tbody');
    if (!tbody) return;

    try {
        // خطوة 1: جلب بيانات المنتجات لبناء قاموس البحث المساعد
        const productsResponse = await fetch(`${API_BASE_URL}/products`);
        if (!productsResponse.ok) throw new Error('Failed fetching products catalog maps.');
        const productsCatalog = await productsResponse.json();
        
        const productMap = {};
        productsCatalog.forEach(p => {
            const pId = p.product_id !== undefined ? p.product_id : p.id;
            productMap[pId] = { name: p.product_name, price: p.unit_price };
        });

        // خطوة 2: جلب كافة الفواتير من الخادم
        const ordersResponse = await fetch(`${API_BASE_URL}/orders`);
        if (!ordersResponse.ok) throw new Error('Failed to retrieve core order lists.');
        const allOrders = await ordersResponse.json();
        
        tbody.innerHTML = '';

        if (!allOrders || allOrders.length === 0) {
            renderEmptyState("لم يتم بيع أي منتجات خلال هذه الفترة الزمنية.");
            return;
        }

        // ✅ إضافة الترتيب: فرز الفواتير بالكامل من الأقدم للأحدث قبل البدء بالتجميع والاحتساب
        allOrders.sort((a, b) => {
            return new Date(a.order.sale_date) - new Date(b.order.sale_date);
        });

        const productStats = {};

        // خطوة 3: التجميع والاحتساب بناءً على النطاق الزمني المُحدد (يمر الآن من الأقدم للأحدث)
        allOrders.forEach(itemWrapper => {
            const orderInfo = itemWrapper.order;
            const orderItems = itemWrapper.items;

            if (!orderInfo || !orderInfo.sale_date) return;
            const currentOrderDate = orderInfo.sale_date.split('T')[0].split(' ')[0];
            
            if (currentOrderDate >= from && currentOrderDate <= to) {
                if (orderItems && orderItems.length > 0) {
                    orderItems.forEach(item => {
                        const lookup = productMap[item.product_id] || { name: `منتج مجهول #${item.product_id}`, price: 0 };
                        const name = lookup.name;
                        const price = lookup.price;

                        if (!productStats[name]) {
                            productStats[name] = { qty: 0, revenue: 0 };
                        }
                        productStats[name].qty += item.quantity;
                        productStats[name].revenue += (item.quantity * price);
                    });
                }
            }
        });

        // ترتيب المنتجات الناتجة أبجدياً لضمان مظهر منظم داخل الجدول
        const productNames = Object.keys(productStats).sort((a, b) => a.localeCompare(b, 'ar'));
        
        if (productNames.length === 0) {
            renderEmptyState("لم يتم بيع أي منتجات خلال هذه الفترة الزمنية.");
            return;
        }

        // خطوة 4: حقن الصفوف والبيانات المجمعة داخل الجدول المخصص
        productNames.forEach(name => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${name}</strong></td>
                <td class="qty-column">${productStats[name].qty}</td>
                <td class="text-left price-column">${productStats[name].revenue.toFixed(2)} JD</td>
            `;
            tbody.appendChild(tr);
        });

    } catch (error) {
        console.error("Fetch/Aggregation Error: ", error);
        tbody.innerHTML = `<tr class="empty-state-row"><td colspan="3"><div class="empty-state">❌ خطأ أثناء تجميع إحصائيات المنتجات: ${error.message}</div></td></tr>`;
    }
}

function renderEmptyState(message) {
    const tbody = document.querySelector('table tbody');
    if (tbody) {
        tbody.innerHTML = `
            <tr class="empty-state-row">
                <td colspan="3">
                    <div class="empty-state">📦 ${message}</div>
                </td>
            </tr>
        `;
    }
}