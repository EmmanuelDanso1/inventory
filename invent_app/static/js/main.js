/**
 * Inventory Management System - Main JavaScript
 * 
 * Features:
 * - Navigation & UI interactions
 * - Form validation & AJAX submissions
 * - Table search & filtering
 * - Notifications & alerts
 * - API helpers
 * - Export & print functionality
 * - Stock status indicators
 */

'use strict';

// INITIALIZATION
document.addEventListener('DOMContentLoaded', function() {
    initNavigation();
    initFlashMessages();
    initTabs();
    initDeleteButtons();
    initFormFocus();
    initTooltips();
    
    console.log('%c📦 Inventory Management System', 'color: #4299e1; font-size: 20px; font-weight: bold;');
    console.log('%cDatabase Performance Testing Project', 'color: #718096; font-size: 12px;');
});


// NAVIGATION
function initNavigation() {
    // Highlight active navigation link based on current URL
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        }
    });
}


// FLASH MESSAGES
function initFlashMessages() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Auto-hide after 5 seconds
        setTimeout(() => {
            fadeOutElement(alert);
        }, 5000);
    });
}

function fadeOutElement(element) {
    element.style.transition = 'opacity 0.5s ease';
    element.style.opacity = '0';
    setTimeout(() => element.remove(), 500);
}


// TABS
function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', function() {
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Filter table if data-type attribute exists
            const filterType = this.getAttribute('data-type');
            if (filterType) {
                filterTableByType(filterType);
            }
        });
    });
}

function filterTableByType(type) {
    const rows = document.querySelectorAll('table tbody tr[data-type]');
    rows.forEach(row => {
        const rowType = row.getAttribute('data-type');
        row.style.display = (type === 'all' || rowType === type) ? '' : 'none';
    });
}


// DELETE CONFIRMATION
function initDeleteButtons() {
    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', function(e) {
            const itemName = this.getAttribute('data-item-name') || 'this item';
            if (!confirmDelete(itemName)) {
                e.preventDefault();
            }
        });
    });
}

function confirmDelete(itemName = 'this item') {
    return confirm(`Are you sure you want to delete "${itemName}"? This action cannot be undone.`);
}


// FORM HANDLING
function initFormFocus() {
    // Auto-focus first input in forms
    const firstInput = document.querySelector('form input:not([type="hidden"]):not([readonly]):first-of-type');
    if (firstInput) {
        firstInput.focus();
    }
}

function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.style.borderColor = '#e53e3e';
            input.classList.add('is-invalid');
        } else {
            input.style.borderColor = '#e2e8f0';
            input.classList.remove('is-invalid');
        }
    });
    
    if (!isValid) {
        showNotification('Please fill in all required fields.', 'danger');
    }
    
    return isValid;
}


// AJAX FORM SUBMISSION
async function submitFormAjax(formId, url, method = 'POST') {
    const form = document.getElementById(formId);
    if (!form) {
        console.error('Form not found:', formId);
        return null;
    }
    
    const formData = new FormData(form);
    showLoading();
    
    try {
        const response = await fetch(url || form.action, {
            method: method || form.method,
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        hideLoading();
        
        if (response.ok) {
            const data = await response.json();
            showNotification(data.message || 'Success!', 'success');
            return data;
        } else {
            const errorData = await response.json().catch(() => ({}));
            showNotification(errorData.message || 'An error occurred', 'danger');
            return null;
        }
    } catch (error) {
        hideLoading();
        console.error('Error:', error);
        showNotification('Network error. Please try again.', 'danger');
        return null;
    }
}


// TABLE SEARCH
function searchTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!input || !table) return;
    
    const filter = input.value.toLowerCase();
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 1; i < rows.length; i++) {
        let found = false;
        const cells = rows[i].getElementsByTagName('td');
        
        for (let j = 0; j < cells.length; j++) {
            if (cells[j].textContent.toLowerCase().includes(filter)) {
                found = true;
                break;
            }
        }
        
        rows[i].style.display = found ? '' : 'none';
    }
}

// Debounced search for better performance
const debouncedSearch = debounce(searchTable, 300);

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


// FORMATTING UTILITIES
function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '$0.00';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatNumber(number) {
    if (number === null || number === undefined) return '0';
    return new Intl.NumberFormat('en-US').format(number);
}

function formatDate(dateString, includeTime = true) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };
    
    if (includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
    }
    
    return new Intl.DateTimeFormat('en-US', options).format(date);
}


// STOCK STATUS HELPERS
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

function updateStockStatus(stock, reorderLevel) {
    return {
        class: getStockStatusClass(stock, reorderLevel),
        text: getStockStatusText(stock, reorderLevel)
    };
}


// NOTIFICATION SYSTEM
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        min-width: 300px;
        animation: slideInRight 0.3s ease;
    `;
    notification.innerHTML = `
        ${message}
        <button class="close-btn" onclick="this.parentElement.remove()">×</button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.transition = 'opacity 0.3s ease';
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Add slide-in animation
if (!document.getElementById('notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
}


// LOADING SPINNER
function showLoading() {
    if (document.getElementById('loading-spinner')) return;
    
    const loader = document.createElement('div');
    loader.id = 'loading-spinner';
    loader.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                    background: rgba(0, 0, 0, 0.5); z-index: 9999; 
                    display: flex; align-items: center; justify-content: center;">
            <div style="background: white; padding: 30px; border-radius: 10px; 
                        text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                <div class="spinner"></div>
                <p style="margin-top: 15px; color: #2d3748; font-weight: 500;">Loading...</p>
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

// Add spinner animation styles
if (!document.getElementById('spinner-styles')) {
    const style = document.createElement('style');
    style.id = 'spinner-styles';
    style.textContent = `
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #4299e1;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}


// EXPORT & PRINT
function exportTableToCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) {
        showNotification('Table not found', 'danger');
        return;
    }
    
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = Array.from(cols).map(col => {
            // Clean text and escape commas
            let text = col.textContent.trim().replace(/"/g, '""');
            return text.includes(',') ? `"${text}"` : text;
        });
        csv.push(rowData.join(','));
    });
    
    // Create and download CSV file
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (navigator.msSaveBlob) { // IE 10+
        navigator.msSaveBlob(blob, filename);
    } else {
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    showNotification('Table exported successfully!', 'success');
}

function printPage() {
    window.print();
}


// CLIPBOARD
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Failed to copy:', err);
            showNotification('Failed to copy to clipboard', 'danger');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.select();
        
        try {
            document.execCommand('copy');
            showNotification('Copied to clipboard!', 'success');
        } catch (err) {
            showNotification('Failed to copy to clipboard', 'danger');
        }
        
        document.body.removeChild(textArea);
    }
}


// LOCAL STORAGE HELPERS
const Storage = {
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error saving to localStorage:', error);
            return false;
        }
    },
    
    get: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return defaultValue;
        }
    },
    
    remove: function(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error removing from localStorage:', error);
            return false;
        }
    },
    
    clear: function() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Error clearing localStorage:', error);
            return false;
        }
    }
};


// API HELPERS
const API = {
    async request(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },
    
    getItem: async function(itemId) {
        return await this.request(`/api/items/${itemId}`);
    },
    
    getItems: async function() {
        return await this.request('/api/items');
    },
    
    getSupplier: async function(supplierId) {
        return await this.request(`/api/suppliers/${supplierId}`);
    },
    
    getTransaction: async function(transactionId) {
        return await this.request(`/api/transactions/${transactionId}`);
    },
    
    getStats: async function() {
        return await this.request('/api/stats');
    }
};


// TOOLTIPS
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'custom-tooltip';
            tooltip.textContent = this.getAttribute('data-tooltip');
            tooltip.style.cssText = `
                position: fixed;
                background: #2d3748;
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 13px;
                z-index: 10000;
                pointer-events: none;
                white-space: nowrap;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            `;
            document.body.appendChild(tooltip);
            
            // Position tooltip
            const rect = this.getBoundingClientRect();
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 8) + 'px';
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
}


// UTILITY FUNCTIONS
function isEmpty(value) {
    return value === null || value === undefined || value === '';
}

function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function truncate(str, length = 50) {
    if (!str) return '';
    return str.length > length ? str.substring(0, length) + '...' : str;
}


// EXPORT FUNCTIONS TO GLOBAL SCOPE
window.searchTable = searchTable;
window.debouncedSearch = debouncedSearch;
window.confirmDelete = confirmDelete;
window.validateForm = validateForm;
window.submitFormAjax = submitFormAjax;
window.formatCurrency = formatCurrency;
window.formatNumber = formatNumber;
window.formatDate = formatDate;
window.getStockStatusClass = getStockStatusClass;
window.getStockStatusText = getStockStatusText;
window.updateStockStatus = updateStockStatus;
window.showNotification = showNotification;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.exportTableToCSV = exportTableToCSV;
window.printPage = printPage;
window.copyToClipboard = copyToClipboard;
window.Storage = Storage;
window.API = API;
window.isEmpty = isEmpty;
window.isValidEmail = isValidEmail;
window.truncate = truncate;