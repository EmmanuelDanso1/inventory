/**
 * Chart.js Helper Functions
 * Inventory Management System
 * 
 * Requires Chart.js to be loaded before this file
 */

'use strict';

// Default chart colors
const chartColors = {
    primary: '#4299e1',
    success: '#48bb78',
    warning: '#ed8936',
    danger: '#f56565',
    info: '#4299e1',
    secondary: '#718096'
};

// STOCK MOVEMENT CHART (Line Chart)
/**
 * Create a line chart showing stock in/out movements
 * @param {string} canvasId - Canvas element ID
 * @param {Array} labels - Date labels for x-axis
 * @param {Array} stockInData - Stock in quantities
 * @param {Array} stockOutData - Stock out quantities
 * @returns {Chart} Chart.js instance
 */
function createStockMovementChart(canvasId, labels, stockInData, stockOutData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error('Canvas element not found:', canvasId);
        return null;
    }
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Stock In',
                data: stockInData,
                borderColor: chartColors.success,
                backgroundColor: 'rgba(72, 187, 120, 0.1)',
                tension: 0.4,
                fill: true,
                borderWidth: 2
            }, {
                label: 'Stock Out',
                data: stockOutData,
                borderColor: chartColors.warning,
                backgroundColor: 'rgba(237, 137, 54, 0.1)',
                tension: 0.4,
                fill: true,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#4299e1',
                    borderWidth: 1
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        color: '#718096'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        color: '#718096'
                    },
                    grid: {
                        display: false
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}


// CATEGORY DISTRIBUTION CHART (Bar Chart)
/**
 * Create a bar chart showing items per category
 * @param {string} canvasId - Canvas element ID
 * @param {Array} categories - Category names
 * @param {Array} counts - Item counts per category
 * @returns {Chart} Chart.js instance
 */
function createCategoryChart(canvasId, categories, counts) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error('Canvas element not found:', canvasId);
        return null;
    }
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [{
                label: 'Items per Category',
                data: counts,
                backgroundColor: chartColors.primary,
                borderColor: chartColors.primary,
                borderWidth: 1,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        color: '#718096'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        color: '#718096'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}


// STOCK STATUS CHART (Doughnut Chart)
/**
 * Create a doughnut chart showing stock status distribution
 * @param {string} canvasId - Canvas element ID
 * @param {number} inStock - Number of in-stock items
 * @param {number} lowStock - Number of low-stock items
 * @param {number} outOfStock - Number of out-of-stock items
 * @returns {Chart} Chart.js instance
 */
function createStockStatusChart(canvasId, inStock, lowStock, outOfStock) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error('Canvas element not found:', canvasId);
        return null;
    }
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['In Stock', 'Low Stock', 'Out of Stock'],
            datasets: [{
                data: [inStock, lowStock, outOfStock],
                backgroundColor: [
                    chartColors.success,
                    chartColors.warning,
                    chartColors.danger
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}


// SUPPLIER PERFORMANCE CHART (Horizontal Bar)
/**
 * Create a horizontal bar chart for supplier comparison
 * @param {string} canvasId - Canvas element ID
 * @param {Array} suppliers - Supplier names
 * @param {Array} values - Values to compare (e.g., total items supplied)
 * @returns {Chart} Chart.js instance
 */
function createSupplierChart(canvasId, suppliers, values) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error('Canvas element not found:', canvasId);
        return null;
    }
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: suppliers,
            datasets: [{
                label: 'Items Supplied',
                data: values,
                backgroundColor: chartColors.info,
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y', // Horizontal bars
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}


// TRANSACTION TREND CHART (Area Chart)
/**
 * Create an area chart for transaction trends
 * @param {string} canvasId - Canvas element ID
 * @param {Array} labels - Date labels
 * @param {Array} data - Transaction counts
 * @returns {Chart} Chart.js instance
 */
function createTransactionTrendChart(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error('Canvas element not found:', canvasId);
        return null;
    }
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Transactions',
                data: data,
                borderColor: chartColors.primary,
                backgroundColor: 'rgba(66, 153, 225, 0.2)',
                tension: 0.4,
                fill: true,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}


// UTILITY FUNCTIONS

/**
 * Destroy a chart instance if it exists
 * @param {Chart} chartInstance - Chart.js instance
 */
function destroyChart(chartInstance) {
    if (chartInstance && typeof chartInstance.destroy === 'function') {
        chartInstance.destroy();
    }
}

/**
 * Update chart data dynamically
 * @param {Chart} chartInstance - Chart.js instance
 * @param {Array} newLabels - New labels
 * @param {Array} newData - New data
 */
function updateChartData(chartInstance, newLabels, newData) {
    if (chartInstance) {
        chartInstance.data.labels = newLabels;
        chartInstance.data.datasets[0].data = newData;
        chartInstance.update();
    }
}


// EXPORT FUNCTIONS
window.createStockMovementChart = createStockMovementChart;
window.createCategoryChart = createCategoryChart;
window.createStockStatusChart = createStockStatusChart;
window.createSupplierChart = createSupplierChart;
window.createTransactionTrendChart = createTransactionTrendChart;
window.destroyChart = destroyChart;
window.updateChartData = updateChartData;
window.chartColors = chartColors;