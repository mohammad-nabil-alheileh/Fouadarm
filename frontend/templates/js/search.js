document.addEventListener('DOMContentLoaded', () => {
    
    // --- New: Date Validation Guard ---
    const fromDateInput = document.getElementById('from_date');
    const toDateInput = document.getElementById('to_date');

    if (fromDateInput && toDateInput) {
        // When 'From Date' changes, 'To Date' cannot be earlier than it
        fromDateInput.addEventListener('change', () => {
            toDateInput.min = fromDateInput.value;
        });

        // When 'To Date' changes, 'From Date' cannot be later than it
        toDateInput.addEventListener('change', () => {
            fromDateInput.max = toDateInput.value;
        });
    }

    // 1. Pinpoint Active Menu Fix
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

    // 2. Name Search Form Submission
    const nameSearchForm = document.querySelector('form[action="/search_by_name"]');
    if (nameSearchForm) {
        nameSearchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const customerName = this.querySelector('input[name="name"]').value.trim();
            if (customerName) {
                window.location.href = `/results_name.html?name=${encodeURIComponent(customerName)}`;
            }
        });
    }

// 3. FIXED: Date Range Search Form Submission (Robust Version)
const dateRangeForm = document.getElementById('date-search-form');
if (dateRangeForm) {
    // Find both buttons explicitly
    const dateBtn = dateRangeForm.querySelector('[data-target="date"]');
    const productsBtn = dateRangeForm.querySelector('[data-target="products"]');

    const handleSearch = (targetType) => {
        const fromDate = dateRangeForm.querySelector('input[name="from_date"]').value;
        const toDate = dateRangeForm.querySelector('input[name="to_date"]').value;

        // Trigger native HTML5 validation UI if fields are empty
        if (!fromDate || !toDate) {
            dateRangeForm.reportValidity();
            return;
        }

        if (targetType === 'date') {
            window.location.href = `/results_date.html?from=${fromDate}&to=${toDate}`;
        } else if (targetType === 'products') {
            window.location.href = `/results_products.html?from=${fromDate}&to=${toDate}`;
        }
    };

    // Listen for direct clicks on the buttons
    dateBtn.addEventListener('click', (e) => {
        e.preventDefault();
        handleSearch('date');
    });

    productsBtn.addEventListener('click', (e) => {
        e.preventDefault();
        handleSearch('products');
    });

    // Optional: Handle what happens if they press "Enter" inside an input field
    dateRangeForm.addEventListener('submit', (e) => {
        e.preventDefault(); 
        // Default to products or date search here if desired
    });
}});