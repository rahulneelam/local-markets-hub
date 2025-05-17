/**
 * Main JavaScript file for Marketplace Platform
 * Contains shared functionality used across the site
 */

// Helper function to format dates
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', options);
}

// Helper function to format prices
function formatPrice(price) {
    return parseFloat(price).toFixed(2);
}

// Table search functionality
function setupTableSearch(inputId, tableId, columns = [0]) {
    const searchInput = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!searchInput || !table) return;
    
    searchInput.addEventListener('keyup', function() {
        const searchTerm = this.value.toLowerCase();
        const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
        
        for (let i = 0; i < rows.length; i++) {
            let found = false;
            
            for (const colIndex of columns) {
                const cell = rows[i].getElementsByTagName('td')[colIndex];
                if (cell) {
                    const textValue = cell.textContent || cell.innerText;
                    if (textValue.toLowerCase().indexOf(searchTerm) > -1) {
                        found = true;
                        break;
                    }
                }
            }
            
            rows[i].style.display = found ? '' : 'none';
        }
    });
}

// Confirmation dialog
function confirmAction(message, callback) {
    if (window.confirm(message)) {
        callback();
    }
}

// Shopping Cart Functions
function addToCart(productId, name, price, quantity = 1, shopId) {
    // Get existing cart from session storage or create a new one
    let cart = JSON.parse(sessionStorage.getItem('cart')) || { items: [], total: 0 };
    
    // Check if we're adding from a different shop - this requires clearing the cart
    if (cart.items.length > 0 && cart.shopId && cart.shopId !== shopId) {
        if (!window.confirm("Your cart contains items from another shop. Would you like to clear your cart and add this item?")) {
            return false;
        }
        cart = { items: [], total: 0 };
    }
    
    // Set the shop ID for this cart
    cart.shopId = shopId;
    
    // Check if item already exists in cart
    const existingItemIndex = cart.items.findIndex(item => item.product_id === productId);
    
    if (existingItemIndex > -1) {
        // Update existing item
        cart.items[existingItemIndex].quantity += quantity;
    } else {
        // Add new item
        cart.items.push({
            product_id: productId,
            name: name,
            price: parseFloat(price),
            quantity: quantity
        });
    }
    
    // Update cart total
    cart.total = cart.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    
    // Save cart to session storage
    sessionStorage.setItem('cart', JSON.stringify(cart));
    
    // Sync with server
    syncCartWithServer(cart);
    
    // Update cart UI
    updateCartBadge();
    
    return true;
}

// Update Cart Item Quantity
function updateCartItemQuantity(productId, quantity) {
    let cart = JSON.parse(sessionStorage.getItem('cart'));
    
    if (!cart) return;
    
    const itemIndex = cart.items.findIndex(item => item.product_id === productId);
    
    if (itemIndex === -1) return;
    
    // If quantity is 0 or less, remove the item
    if (quantity <= 0) {
        cart.items.splice(itemIndex, 1);
    } else {
        cart.items[itemIndex].quantity = quantity;
    }
    
    // Recalculate total
    cart.total = cart.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    
    // If cart is empty, remove shop ID
    if (cart.items.length === 0) {
        delete cart.shopId;
    }
    
    // Save updated cart
    sessionStorage.setItem('cart', JSON.stringify(cart));
    
    // Sync with server
    syncCartWithServer(cart);
    
    // Update badge
    updateCartBadge();
    
    return cart;
}

// Remove item from cart
function removeCartItem(productId) {
    return updateCartItemQuantity(productId, 0);
}

// Clear entire cart
function clearCart() {
    const emptyCart = {items: [], total: 0};
    sessionStorage.setItem('cart', JSON.stringify(emptyCart));
    syncCartWithServer(emptyCart);
    updateCartBadge();
}

// Update cart badge in navbar
function updateCartBadge() {
    const cart = JSON.parse(sessionStorage.getItem('cart'));
    const badge = document.querySelector('.cart-badge');
    
    if (!badge) return;
    
    if (cart && cart.items && cart.items.length > 0) {
        const itemCount = cart.items.reduce((sum, item) => sum + item.quantity, 0);
        badge.textContent = itemCount;
        badge.style.display = 'inline-block';
    } else {
        badge.style.display = 'none';
    }
}

// Get Cart Object
function getCart() {
    return JSON.parse(sessionStorage.getItem('cart')) || { items: [], total: 0 };
}

// Sync cart with server
function syncCartWithServer(cart) {
    fetch('/user/cart/sync', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(cart)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Cart synced with server');
        } else {
            console.error('Failed to sync cart with server:', data.message);
        }
    })
    .catch(error => {
        console.error('Error syncing cart:', error);
    });
}

// AJAX Form Submission Helper
function handleAjaxForm(formId, successCallback, errorCallback) {
    const form = document.getElementById(formId);
    
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const url = form.getAttribute('action');
        const method = form.getAttribute('method') || 'POST';
        
        // Show loading state
        form.classList.add('loading');
        const submitButton = form.querySelector('[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
        }
        
        fetch(url, {
            method: method,
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            // Reset form state
            form.classList.remove('loading');
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = submitButton.getAttribute('data-original-text') || 'Submit';
            }
            
            if (data.success) {
                if (typeof successCallback === 'function') {
                    successCallback(data);
                }
            } else {
                if (typeof errorCallback === 'function') {
                    errorCallback(data);
                } else {
                    showNotification(data.message || 'An error occurred', 'danger');
                }
            }
        })
        .catch(error => {
            // Reset form state
            form.classList.remove('loading');
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = submitButton.getAttribute('data-original-text') || 'Submit';
            }
            
            console.error('Error submitting form:', error);
            
            if (typeof errorCallback === 'function') {
                errorCallback({ success: false, message: 'Network error, please try again' });
            } else {
                showNotification('Network error, please try again', 'danger');
            }
        });
    });
    
    // Save original button text
    const submitButton = form.querySelector('[type="submit"]');
    if (submitButton) {
        submitButton.setAttribute('data-original-text', submitButton.innerHTML);
    }
}

// Show notification toast
function showNotification(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center border-0 text-white bg-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 3000
    });
    
    bsToast.show();
    
    // Remove the toast from DOM after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize all popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Initialize cart badge
    updateCartBadge();
    
    // Save form button original text
    document.querySelectorAll('form button[type="submit"]').forEach(button => {
        button.setAttribute('data-original-text', button.innerHTML);
    });
});

// Handle quantity input controls
document.addEventListener('DOMContentLoaded', function() {
    // Initialize quantity controls
    document.querySelectorAll('.quantity-control').forEach(control => {
        const input = control.querySelector('input');
        const decreaseBtn = control.querySelector('.btn-decrease');
        const increaseBtn = control.querySelector('.btn-increase');
        
        if (input && decreaseBtn && increaseBtn) {
            decreaseBtn.addEventListener('click', function() {
                let value = parseInt(input.value, 10) || 0;
                if (value > 1) {
                    input.value = value - 1;
                    input.dispatchEvent(new Event('change'));
                }
            });
            
            increaseBtn.addEventListener('click', function() {
                let value = parseInt(input.value, 10) || 0;
                const max = parseInt(input.getAttribute('max'), 10) || 9999;
                if (value < max) {
                    input.value = value + 1;
                    input.dispatchEvent(new Event('change'));
                }
            });
        }
    });
});