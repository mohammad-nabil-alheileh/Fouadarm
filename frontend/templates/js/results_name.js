const API_BASE_URL = 'http://127.0.0.1:5000';

document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const targetCustomerName = urlParams.get('name');

    // 1. Update filter text elements at the top
    const metaValue = document.querySelector('.search-meta .meta-value');
    if (targetCustomerName) {
        if (metaValue) metaValue.textContent = targetCustomerName;
        fetchCustomerData(targetCustomerName);
    } else {
        renderEmptyState("اسم العميل مفقود في الرابط الأساسي.");
    }

    // 2. Active Menu Highlighter Fix
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

async function fetchCustomerData(name) {
    const tbody = document.querySelector('table tbody');
    if (!tbody) return;

    try {
        // Step 1: Fetch products map dictionary
        const productsResponse = await fetch(`${API_BASE_URL}/products`);
        if (!productsResponse.ok) throw new Error('Failed fetching products catalog maps.');
        const productsCatalog = await productsResponse.json();
        
        const productMap = {};
        productsCatalog.forEach(p => {
            const pId = p.product_id !== undefined ? p.product_id : p.id;
            productMap[pId] = p.product_name;
        });

        // Step 2: Fetch customer ledger history data
        const response = await fetch(`${API_BASE_URL}/orders/customer/${encodeURIComponent(name)}`);
        if (!response.ok) throw new Error('Failed parsing customer ledger records');
        
        const dataPayload = await response.json();
        tbody.innerHTML = ''; 

        if (!dataPayload || dataPayload.length === 0) {
            renderEmptyState("لا توجد فواتير مسجلة لهذا الاسم.");
            return;
        }

        // ✅ FIXED: Sort data from Older to Newer chronologically
        dataPayload.sort((a, b) => {
            const dateA = new Date(a.order.sale_date);
            const dateB = new Date(b.order.sale_date);
            return dateB - dateA; // For newer to older, you would use (dateB - dateA)
        });

        // Step 3: Loop and aggregate total pricing calculations safely
        let totalSpentForAllOrders = 0;
        const allPurchasesHTML = dataPayload.map(itemWrapper => {
            const orderInfo = itemWrapper.order;
            const orderItems = itemWrapper.items;
            const orderPrice = parseFloat(orderInfo.total_price) || 0;
            
            const rawDate = orderInfo.sale_date || '';
            const orderDate = rawDate.split('T')[0].split(' ')[0];
            
            totalSpentForAllOrders += orderPrice;

            const itemsString = orderItems && orderItems.length > 0 
                ? orderItems.map(i => {
                    const productName = productMap[i.product_id] || `منتج مجهول #${i.product_id}`;
                    return `${productName} (x${i.quantity})`;
                }).join(' + ')
                : 'لا توجد منتجات مسجلة';

            return `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px dashed #e2e8f0; padding-bottom: 6px;">
                    <div style="display: flex; flex-direction: column; gap: 2px;">
                        <span class="text-muted" style="font-weight: 500;">• ${itemsString}</span>
                        <span style="font-size: 0.8rem; color: #94a3b8; margin-right: 10px;">📅 ${orderDate}</span>
                    </div>
                    <span style="font-weight: 600; color: #475569;">${orderPrice.toFixed(2)} JD</span>
                </div>
            `;
        }).join('');

        // Step 4: Inject row structure into the UI DOM container
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="fw-semibold" style="vertical-align: top; padding-top: 15px;"><strong>${name}</strong></td>
            <td>
                <div class="purchase-history">${allPurchasesHTML}</div>
                <div class="user-total-badge" style="background-color: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; padding: 6px 12px; border-radius: 6px; display: inline-block; font-size: 0.9rem; margin-top: 12px;">
                    💵 إجمالي فواتير العميل الكلي: <strong>${totalSpentForAllOrders.toFixed(2)} JD</strong>
                </div>
            </td>
        `;
        tbody.appendChild(tr);

    } catch (error) {
        console.error(error);
        renderEmptyState("حدث خطأ غير متوقع أثناء استدعاء بيانات الفواتير.");
    }
}

function renderEmptyState(message) {
    const tbody = document.querySelector('table tbody');
    if (tbody) {
        tbody.innerHTML = `
            <tr class="empty-state-row">
                <td colspan="2">
                    <div class="empty-state">📭 ${message}</div>
                </td>
            </tr>
        `;
    }
}