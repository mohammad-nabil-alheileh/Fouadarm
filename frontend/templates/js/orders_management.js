const API_BASE_URL = 'http://127.0.0.1:5000';

document.addEventListener('DOMContentLoaded', () => {
    loadAllProductsFromDB().then(() => {
        loadOrdersTable();
    });
});

const menuItems = document.querySelectorAll('.menu-item');
    const currentUrl = window.location.pathname;

    menuItems.forEach(item => {
        // إذا كان رابط العنصر موجوداً داخل رابط الصفحة الحالية
        if (item.getAttribute('href') && currentUrl.includes(item.getAttribute('href'))) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

// جلب كل المنتجات وتخزينها عالمياً لغايات التعديل والإضافة
async function loadAllProductsFromDB() {
    try {
        const response = await fetch(`${API_BASE_URL}/products`);
        if (response.ok) {
            window.allProductsList = await response.json();
            console.log("تم تحميل المنتجات بنجاح لعمليات التعديل:", window.allProductsList);
        }
    } catch (err) {
        console.error("فشل جلب قائمة المنتجات المساعدة:", err);
    }
}

// GET: جلب وعرض كل الفواتير الحالية من السيرفر
async function loadOrdersTable() {
    const tbody = document.querySelector('#orders-table tbody');
    if (!tbody) return;

    try {
        const response = await fetch(`${API_BASE_URL}/orders`);
        if (!response.ok) throw new Error('فشل جلب بيانات الفواتير من الخادم.');
        
        const rawOrders = await response.json();
        tbody.innerHTML = '';

        if (!rawOrders || rawOrders.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">لا توجد فواتير مسجلة في النظام حالياً.</td></tr>`;
            return;
        }

        rawOrders.forEach(wrapper => {
            const orderData = wrapper.order;
            if (!orderData) return;

            const id = orderData.sale_id;
            const customerName = orderData.customer_name || "عميل غير مسمى";
            const totalPrice = (orderData.total_price && !isNaN(parseFloat(orderData.total_price))) ? parseFloat(orderData.total_price).toFixed(2) : "0.00";
            const saleDate = orderData.sale_date ? orderData.sale_date.split('T')[0] : 'غير محدد';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><code>#${id}</code></td>
                <td><strong>${customerName}</strong></td>
                <td>${saleDate}</td>
                <td>${totalPrice} JD</td>
                <td class="td-actions">
                    <button class="btn-secondary btn-edit" type="button" onclick="loadOrderToEdit(${id})">تعديل الفاتورة والمنتجات</button>
                    <button class="btn-danger btn-delete-item" type="button" onclick="deleteWholeOrder(${id})">حذف الفاتورة</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error(err);
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--danger-color);">❌ فشل الاتصال بقاعدة البيانات لجلب الفواتير.</td></tr>`;
    }
}

// GET (Single Order): تحميل الفاتورة الواحدة
async function loadOrderToEdit(saleId) {
    try {
        const response = await fetch(`${API_BASE_URL}/orders/${saleId}`);
        if (!response.ok) throw new Error('تعذر جلب تفاصيل الفاتورة المطلوبة.');

        const wrapper = await response.json();
        const orderData = wrapper.order;
        const itemsData = wrapper.items;

        if (!orderData) throw new Error('بيانات الفاتورة الداخلية تالفة.');

        document.getElementById('edit-sale-id').value = orderData.sale_id;
        document.getElementById('customer-name').value = orderData.customer_name;
        
        // عرض السعر المحدث القادم مباشرة من السيرفر وقاعدة البيانات
        document.getElementById('order-total-price').value = parseFloat(orderData.total_price).toFixed(2);

        const itemsContainer = document.getElementById('order-items-container');
        itemsContainer.innerHTML = '';

        // زر إضافة صنف جديد
        const addRowBtnContainer = document.createElement('div');
        addRowBtnContainer.style.marginBottom = '1.5rem';
        addRowBtnContainer.innerHTML = `
            <button type="button" class="btn-primary" style="background-color: #0284c7; padding: 0.5rem 1.5rem; font-size: 0.85rem;" onclick="addNewItemRowToCurrentOrder()">➕ إضافة صنف جديد لهذه الفاتورة</button>
        `;
        itemsContainer.appendChild(addRowBtnContainer);

        if (!itemsData || itemsData.length === 0) {
            const noItemsText = document.createElement('p');
            noItemsText.id = "no-items-warning";
            noItemsText.style.color = "var(--text-muted)";
            noItemsText.innerText = "لا توجد منتجات داخل هذه الفاتورة حالياً.";
            itemsContainer.appendChild(noItemsText);
        } else {
            itemsData.forEach(item => {
                createItemRowUI(item);
            });
        }

        // الحقل مفتوح للتعديل اليدوي المستقل في أي وقت
        const totalPriceInput = document.getElementById('order-total-price');
        if (totalPriceInput) {
            totalPriceInput.removeAttribute('readonly');
        }

        const editCard = document.getElementById('edit-order-card');
        editCard.classList.remove('hidden');
        editCard.scrollIntoView({ behavior: 'smooth' });

    } catch (err) {
        alert(`خطأ أثناء تحميل الفاتورة: ${err.message}`);
    }
}

// بناء سطر منتج (تم جعل اختيار الصنف للقراءة فقط لزيادة الاستقرار)
function createItemRowUI(item) {
    const itemsContainer = document.getElementById('order-items-container');
    const itemRow = document.createElement('div');
    itemRow.className = 'item-edit-row';
    
    itemRow.dataset.saleItemId = item.sale_item;
    itemRow.dataset.serverQty = item.quantity;
    itemRow.dataset.serverPrice = item.unit_price || 0;
    
    let currentProductName = "منتج غير معروف";
    if (window.allProductsList && window.allProductsList.length > 0) {
        const found = window.allProductsList.find(p => (p.product_id !== undefined ? p.product_id : p.id) === item.product_id);
        if (found) {
            currentProductName = found.product_name;
            if (!itemRow.dataset.serverPrice || itemRow.dataset.serverPrice == 0) {
                itemRow.dataset.serverPrice = found.unit_price;
            }
        }
    }

    itemRow.innerHTML = `
        <div class="input-group" style="min-width: 220px;">
            <label>الصنف</label>
            <input type="text" value="${currentProductName} (${itemRow.dataset.serverPrice} JD)" readonly style="background-color: #e2e8f0; font-weight: 500; cursor: not-allowed; color: #334155;">
        </div>
        <div class="input-group">
            <label>الكمية المطلوبة</label>
            <input type="number" class="edit-quantity-input" value="${item.quantity}" min="1">
        </div>
        <div class="input-group" style="display: flex; gap: 0.5rem; align-items: flex-end;">
            <button type="button" class="btn-secondary" style="height: 44px; padding: 0 1rem; background-color: #bbf7d0; color: #166534;" onclick="saveQuantityChangesOnly(this)">🔄 تحديث الكمية</button>
            <button type="button" class="btn-danger" style="height: 44px;" onclick="deleteSingleItemFromServer(this)">حذف</button>
        </div>
    `;
    itemsContainer.appendChild(itemRow);
}

// إضافة سطر فارغ لمنتج جديد
function addNewItemRowToCurrentOrder() {
    const warning = document.getElementById('no-items-warning');
    if (warning) warning.remove();

    const itemsContainer = document.getElementById('order-items-container');
    const itemRow = document.createElement('div');
    itemRow.className = 'item-edit-row';
    itemRow.dataset.saleItemId = "NEW";
    
    let selectOptionsHtml = '<option value="" data-price="0" selected disabled>اختر المنتج المراد إضافته...</option>';
    if (window.allProductsList && window.allProductsList.length > 0) {
        window.allProductsList.forEach(p => {
            const pId = p.product_id !== undefined ? p.product_id : p.id;
            selectOptionsHtml += `<option value="${pId}" data-price="${p.unit_price}">${p.product_name} (${p.unit_price} JD)</option>';`;
        });
    }

    itemRow.innerHTML = `
        <div class="input-group" style="min-width: 220px;">
            <label>اختر صنف جديد</label>
            <select class="edit-product-select">
                ${selectOptionsHtml}
            </select>
        </div>
        <div class="input-group">
            <label>الكمية</label>
            <input type="number" class="edit-quantity-input" value="1" min="1">
        </div>
        <div class="input-group" style="display: flex; gap: 0.5rem; align-items: flex-end;">
            <button type="button" class="btn-secondary" style="height: 44px; padding: 0 1rem; background-color: #bae6fd; color: #0369a1;" onclick="saveNewItemToServer(this)">💾 حفظ وإدراج</button>
            <button type="button" class="btn-danger" style="height: 44px;" onclick="this.closest('.item-edit-row').remove();">إلغاء</button>
        </div>
    `;
    itemsContainer.appendChild(itemRow);
}

// دالة مساعدة لتحديث السعر الإجمالي الكلي في الباك إيند عند الحذف أو الإضافة
async function updateOrderTotalOnServer(saleId, newTotal) {
    try {
        await fetch(`${API_BASE_URL}/orders/${saleId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ total_price: parseFloat(newTotal) })
        });
    } catch (err) {
        console.error("فشل تحديث السعر الإجمالي في السيرفر:", err);
    }
}

// POST: حفظ صنف جديد وإضافته للإجمالي
async function saveNewItemToServer(buttonElement) {
    const row = buttonElement.closest('.item-edit-row');
    const saleId = parseInt(document.getElementById('edit-sale-id').value);
    const select = row.querySelector('.edit-product-select');
    const qtyInput = row.querySelector('.edit-quantity-input');

    if (!select || !select.value) {
        alert('الرجاء اختيار صنف أولاً!');
        return;
    }

    const productId = parseInt(select.value);
    const quantity = parseInt(qtyInput.value);

    const selectedOption = select.options[select.selectedIndex];
    const unitPrice = parseFloat(selectedOption.getAttribute('data-price')) || 0;
    const addedAmount = unitPrice * quantity;

    const currentTotal = parseFloat(document.getElementById('order-total-price').value) || 0;
    const updatedTotal = currentTotal + addedAmount;

    try {
        const response = await fetch(`${API_BASE_URL}/order-items?sale_id=${saleId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId, quantity: quantity })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'المخزون غير كافٍ.');
        }

        await updateOrderTotalOnServer(saleId, updatedTotal);

        alert('تم إضافة المنتج وتحديث السعر الإجمالي تلقائياً!');
        loadOrderToEdit(saleId); 
        loadOrdersTable();
    } catch (error) {
        alert(`خطأ: ${error.message}`);
    }
}

// PATCH: تحديث كمية المنتج فقط
async function saveQuantityChangesOnly(buttonElement) {
    const row = buttonElement.closest('.item-edit-row');
    const saleItemId = row.dataset.saleItemId;
    const saleId = document.getElementById('edit-sale-id').value;
    const qtyInput = row.querySelector('.edit-quantity-input');

    const newQuantity = parseInt(qtyInput.value);
    const oldQuantity = parseInt(row.dataset.serverQty);

    if (newQuantity === oldQuantity) {
        alert('الكمية لم تتغير، لم يتم إجراء تعديلات.');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/order-items/${saleItemId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantity: newQuantity })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'المخزون غير كافٍ للكمية المطلوبة.');
        }

        alert('تم تحديث الكمية وقام السيرفر بإعادة احتساب إجمالي الفاتورة تلقائياً!');
        loadOrderToEdit(saleId);
        loadOrdersTable();
    } catch (error) {
        alert(`خطأ: ${error.message}`);
    }
}

// DELETE: حذف صنف ويطرح قيمته بالكامل
async function deleteSingleItemFromServer(buttonElement) {
    const row = buttonElement.closest('.item-edit-row');
    const saleItemId = row.dataset.saleItemId;
    const saleId = document.getElementById('edit-sale-id').value;

    const totalRemainingRows = document.querySelectorAll('.item-edit-row').length;

    if (totalRemainingRows <= 1) {
        // تم دمج رسالة التأكيد هنا أيضاً لحماية الصنف الأخير وحذف الفاتورة التلقائي
        const confirmDeleteOrder = confirm(
            "⚠️ تنبيه: هذا هو الصنف الأخير في الفاتورة!\n\n" +
            "حذفه سيؤدي إلى حذف الفاتورة رقم #" + saleId + " بالكامل.\n\n" +
            "هل تريد حذف الفاتورة كاملة؟"
        );
        if (confirmDeleteOrder) {
            deleteWholeOrder(saleId);
        }
        return;
    }

    if (!confirm('هل أنت متأكد من حذف هذا المنتج؟')) return;

    const qty = parseFloat(row.dataset.serverQty) || 0;
    const price = parseFloat(row.dataset.serverPrice) || 0;
    const removedAmount = qty * price;

    const currentTotal = parseFloat(document.getElementById('order-total-price').value) || 0;
    let updatedTotal = currentTotal - removedAmount;
    if (updatedTotal < 0) updatedTotal = 0;

    try {
        const response = await fetch(`${API_BASE_URL}/order-items/${saleItemId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'تعذر الحذف من قاعدة البيانات.');
        }

        await updateOrderTotalOnServer(saleId, updatedTotal);

        alert('تم حذف المنتج وطرح قيمته من السعر الإجمالي بنجاح!');
        loadOrderToEdit(saleId);
        loadOrdersTable();
    } catch (error) {
        alert(`خطأ أثناء الحذف: ${error.message}`);
    }
}

// PATCH (Order Metadata): الحفظ الكلي والنهائي للفاتورة
async function handleOrderUpdate(e) {
    e.preventDefault();

    const saleId = document.getElementById('edit-sale-id').value;
    const customerName = document.getElementById('customer-name').value.trim();
    const totalPrice = parseFloat(document.getElementById('order-total-price').value) || 0;

    const payload = {
        customer_name: customerName,
        total_price: totalPrice
    };

    try {
        const response = await fetch(`${API_BASE_URL}/orders/${saleId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'رفض السيرفر تعديل الفاتورة.');
        }

        alert('تم حفظ بيانات الفاتورة وتثبيت السعر الإجمالي بنجاح!');
        closeEditState();
        loadOrdersTable();
    } catch (error) {
        alert(`فشل التحديث: ${error.message}`);
    }
}

// 🌐 DELETE: حذف الفاتورة كاملة (تم إضافة نافذة تأكيد قبل الحذف لحماية البيانات)
async function deleteWholeOrder(saleId) {
    // ✋ خطوة التأكيد الجديدة:
    const userConfirmed = confirm(`⚠️ تنبيه هائل:\n\nهل أنت متأكد تماماً من رغبتك في حذف الفاتورة رقم #${saleId} بشكل نهائي ومسح جميع منتجاتها وسجلاتها من النظام؟\n\nلا يمكن التراجع عن هذه العملية لاحقاً.`);
    
    // إذا ضغط المستخدم على Cancel، نوقف الدالة فوراً ولا يتم مسح شيء
    if (!userConfirmed) {
        console.log("تم إلغاء عملية حذف الفاتورة من قبل المستخدم.");
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/orders/${saleId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'فشل حذف الفاتورة.');
        }

        alert('تم حذف الفاتورة كاملة بنجاح من قاعدة البيانات.');
        closeEditState();
        loadOrdersTable();
    } catch (error) {
        alert(`خطأ: ${error.message}`);
    }
}

// إغلاق اللوحة
function closeEditState() {
    const editCard = document.getElementById('edit-order-card');
    if (editCard) editCard.classList.add('hidden');
    
    const form = document.getElementById('order-metadata-form');
    if (form) form.reset();
    
    document.getElementById('edit-sale-id').value = '';
    document.getElementById('order-items-container').innerHTML = '';
}