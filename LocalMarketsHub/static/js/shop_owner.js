// Shop Owner section functionality
document.addEventListener('DOMContentLoaded', async () => {
  // Get username or show login form
  const username = createUsernameForm('username-container', loadShopOwnerDashboard);
  
  if (username) {
    await loadShopOwnerDashboard(username);
  }
});

async function loadShopOwnerDashboard(username) {
  // Show welcome message
  document.getElementById('shop-owner-welcome').innerHTML = `
    <h2>Shop Owner Dashboard</h2>
    <p>Welcome, ${username}! Manage your shops and products here.</p>
  `;
  
  // Show shop owner dashboard
  document.getElementById('shop-owner-dashboard').classList.remove('d-none');
  
  // Load shop owner's shops
  await loadOwnerShops(username);

  // Setup create shop form
  setupCreateShopForm(username);

  // Setup interval to refresh orders
  setInterval(() => {
    refreshShopOrders();
  }, 30000); // Refresh every 30 seconds
}

async function loadOwnerShops(username) {
  const shopsContainer = document.getElementById('owner-shops-container');
  shopsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
  
  try {
    const shops = await apiRequest(`/api/shops/owner/${username}`);
    
    if (!shops || shops.length === 0) {
      shopsContainer.innerHTML = `
        <div class="alert alert-info">
          You don't have any shops yet. Create one below!
        </div>
      `;
      return;
    }
    
    // Display shops
    const shopsHTML = shops.map(shop => `
      <div class="card mb-4">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0">${shop.name}</h5>
          <span class="badge ${getStatusBadgeClass(shop.status)}">${shop.status}</span>
        </div>
        <div class="card-body">
          <p>${shop.description}</p>
          <p><strong>Created:</strong> ${formatDate(shop.created_at)}</p>
          
          ${shop.status === 'approved' ? `
            <div class="d-flex justify-content-between">
              <button 
                class="btn btn-primary manage-products-btn" 
                data-shop-id="${shop.id}" 
                data-shop-name="${shop.name}"
              >
                Manage Products
              </button>
              <button 
                class="btn btn-info view-orders-btn" 
                data-shop-id="${shop.id}" 
                data-shop-name="${shop.name}"
              >
                View Orders
              </button>
            </div>
          ` : `
            <div class="alert alert-warning">
              Your shop needs to be approved by an admin before you can manage products.
            </div>
          `}
        </div>
      </div>
    `).join('');
    
    shopsContainer.innerHTML = shopsHTML;
    
    // Add event listeners to shop buttons
    document.querySelectorAll('.manage-products-btn').forEach(button => {
      button.addEventListener('click', () => {
        const shopId = button.getAttribute('data-shop-id');
        const shopName = button.getAttribute('data-shop-name');
        manageShopProducts(shopId, shopName);
      });
    });
    
    document.querySelectorAll('.view-orders-btn').forEach(button => {
      button.addEventListener('click', () => {
        const shopId = button.getAttribute('data-shop-id');
        const shopName = button.getAttribute('data-shop-name');
        viewShopOrders(shopId, shopName);
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

function getStatusBadgeClass(status) {
  switch (status) {
    case 'approved':
      return 'bg-success';
    case 'rejected':
      return 'bg-danger';
    case 'pending':
    default:
      return 'bg-warning';
  }
}

function setupCreateShopForm(username) {
  const form = document.getElementById('create-shop-form');
  
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const shopName = document.getElementById('shop-name').value.trim();
    const shopDescription = document.getElementById('shop-description').value.trim();
    
    if (!shopName || !shopDescription) {
      showToast('Please fill in all fields', 'error');
      return;
    }
    
    try {
      const result = await apiRequest('/api/shops', 'POST', {
        name: shopName,
        owner: username,
        description: shopDescription
      });
      
      if (result) {
        showToast('Shop request submitted! Waiting for admin approval.');
        
        // Reset form
        form.reset();
        
        // Reload shops
        await loadOwnerShops(username);
      }
    } catch (error) {
      showToast('Error creating shop: ' + error.message, 'error');
    }
  });
}

async function manageShopProducts(shopId, shopName) {
  // Show products management modal
  const modalContainer = document.getElementById('modal-container');
  modalContainer.innerHTML = `
    <div class="modal fade" id="manage-products-modal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">${shopName} - Manage Products</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="mb-4">
              <h6>Add New Product</h6>
              <form id="add-product-form">
                <div class="row g-3">
                  <div class="col-md-6">
                    <input type="text" class="form-control" id="product-name" placeholder="Product Name" required>
                  </div>
                  <div class="col-md-3">
                    <input type="number" class="form-control" id="product-price" placeholder="Price" step="0.01" min="0.01" required>
                  </div>
                  <div class="col-md-3">
                    <input type="number" class="form-control" id="product-stock" placeholder="Stock" min="1" required>
                  </div>
                  <div class="col-12">
                    <textarea class="form-control" id="product-description" placeholder="Description" rows="2" required></textarea>
                  </div>
                  <div class="col-12">
                    <button type="submit" class="btn btn-success">Add Product</button>
                  </div>
                </div>
              </form>
            </div>
            
            <hr>
            
            <h6>Current Products</h6>
            <div id="products-list">
              <div class="text-center"><div class="spinner-border" role="status"></div></div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
  `;
  
  const modal = new bootstrap.Modal(document.getElementById('manage-products-modal'));
  modal.show();
  
  // Load products
  loadShopProducts(shopId);
  
  // Setup add product form
  document.getElementById('add-product-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const productName = document.getElementById('product-name').value.trim();
    const productDescription = document.getElementById('product-description').value.trim();
    const productPrice = document.getElementById('product-price').value;
    const productStock = document.getElementById('product-stock').value;
    
    try {
      const result = await apiRequest(`/api/shops/${shopId}/products`, 'POST', {
        name: productName,
        description: productDescription,
        price: productPrice,
        stock: productStock
      });
      
      if (result) {
        showToast('Product added successfully!');
        
        // Reset form
        document.getElementById('add-product-form').reset();
        
        // Reload products
        loadShopProducts(shopId);
      }
    } catch (error) {
      showToast('Error adding product: ' + error.message, 'error');
    }
  });
}

async function loadShopProducts(shopId) {
  const productsList = document.getElementById('products-list');
  
  try {
    const products = await apiRequest(`/api/shops/${shopId}/products`);
    
    if (!products || products.length === 0) {
      productsList.innerHTML = `
        <div class="alert alert-info">
          You don't have any products yet. Add one using the form above!
        </div>
      `;
      return;
    }
    
    // Display products with edit and delete options
    const productsHTML = products.map(product => `
      <div class="card mb-3">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h6 class="card-title mb-0">${product.name}</h6>
            <div>
              <button 
                class="btn btn-sm btn-outline-primary edit-product-btn" 
                data-product-id="${product.id}"
              >
                Edit
              </button>
              <button 
                class="btn btn-sm btn-outline-danger delete-product-btn" 
                data-product-id="${product.id}" 
                data-product-name="${product.name}"
              >
                Delete
              </button>
            </div>
          </div>
          <p class="card-text small mb-1">${product.description}</p>
          <div class="d-flex justify-content-between">
            <span><strong>Price:</strong> ${formatPrice(product.price)}</span>
            <span><strong>Stock:</strong> ${product.stock}</span>
          </div>
          
          <!-- Edit form (hidden by default) -->
          <div class="product-edit-form d-none mt-3" id="edit-form-${product.id}">
            <form class="update-product-form" data-product-id="${product.id}">
              <div class="row g-2">
                <div class="col-md-6">
                  <input type="text" class="form-control form-control-sm" name="name" value="${product.name}" required>
                </div>
                <div class="col-md-3">
                  <input type="number" class="form-control form-control-sm" name="price" value="${product.price}" step="0.01" min="0.01" required>
                </div>
                <div class="col-md-3">
                  <input type="number" class="form-control form-control-sm" name="stock" value="${product.stock}" min="1" required>
                </div>
                <div class="col-12">
                  <textarea class="form-control form-control-sm" name="description" rows="2" required>${product.description}</textarea>
                </div>
                <div class="col-12 text-end">
                  <button type="button" class="btn btn-sm btn-secondary cancel-edit-btn" data-product-id="${product.id}">Cancel</button>
                  <button type="submit" class="btn btn-sm btn-success">Save</button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    `).join('');
    
    productsList.innerHTML = productsHTML;
    
    // Add event listeners for product actions
    setupProductEventListeners(shopId);
    
  } catch (error) {
    productsList.innerHTML = `
      <div class="alert alert-danger">
        Error loading products: ${error.message}
      </div>
    `;
  }
}

function setupProductEventListeners(shopId) {
  // Edit product buttons
  document.querySelectorAll('.edit-product-btn').forEach(button => {
    button.addEventListener('click', () => {
      const productId = button.getAttribute('data-product-id');
      const editForm = document.getElementById(`edit-form-${productId}`);
      editForm.classList.toggle('d-none');
    });
  });
  
  // Cancel edit buttons
  document.querySelectorAll('.cancel-edit-btn').forEach(button => {
    button.addEventListener('click', () => {
      const productId = button.getAttribute('data-product-id');
      const editForm = document.getElementById(`edit-form-${productId}`);
      editForm.classList.add('d-none');
    });
  });
  
  // Update product forms
  document.querySelectorAll('.update-product-form').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const productId = form.getAttribute('data-product-id');
      const formData = new FormData(form);
      const productData = {
        name: formData.get('name'),
        description: formData.get('description'),
        price: formData.get('price'),
        stock: formData.get('stock')
      };
      
      try {
        const result = await apiRequest(`/api/shops/${shopId}/products/${productId}`, 'PUT', productData);
        
        if (result) {
          showToast('Product updated successfully!');
          
          // Hide edit form
          const editForm = document.getElementById(`edit-form-${productId}`);
          editForm.classList.add('d-none');
          
          // Reload products
          loadShopProducts(shopId);
        }
      } catch (error) {
        showToast('Error updating product: ' + error.message, 'error');
      }
    });
  });
  
  // Delete product buttons
  document.querySelectorAll('.delete-product-btn').forEach(button => {
    button.addEventListener('click', async () => {
      const productId = button.getAttribute('data-product-id');
      const productName = button.getAttribute('data-product-name');
      
      if (confirm(`Are you sure you want to delete "${productName}"?`)) {
        try {
          const result = await apiRequest(`/api/shops/${shopId}/products/${productId}`, 'DELETE');
          
          if (result) {
            showToast('Product deleted successfully!');
            
            // Reload products
            loadShopProducts(shopId);
          }
        } catch (error) {
          showToast('Error deleting product: ' + error.message, 'error');
        }
      }
    });
  });
}

async function viewShopOrders(shopId, shopName) {
  // Show orders modal
  const modalContainer = document.getElementById('modal-container');
  modalContainer.innerHTML = `
    <div class="modal fade" id="shop-orders-modal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">${shopName} - Orders</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div id="orders-list" data-shop-id="${shopId}">
              <div class="text-center"><div class="spinner-border" role="status"></div></div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            <button type="button" class="btn btn-primary" id="refresh-orders-btn">
              <i class="bi bi-arrow-clockwise"></i> Refresh Orders
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
  
  const modal = new bootstrap.Modal(document.getElementById('shop-orders-modal'));
  modal.show();
  
  // Load orders
  loadShopOrders(shopId);
  
  // Setup refresh button
  document.getElementById('refresh-orders-btn').addEventListener('click', () => {
    loadShopOrders(shopId);
  });
}

async function loadShopOrders(shopId) {
  const ordersList = document.getElementById('orders-list');
  
  try {
    const orders = await apiRequest(`/api/orders?shop_id=${shopId}`);
    
    if (!orders || orders.length === 0) {
      ordersList.innerHTML = `
        <div class="alert alert-info">
          You don't have any orders yet.
        </div>
      `;
      return;
    }
    
    // Sort orders by date (newest first)
    orders.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    // Display orders
    const ordersHTML = orders.map(order => `
      <div class="card mb-3">
        <div class="card-header d-flex justify-content-between">
          <span>Order #${order.id}</span>
          <span class="badge ${getOrderStatusBadgeClass(order.status)}">${order.status}</span>
        </div>
        <div class="card-body">
          <p><strong>Customer:</strong> ${order.user}</p>
          <p><strong>Date:</strong> ${formatDate(order.created_at)}</p>
          <p><strong>Total:</strong> ${formatPrice(order.total_price)}</p>
          
          <h6>Items:</h6>
          <ul class="list-group mb-3">
            ${order.items.map(item => `
              <li class="list-group-item d-flex justify-content-between align-items-center">
                ${item.name}
                <span>${item.quantity} × ${formatPrice(item.price)}</span>
              </li>
            `).join('')}
          </ul>
          
          <div class="d-flex justify-content-end">
            ${order.status === 'pending' ? `
              <button 
                class="btn btn-success complete-order-btn" 
                data-order-id="${order.id}"
              >
                Mark as Completed
              </button>
            ` : ''}
          </div>
        </div>
      </div>
    `).join('');
    
    ordersList.innerHTML = ordersHTML;
    
    // Add event listeners for order actions
    document.querySelectorAll('.complete-order-btn').forEach(button => {
      button.addEventListener('click', async () => {
        const orderId = button.getAttribute('data-order-id');
        
        try {
          const result = await apiRequest(`/api/orders/${orderId}`, 'PUT', {
            status: 'completed'
          });
          
          if (result) {
            showToast('Order marked as completed!');
            
            // Reload orders
            loadShopOrders(shopId);
          }
        } catch (error) {
          showToast('Error updating order: ' + error.message, 'error');
        }
      });
    });
    
  } catch (error) {
    ordersList.innerHTML = `
      <div class="alert alert-danger">
        Error loading orders: ${error.message}
      </div>
    `;
  }
}

function getOrderStatusBadgeClass(status) {
  switch (status) {
    case 'completed':
      return 'bg-success';
    case 'cancelled':
      return 'bg-danger';
    case 'pending':
    default:
      return 'bg-warning';
  }
}

function refreshShopOrders() {
  // If the orders modal is open, refresh the orders
  const ordersList = document.getElementById('orders-list');
  if (ordersList && ordersList.dataset.shopId) {
    loadShopOrders(ordersList.dataset.shopId);
  }
}
