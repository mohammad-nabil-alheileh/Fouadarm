const API_BASE_URL = 'http://127.0.0.1:5000';

document.addEventListener('DOMContentLoaded', () => {
    console.log("Products JS synchronized with FastAPI Router definitions.");
    
    const productForm = document.getElementById('product-form');
    if (productForm) {
        productForm.addEventListener('submit', handleProductSubmit);
    }

    loadProductsTable();
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

async function loadProductsTable() {
    const tbody = document.querySelector('#products-table tbody');
    if (!tbody) return;

    try {
        const response = await fetch(`${API_BASE_URL}/products`);
        if (!response.ok) throw new Error('Could not fetch records from database.');
        
        const products = await response.json();
        tbody.innerHTML = '';

        if (products.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">لا توجد بضائع مسجلة حالياً في النظام.</td></tr>`;
            return;
        }

        products.forEach(product => {
            const id = product.product_id !== undefined ? product.product_id : product.id;
            const tr = document.createElement('tr');

            tr.innerHTML = `
                <td><code>#${id}</code></td>
                <td><strong>${product.product_name}</strong></td>
                <td>${product.total_count} وحدة متاح</td>
                <td>${parseFloat(product.unit_price).toFixed(2)} JD</td>
                <td class="td-actions">
                    <button class="btn-secondary btn-edit" type="button" id="edit-btn-${id}">تعديل البيانات</button>
                    <button class="btn-danger btn-delete-item" type="button" onclick="deleteProductRecord(${id})">حذف</button>
                </td>
            `;
            tbody.appendChild(tr);

            document.getElementById(`edit-btn-${id}`).addEventListener('click', () => {
                setupEditState(product);
            });
        });
    } catch (err) {
        console.error("Fetch inventory error:", err);
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--danger-color);">❌ فشل جلب المنتجات. يرجى التأكد من تشغيل الـ Backend والـ CORS.</td></tr>`;
    }
}

async function handleProductSubmit(e) {
    e.preventDefault(); 

    const productId = document.getElementById('edit-product-id').value;
    const productName = document.getElementById('product-name').value.trim();
    const totalCount = parseInt(document.getElementById('total-count').value);
    const unitPrice = parseFloat(document.getElementById('unit-price').value);

    if (!productName || isNaN(totalCount) || isNaN(unitPrice)) {
        alert("يرجى ملء جميع الحقول بشكل صحيح.");
        return;
    }

    const payload = {
        product_name: productName,
        total_count: totalCount,
        unit_price: unitPrice
    };

    let url = `${API_BASE_URL}/products`;
    let method = 'POST';

    if (productId) {
        url = `${API_BASE_URL}/products/${productId}`;
        method = 'PATCH'; 
    }

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorDetails = await response.json();
            throw new Error(errorDetails.detail || 'الخادم رفض معالجة المعاملة.');
        }

        if (response.status !== 204) {
            await response.json();
        }

        alert(productId ? 'تم تحديث مواصفات الصنف بنجاح!' : 'تم تسجيل المنتج الجديد في النظام بنجاح!');
        clearFormState();
        loadProductsTable();
    } catch (error) {
        console.error("Database mutation failure:", error);
        alert(`فشلت العملية: ${error.message}`);
    }
}

function setupEditState(product) {
    const id = product.product_id !== undefined ? product.product_id : product.id;
    
    document.getElementById('edit-product-id').value = id;
    document.getElementById('product-name').value = product.product_name;
    document.getElementById('total-count').value = product.total_count;
    document.getElementById('unit-price').value = product.unit_price;

    document.getElementById('form-title').textContent = `✏️ تعديل بيانات المنتج رقم #${id}`;
    document.getElementById('submit-btn').textContent = 'تطبيق التحديثات الحالية';
    document.getElementById('cancel-btn').classList.remove('hidden');
    document.getElementById('product-name').focus();
}

function clearFormState() {
    document.getElementById('edit-product-id').value = '';
    document.getElementById('product-form').reset();
    
    document.getElementById('form-title').textContent = 'إضافة منتج جديد لشركاء العمل';
    document.getElementById('submit-btn').textContent = 'حفظ بيانات المنتج';
    document.getElementById('cancel-btn').classList.add('hidden');
}

async function deleteProductRecord(id) {
    if (!confirm(`هل أنت متأكد من رغبتك بحذف المنتج رقم #${id} نهائياً؟ لا يمكن التراجع عن هذا الإجراء.`)) return;

    try {
        const response = await fetch(`${API_BASE_URL}/products/${id}`, { method: 'DELETE' });
        
        if (!response.ok) {
            const errorDetails = await response.json();
            throw new Error(errorDetails.detail || 'خطأ متعلق ببيانات الفواتير المرتبطة.');
        }
        
        alert('تم مسح وإزالة سجل المنتج بنجاح.');
        loadProductsTable();
    } catch (error) {
        console.error(error);
        alert(`تعذر حذف الصنف: ${error.message}`);
    }
}