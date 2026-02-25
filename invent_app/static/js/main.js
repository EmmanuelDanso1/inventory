/**
 * Main JavaScript for Inventory Management System
 */

// ============================================
// Navigation Active State
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    // Set active nav link based on current URL
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});


// ============================================
// Flash Message Auto-Close
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        }, 5000); // Auto-close after 5 seconds
    });
});


// ============================================
// Confirm Delete Actions
// ============================================
function confirmDelete(itemName, url) {
    if (confirm(`Are you sure you want to delete "${itemName}"? This action cannot be undone.`)) {
        window.location.href = url;
    }
}


// ============================================
// Table Search Functionality
// ============================================
function searchTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toLowerCase();
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tr');

    for (let i = 1; i < rows.length; i++) {
        let found = false;
        const cells = rows[i].getElementsByTagName('td');
        
        for (let j = 0; j < cells.length; j++) {
            if (cells[j].textContent.toLowerCase().indexOf(filter) > -1) {
                found = true;
                break;
            }
        }
        
        rows[i].style.display = found ? '' : 'none';
    }
}


// ============================================
// Form Validation
// ============================================
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = '#e53e3e';
            isValid = false;
        } else {
            input.style.borderColor = '#e2e8f0';
        }
    });

    if (!isValid) {
        alert('Please fill in all required fields.');
    }

    return isValid;
}


// ============================================
// Number Formatting
// ============================================
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatNumber(number) {
    return new Intl.NumberFormat('en-US').format(number);
}


// ============================================
// Date Formatting
// ============================================
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}


// ============================================
// Export Table to CSV
// ============================================
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tr');
    let csv = [];

    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = Array.from(cols).map(col => {
            // Remove any HTML tags and clean the text
            return col.textContent.replace(/,/g, '').trim();
        });
        csv.push(rowData.join(','));
    });

    // Create CSV file
    const csvFile = new Blob([csv.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename || 'export.csv';
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}


// ============================================
// Print Page
// ============================================
function printPage() {
    window.print();
}


// ============================================
// Loading Spinner
// ============================================
function showLoading() {
    const loader = document.createElement('div');
    loader.id = 'loading-spinner';
    loader.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                    background: rgba(0,0,0,0.5); z-index: 9999; display: flex; 
                    align-items: center; justify-content: center;">
            <div style="background: white; padding: 30px; border-radius: 10px; text-align: center;">
                <div style="border: 4px solid #f3f3f3; border-top: 4px solid #4299e1; 
                            border-radius: 50%; width: 40px; height: 40px; 
                            animation: spin 1s linear infinite; margin: 0 auto 15px;"></div>
                <p>Loading...</p>
            </div>
        </div>
    `;
    document.body.appendChild(loader);
}

function hideLoading() {
    const loader = document.getElementById('loading-spinner');
    if (loader) {
        loader.remove();
    }
}

// CSS animation for spinner
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);


// ============================================
// AJAX Form Submission
// ============================================
function submitFormAjax(formId, successCallback) {
    const form = document.getElementById(formId);
    const formData = new FormData(form);

    showLoading();

    fetch(form.action, {
        method: form.method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            if (successCallback) {
                successCallback(data);
            } else {
                window.location.reload();
            }
        } else {
            alert(data.message || 'An error occurred');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    });
}


// ============================================
// Stock Level Color Coding
// ============================================
function getStockStatusClass(currentStock, reorderLevel) {
    if (currentStock === 0) {
        return 'badge-danger';
    } else if (currentStock <= reorderLevel) {
        return 'badge-warning';
    } else {
        return 'badge-success';
    }
}

function getStockStatusText(currentStock, reorderLevel) {
    if (currentStock === 0) {
        return 'Out of Stock';
    } else if (currentStock <= reorderLevel) {
        return 'Low Stock';
    } else {
        return 'In Stock';
    }
}


// ============================================
// Debounce Function (for search inputs)
// ============================================
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}


// ============================================
// API Helper Functions
// ============================================
const API = {
    // Get item details
    getItem: async function(itemId) {
        try {
            const response = await fetch(`/api/items/${itemId}`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching item:', error);
            return null;
        }
    },

    // Get supplier details
    getSupplier: async function(supplierId) {
        try {
            const response = await fetch(`/api/suppliers/${supplierId}`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching supplier:', error);
            return null;
        }
    },

    // Get transaction details
    getTransaction: async function(transactionId) {
        try {
            const response = await fetch(`/api/transactions/${transactionId}`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching transaction:', error);
            return null;
        }
    }
};


// ============================================
// Notification System
// ============================================
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 10000; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button class="close-btn" onclick="this.parentElement.remove()">×</button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}


// ============================================
// Local Storage Helpers
// ============================================
const Storage = {
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Error saving to localStorage:', error);
        }
    },

    get: function(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return null;
        }
    },

    remove: function(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('Error removing from localStorage:', error);
        }
    }
};


// ============================================
// Initialize Tooltips (if using)
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.getAttribute('data-tooltip');
            tooltip.style.cssText = `
                position: absolute;
                background: #2d3748;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 10000;
            `;
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
            tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
            
            this._tooltip = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                this._tooltip = null;
            }
        });
    });
});


// ============================================
// Console Welcome Message
// ============================================
console.log('%c📦 Inventory Management System', 'color: #4299e1; font-size: 20px; font-weight: bold;');
console.log('%cDatabase Performance Testing Project', 'color: #718096; font-size: 12px;');
console.log('%cFlask + SQLAlchemy + PostgreSQL', 'color: #48bb78; font-size: 12px;');