// User section functionality
document.addEventListener('DOMContentLoaded', async () => {
  // Get username or show login form
  const username = createUsernameForm('username-container', loadUserDashboard);
  
  if (username) {
    await loadUserDashboard(username);
  }
});

async function loadUserDashboard(username) {
  // Show welcome message
  document.getElementById('user-welcome').innerHTML = `
    <h2>Welcome, ${username}!</h2>
    <p>Browse and shop from our marketplace.</p>
  `;
  
  // Show user dashboard
  document.getElementById('user-dashboard').classList.remove('d-none');
  
  // Load approved shops
  await loadApprovedShops();
  
  // Set up search functionality
  document.getElementById('shop-search').addEventListener('input', async (e) => {
    const searchQuery = e.target.value.trim();
    await loadApprovedShops(searchQuery);
  });
}

async function loadApprovedShops(searchQuery = '') {
  const shopsContainer = document.getElementById('shops-container');
  shopsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
  
  try {
    const shops = await apiRequest(`/api/shops/search?status=approved&query=${searchQuery}`);
    
    if (!shops || shops.length === 0) {
      shopsContainer.innerHTML = `
        <div class="alert alert-info">
          ${searchQuery ? 'No shops found matching your search.' : 'No shops available yet.'}
        </div>
      `;
      return;
    }
    
    // Display shops
    const shopsHTML = shops.map(shop => `
      <div class="col-md-4 mb-4">
        <div class="card h-100">
          <div class="card-body">
            <h5 class="card-title">${shop.name}</h5>
            <p class="card-text">${shop.description}</p>
            <button 
              class="btn btn-primary view-shop-btn" 
              data-shop-id="${shop.id}" 
              data-shop-name="${shop.name}"
            >
              View Shop
            </button>
          </div>
        </div>
      </div>
    `).join('');
    
    shopsContainer.innerHTML = `<div class="row">${shopsHTML}</div>`;
    
    // Add event listeners to shop buttons
    document.querySelectorAll('.view-shop-btn').forEach(button => {
      button.addEventListener('click', () => {
        const shopId = button.getAttribute('data-shop-id');
        const shopName = button.getAttribute('data-shop-name');
        viewShopProducts(shopId, shopName);
      });
    });
    
  } catch (error) {
    shopsContainer.innerHTML = `
      <div class="alert alert-danger">
        Error loading shops: ${error.message}
      </div>
    `;
  }
}

async function viewShopProducts(shopId, shopName) {
  // Show products modal
  const modalContainer = document.getElementById('modal-container');
  modalContainer.innerHTML = `
    <div class="modal fade" id="shop-products-modal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">${shopName} - Products</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div id="products-list">
              <div class="text-center"><div class="spinner-border" role="status"></div></div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            <button type="button" class="btn btn-primary" id="checkout-btn" disabled>Checkout</button>
          </div>
        </div>
      </div>
    </div>
  `;
  
  const modal = new bootstrap.Modal(document.getElementById('shop-products-modal'));
  modal.show();
  
  // Load products
  try {
    const products = await apiRequest(`/api/shops/${shopId}/products`);
    const productsList = document.getElementById('products-list');
    
    if (!products || products.length === 0) {
      productsList.innerHTML = `
        <div class="alert alert-info">
          This shop doesn't have any products yet.
        </div>
      `;
      return;
    }
    
    // Display products with add to cart functionality
    const productsHTML = products.map(product => `
      <div class="card mb-3">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h5 class="card-title">${product.name}</h5>
              <p class="card-text">${product.description}</p>
              <p class="card-text">
                <strong>Price:</strong> ${formatPrice(product.price)}
                <br>
                <strong>In Stock:</strong> ${product.stock}
              </p>
            </div>
            <div>
              <div class="input-group" style="width: 150px;">
                <input 
                  type="number" 
                  class="form-control product-quantity" 
                  data-product-id="${product.id}" 
                  data-product-price="${product.price}"
                  data-product-name="${product.name}"
                  data-max-stock="${product.stock}"
                  min="0" 
                  max="${product.stock}" 
                  value="0"
                >
                <button 
                  class="btn btn-outline-primary add-to-cart-btn"
                  data-product-id="${product.id}"
                >
                  Add
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `).join('');
    
    productsList.innerHTML = productsHTML;
    
    // Setup shopping cart
    setupShoppingCart(shopId);
    
  } catch (error) {
    document.getElementById('products-list').innerHTML = `
      <div class="alert alert-danger">
        Error loading products: ${error.message}
      </div>
    `;
  }
}

function setupShoppingCart(shopId) {
  const cart = { items: [], totalPrice: 0 };
  
  // Add event listeners to add to cart buttons
  document.querySelectorAll('.add-to-cart-btn').forEach(button => {
    button.addEventListener('click', () => {
      const productId = button.getAttribute('data-product-id');
      const input = document.querySelector(`.product-quantity[data-product-id="${productId}"]`);
      const quantity = parseInt(input.value);
      
      if (quantity <= 0) {
        showToast('Please select a quantity greater than 0', 'error');
        return;
      }
      
      const maxStock = parseInt(input.getAttribute('data-max-stock'));
      if (quantity > maxStock) {
        showToast(`Only ${maxStock} items available in stock`, 'error');
        input.value = maxStock;
        return;
      }
      
      // Add to cart
      const price = parseFloat(input.getAttribute('data-product-price'));
      const name = input.getAttribute('data-product-name');
      
      // Check if item already in cart
      const existingItem = cart.items.find(item => item.productId === productId);
      if (existingItem) {
        existingItem.quantity = quantity;
      } else {
        cart.items.push({
          productId,
          name,
          price,
          quantity
        });
      }
      
      // Recalculate total price
      cart.totalPrice = cart.items.reduce((total, item) => total + (item.price * item.quantity), 0);
      
      // Update checkout button
      updateCartUI(cart);
      
      showToast(`Added ${quantity} ${name} to cart`);
    });
  });
  
  // Setup checkout button
  document.getElementById('checkout-btn').addEventListener('click', () => {
    if (cart.items.length === 0) {
      showToast('Your cart is empty', 'error');
      return;
    }
    
    placeOrder(shopId, cart);
  });
}

function updateCartUI(cart) {
  const checkoutBtn = document.getElementById('checkout-btn');
  
  if (cart.items.length === 0) {
    checkoutBtn.disabled = true;
    checkoutBtn.textContent = 'Checkout';
  } else {
    checkoutBtn.disabled = false;
    checkoutBtn.textContent = `Checkout (${formatPrice(cart.totalPrice)})`;
  }
}

async function placeOrder(shopId, cart) {
  try {
    const username = localStorage.getItem('username');
    if (!username) {
      showToast('Please log in to place an order', 'error');
      return;
    }
    
    // Prepare order data
    const orderData = {
      user: username,
      shop_id: shopId,
      items: cart.items,
      total_price: cart.totalPrice
    };
    
    // Send order to API
    const result = await apiRequest('/api/orders', 'POST', orderData);
    
    if (result) {
      showToast('Order placed successfully!');
      
      // Close modal and reset cart
      const modal = bootstrap.Modal.getInstance(document.getElementById('shop-products-modal'));
      modal.hide();
      
      // Show order confirmation
      showOrderConfirmation(result.id);
    }
  } catch (error) {
    showToast('Error placing order: ' + error.message, 'error');
  }
}

function showOrderConfirmation(orderId) {
  // Create and show order confirmation modal
  const modalContainer = document.getElementById('modal-container');
  modalContainer.innerHTML = `
    <div class="modal fade" id="order-confirmation-modal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Order Confirmation</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-success">
              <h4>Thank you for your order!</h4>
              <p>Your order has been placed successfully.</p>
              <p><strong>Order ID:</strong> ${orderId}</p>
            </div>
            <p>You can view your order status in your order history.</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
  `;
  
  const modal = new bootstrap.Modal(document.getElementById('order-confirmation-modal'));
  modal.show();
}
