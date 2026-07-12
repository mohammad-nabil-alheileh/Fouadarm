const API_BASE_URL = 'http://127.0.0.1:5000';

document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const fromDate = urlParams.get('from');
    const toDate = urlParams.get('to');

    // 1. Update timeframe meta header text
    const metaSpan = document.querySelector('.results-meta h3 span');
    if (metaSpan) {
        metaSpan.textContent = `من ${fromDate || '...'} إلى ${toDate || '...'}`;
    }

    if (fromDate && toDate) {
        fetchAndFilterOrdersByDate(fromDate, toDate);
    } else {
        const tbody = document.querySelector('table tbody');
        if (tbody) {
            tbody.innerHTML = `<tr class="empty-state-row"><td colspan="3"><div class="empty-state">⚠️ الرجاء تحديد التواريخ بشكل صحيح من صفحة البحث.</div></td></tr>`;
        }
    }

    // 2. Sidebar Link Highlighter (Active Menu Fix)
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
});

async function fetchAndFilterOrdersByDate(from, to) {
    const tbody = document.querySelector('table tbody');
    if (!tbody) return;

    try {
        // Step 1: Fetch global products mapping catalog
        const productsResponse = await fetch(`${API_BASE_URL}/products`);
        if (!productsResponse.ok) throw new Error('Failed fetching products catalog maps.');
        const productsCatalog = await productsResponse.json();
        
        const productMap = {};
        productsCatalog.forEach(p => {
            const pId = p.product_id !== undefined ? p.product_id : p.id;
            productMap[pId] = p.product_name;
        });

        // Step 2: Fetch global orders tracking dataset
        const response = await fetch(`${API_BASE_URL}/orders`);
        if (!response.ok) throw new Error('Database connection issue encountered.');
        
        const allOrders = await response.json();
        tbody.innerHTML = '';

        // Step 3: Populate and group dataset records by unique customer identities
        const customerData = {};

        allOrders.forEach(itemWrapper => {
            const orderInfo = itemWrapper.order;
            const orderItems = itemWrapper.items;

            if (!orderInfo || !orderInfo.sale_date) return;
            const currentOrderDate = orderInfo.sale_date.split('T')[0].split(' ')[0]; 

            if (currentOrderDate >= from && currentOrderDate <= to) {
                const cName = orderInfo.customer_name;
                const totalPrice = parseFloat(orderInfo.total_price) || 0;

                const itemsText = orderItems && orderItems.length > 0
                    ? orderItems.map(i => {
                        const productName = productMap[i.product_id] || `منتج مجهول #${i.product_id}`;
                        return `${productName} (x${i.quantity})`;
                    }).join(' + ')
                    : 'لا توجد منتجات مسجلة';

                if (!customerData[cName]) {
                    customerData[cName] = {
                        allPurchases: [], // Stores structured objects instead of raw strings
                        totalSpent: 0
                    };
                }

                // Append the timestamp alongside the line-item layout metrics
                customerData[cName].allPurchases.push({
                    text: itemsText,
                    price: totalPrice,
                    date: currentOrderDate // Keep raw timestamp string safely for sorting later
                });
                customerData[cName].totalSpent += totalPrice;
            }
        });

        // Sort customer names alphabetically
        const sortedCustomerNames = Object.keys(customerData).sort((a, b) => a.localeCompare(b, 'ar'));

        if (sortedCustomerNames.length === 0) {
            tbody.innerHTML = `
                <tr class="empty-state-row"><td colspan="3"><div class="empty-state">📅 لا توجد مبيعات في هذه الفترة.</div></td></tr>
            `;
            return;
        }

        // Step 4: Render chronological lists into tables dynamically
        sortedCustomerNames.forEach(name => {
            const tr = document.createElement('tr');
            
            // ✅ Sort individual customer records chronologically from Older to Newer
            customerData[name].allPurchases.sort((invoiceA, invoiceB) => {
                return new Date(invoiceA.date) - new Date(invoiceB.date);
            });

            // ✅ Generate dynamic HTML containing the calendar date badge tag beneath items
            const purchasesDisplay = customerData[name].allPurchases.map(p => {
                return `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px dashed #e2e8f0; padding-bottom: 6px;">
                        <div style="display: flex; flex-direction: column; gap: 2px;">
                            <span class="text-muted" style="font-weight: 500;">• ${p.text}</span>
                            <span style="font-size: 0.8rem; color: #94a3b8; margin-right: 10px;">📅 ${p.date}</span>
                        </div>
                        <span style="font-weight: 600; color: #475569;">${p.price.toFixed(2)} JD</span>
                    </div>`;
            }).join('');
            
            const formattedTotal = customerData[name].totalSpent.toFixed(2);

            tr.innerHTML = `
                <td class="customer-name-cell"><strong>${name}</strong></td>
                <td>
                    <div class="purchase-history">${purchasesDisplay}</div>
                    <div class="user-total-badge" style="margin-top: 12px;">
                        💵 المجموع الكلي للمدفوعات: <strong>${formattedTotal} JD</strong>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch(err) {
        console.error(err);
        tbody.innerHTML = `<tr class="empty-state-row"><td colspan="3"><div class="empty-state">❌ فشل تحميل بيانات الفواتير الزمنية: ${err.message}</div></td></tr>`;
    }
}