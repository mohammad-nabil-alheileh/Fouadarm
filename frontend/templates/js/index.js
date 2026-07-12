const API_BASE_URL = 'http://127.0.0.1:5000'; // Set to your custom Port 5000 setup

document.addEventListener('DOMContentLoaded', () => {
    const saleDateInput = document.getElementById('sale_date');
    if (saleDateInput) {
        saleDateInput.valueAsDate = new Date();
    }
    loadProductsFromDB();
});

// --- Pinpoint Active Menu Fix ---
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
// --------------------------------

// جلب المنتجات من قاعدة البيانات لتغذية القوائم المنسدلة
async function loadProductsFromDB() {
    try {
        const response = await fetch(`${API_BASE_URL}/products`);
        
        if (!response.ok) {
            throw new Error(`خادم المشتل أعاد استجابة خاطئة: ${response.status}`);
        }
        
        const products = await response.json();
        console.log("المنتجات القادمة من قاعدة البيانات:", products);
        
        window.dbProductsList = products;

        const firstSelect = document.querySelector('.product_type');
        if (firstSelect) {
            populateDropdown(firstSelect, products);
        }
        
    } catch (error) {
        console.error('تفاصيل الخطأ في الاتصال:', error);
        alert('حدث خطأ أثناء الاتصال بقاعدة البيانات لجلب المنتجات. يرجى التأكد من تشغيل الـ Backend وتفعيل الـ CORS.');
    }
}

// تعبئة القائمة المنسدلة بالخيارات وتفعيل أحداث التغيير
function populateDropdown(selectElement, products) {
    selectElement.innerHTML = ''; 
    
    if (!products || products.length === 0) {
        selectElement.innerHTML = `<option value="">لا توجد منتجات في قاعدة البيانات</option>`;
        return;
    }

    products.forEach(product => {
        const option = document.createElement('option');
        const pId = product.product_id !== undefined ? product.product_id : product.id;
        
        option.value = pId; 
        option.textContent = `${product.product_name} (${product.unit_price} JD) [المخزون: ${product.total_count}]`;
        option.dataset.price = product.unit_price;
        selectElement.appendChild(option);
    });

    selectElement.addEventListener('change', () => {
        const row = selectElement.closest('.product-row');
        handleProductSelection(row);
    });

    const row = selectElement.closest('.product-row');
    if (row) {
        const totalPriceInput = row.querySelector('.total_price');
        if (totalPriceInput) {
            totalPriceInput.removeAttribute('readonly'); 
            totalPriceInput.addEventListener('input', () => calculateUnitPriceFromTotal(totalPriceInput));
        }
    }

    handleProductSelection(selectElement.closest('.product-row'));
}

function handleProductSelection(row) {
    if (!row) return;
    const select = row.querySelector('.product_type');
    if (!select || select.selectedIndex === -1) return;
    
    const selectedOption = select.options[select.selectedIndex];
    const unitPriceInput = row.querySelector('.unit_price');
    
    if (selectedOption && selectedOption.dataset.price) {
        unitPriceInput.value = parseFloat(selectedOption.dataset.price).toFixed(2);
        calculateRowTotal(unitPriceInput);
    }
}

function calculateRowTotal(inputElement) {
    const row = inputElement.closest('.product-row');
    const quantity = parseFloat(row.querySelector('.quantity').value) || 0;
    const unitPrice = parseFloat(row.querySelector('.unit_price').value) || 0;
    
    const totalPriceInput = row.querySelector('.total_price');
    totalPriceInput.value = (quantity * unitPrice).toFixed(2);
    
    calculateGrandTotal();
}

function calculateUnitPriceFromTotal(totalPriceInputElement) {
    const row = totalPriceInputElement.closest('.product-row');
    const quantity = parseFloat(row.querySelector('.quantity').value) || 0;
    const totalPrice = parseFloat(totalPriceInputElement.value) || 0;
    const unitPriceInput = row.querySelector('.unit_price');

    if (quantity > 0) {
        unitPriceInput.value = (totalPrice / quantity).toFixed(2);
    } else {
        unitPriceInput.value = '0.00';
    }

    calculateGrandTotal();
}

function calculateGrandTotal() {
    let grandTotal = 0;
    document.querySelectorAll('.total_price').forEach(input => {
        grandTotal += parseFloat(input.value) || 0;
    });
    
    const grandTotalContainer = document.getElementById('grand_total');
    if (grandTotalContainer) {
        grandTotalContainer.innerText = `${grandTotal.toFixed(2)} JD`;
    }
}

function addProductRow() {
    const container = document.getElementById('products_container');
    const rows = container.querySelectorAll('.product-row');
    if (rows.length === 0) return;

    const newRow = rows[0].cloneNode(true);
    
    newRow.querySelector('.quantity').value = '';
    newRow.querySelector('.unit_price').value = '0.00';
    
    const totalPriceInput = newRow.querySelector('.total_price');
    totalPriceInput.value = '0.00';
    totalPriceInput.removeAttribute('readonly'); 
    totalPriceInput.addEventListener('input', () => calculateUnitPriceFromTotal(totalPriceInput));
    
    const newSelect = newRow.querySelector('.product_type');
    if (window.dbProductsList) {
        populateDropdown(newSelect, window.dbProductsList);
    }

    container.appendChild(newRow);
}

function removeRow(buttonElement) {
    const container = document.getElementById('products_container');
    if (container.querySelectorAll('.product-row').length > 1) {
        buttonElement.closest('.product-row').remove();
        calculateGrandTotal();
    } else {
        alert('يجب أن تحتوي الفاتورة على منتج واحد على الأقل!');
    }
}

function normalizeCustomerName(name) {
    if (!name) return "";
    let cleanName = name.toLowerCase().trim();
    cleanName = cleanName
        .replace(/[\u064B-\u0652]/g, "") 
        .replace(/[أإآ]/g, "ا")          
        .replace(/ة\b/g, "ه")            
        .replace(/ى\b/g, "ي");           
    return cleanName;
}

// حفظ الفاتورة وإرسال البيانات للـ Backend
async function saveData() {
    const rawCustomerName = document.getElementById('customer_name').value;
    const customerName = normalizeCustomerName(rawCustomerName);

    const grandTotalText = document.getElementById('grand_total').innerText;
    const totalPrice = parseFloat(grandTotalText) || 0;

    // 🕒 FIXED: Extract chosen date from input element
    const saleDateInput = document.getElementById('sale_date');
    const saleDate = saleDateInput ? saleDateInput.value : "";

    if (!customerName) {
        alert('الرجاء إدخال اسم العميل أولاً');
        return;
    }

    if (!saleDate) {
        alert('الرجاء اختيار تاريخ الفاتورة');
        return;
    }

    const items = [];
    let isFormValid = true;

    document.querySelectorAll('.product-row').forEach(row => {
        const select = row.querySelector('.product_type');
        if(!select.value) {
            isFormValid = false;
            return;
        }
        const productId = parseInt(select.value);
        const quantity = parseInt(row.querySelector('.quantity').value) || 0;
        const customUnitPrice = parseFloat(row.querySelector('.unit_price').value) || 0;

        if (!productId || quantity <= 0) {
            isFormValid = false;
            return;
        }

        items.push({
            product_id: productId,
            quantity: quantity,
            unit_price: customUnitPrice 
        });
    });

    if (!isFormValid || items.length === 0) {
        alert('الرجاء التأكد من اختيار المنتجات وتحديد كميات صالحة لجميع الأسطر.');
        return;
    }

    // 📦 FIXED: Added 'sale_date' to payload body object
    const payload = {
        customer_name: customerName, 
        total_price: totalPrice,
        sale_date: saleDate, // Send custom selected date down to database schema
        items: items
    };

    console.log("Sending payload with explicit sale_date out to backend:", payload);

    try {
        const response = await fetch(`${API_BASE_URL}/orders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.status === 201) {
            const newOrderId = await response.json();
            alert(`تم حفظ الفاتورة بنجاح! رقم الفاتورة: ${newOrderId}`);
            window.location.reload();
        } else {
            const errorData = await response.json();
            alert(`فشل الحفظ: ${errorData.detail || 'خطأ في معالجة البيانات'}`);
        }
    } catch (error) {
        console.error('Error during fetch submission:', error);
        alert('فشل الاتصال بالخادم أثناء محاولة حفظ الفاتورة.');
    }
}