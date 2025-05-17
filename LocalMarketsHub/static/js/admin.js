// Admin section functionality
document.addEventListener('DOMContentLoaded', async () => {
  // Get username or show login form
  const username = createUsernameForm('username-container', loadAdminDashboard);
  
  if (username) {
    await loadAdminDashboard(username);
  }
});

async function loadAdminDashboard(username) {
  // Show welcome message
  document.getElementById('admin-welcome').innerHTML = `
    <h2>Admin Dashboard</h2>
    <p>Welcome, ${username}! Manage shop requests and marketplace here.</p>
  `;
  
  // Show admin dashboard
  document.getElementById('admin-dashboard').classList.remove('d-none');
  
  // Load dashboard statistics
  await loadDashboardStats();
  
  // Load pending shop requests
  await loadPendingShopRequests();
  
  // Load all shops
  await loadAllShops();
  
  // Setup refresh buttons
  document.getElementById('refresh-stats-btn').addEventListener('click', loadDashboardStats);
  document.getElementById('refresh-requests-btn').addEventListener('click', loadPendingShopRequests);
  document.getElementById('refresh-shops-btn').addEventListener('click', loadAllShops);
}

async function loadDashboardStats() {
  const statsContainer = document.getElementById('admin-stats');
  statsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
  
  try {
    const stats = await apiRequest('/api/stats');
    
    statsContainer.innerHTML = `
      <div class="row g-4">
        <div class="col-md-3">
          <div class="card text-center h-100">
            <div class="card-body">
              <h5 class="card-title">${stats.users_count}</h5>
              <p class="card-text">Total Users</p>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card text-center h-100">
            <div class="card-body">
              <h5 class="card-title">${stats.shops_count}</h5>
              <p class="card-text">Total Shops</p>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card text-center h-100">
            <div class="card-body">
              <h5 class="card-title">${stats.pending_shops}</h5>
              <p class="card-text">Pending Shops</p>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card text-center h-100">
            <div class="card-body">
              <h5 class="card-title">${stats.orders_count}</h5>
              <p class="card-text">Total Orders</p>
            </div>
          </div>
        </div>
      </div>
    `;
  } catch (error) {
    statsContainer.innerHTML = `
      <div class="alert alert-danger">
        Error loading statistics: ${error.message}
      </div>
    `;
  }
}

async function loadPendingShopRequests() {
  const requestsContainer = document.getElementById('pending-requests');
  requestsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
  
  try {
    const shops = await apiRequest('/api/shops?status=pending');
    
    if (!shops || shops.length === 0) {
      requestsContainer.innerHTML = `
        <div class="alert alert-info">
          There are no pending shop requests.
        </div>
      `;
      return;
    }
    
    // Display pending shop requests
    const requestsHTML = shops.map(shop => `
      <div class="card mb-3">
        <div class="card-body">
          <h5 class="card-title">${shop.name}</h5>
          <p class="card-text"><strong>Owner:</strong> ${shop.owner}</p>
          <p class="card-text">${shop.description}</p>
          <p class="card-text small text-muted">Requested on: ${formatDate(shop.created_at)}</p>
          <div class="d-flex justify-content-end gap-2">
            <button 
              class="btn btn-danger reject-shop-btn" 
              data-shop-id="${shop.id}" 
              data-shop-name="${shop.name}"
            >
              Reject
            </button>
            <button 
              class="btn btn-success approve-shop-btn" 
              data-shop-id="${shop.id}" 
              data-shop-name="${shop.name}"
            >
              Approve
            </button>
          </div>
        </div>
      </div>
    `).join('');
    
    requestsContainer.innerHTML = requestsHTML;
    
    // Add event listeners for request actions
    setupRequestActionListeners();
    
  } catch (error) {
    requestsContainer.innerHTML = `
      <div class="alert alert-danger">
        Error loading pending requests: ${error.message}
      </div>
    `;
  }
}

function setupRequestActionListeners() {
  // Approve shop buttons
  document.querySelectorAll('.approve-shop-btn').forEach(button => {
    button.addEventListener('click', async () => {
      const shopId = button.getAttribute('data-shop-id');
      const shopName = button.getAttribute('data-shop-name');
      
      if (confirm(`Are you sure you want to approve "${shopName}"?`)) {
        try {
          const result = await apiRequest(`/api/shops/${shopId}`, 'PUT', {
            status: 'approved'
          });
          
          if (result) {
            showToast(`Shop "${shopName}" has been approved!`);
            
            // Reload requests and shops
            await loadPendingShopRequests();
            await loadAllShops();
            await loadDashboardStats();
          }
        } catch (error) {
          showToast('Error approving shop: ' + error.message, 'error');
        }
      }
    });
  });
  
  // Reject shop buttons
  document.querySelectorAll('.reject-shop-btn').forEach(button => {
    button.addEventListener('click', async () => {
      const shopId = button.getAttribute('data-shop-id');
      const shopName = button.getAttribute('data-shop-name');
      
      if (confirm(`Are you sure you want to reject "${shopName}"?`)) {
        try {
          const result = await apiRequest(`/api/shops/${shopId}`, 'PUT', {
            status: 'rejected'
          });
          
          if (result) {
            showToast(`Shop "${shopName}" has been rejected!`);
            
            // Reload requests and shops
            await loadPendingShopRequests();
            await loadAllShops();
            await loadDashboardStats();
          }
        } catch (error) {
          showToast('Error rejecting shop: ' + error.message, 'error');
        }
      }
    });
  });
}

async function loadAllShops() {
  const shopsContainer = document.getElementById('all-shops');
  shopsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
  
  try {
    const shops = await apiRequest('/api/shops');
    
    if (!shops || shops.length === 0) {
      shopsContainer.innerHTML = `
        <div class="alert alert-info">
          There are no shops yet.
        </div>
      `;
      return;
    }
    
    // Sort shops by status (approved first, then pending, then rejected)
    const statusOrder = { 'approved': 1, 'pending': 2, 'rejected': 3 };
    shops.sort((a, b) => statusOrder[a.status] - statusOrder[b.status]);
    
    // Display all shops
    const shopsHTML = `
      <div class="table-responsive">
        <table class="table table-striped table-hover">
          <thead>
            <tr>
              <th>Name</th>
              <th>Owner</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${shops.map(shop => `
              <tr>
                <td>${shop.name}</td>
                <td>${shop.owner}</td>
                <td>
                  <span class="badge ${getStatusBadgeClass(shop.status)}">${shop.status}</span>
                </td>
                <td>${formatDate(shop.created_at)}</td>
                <td>
                  <div class="btn-group btn-group-sm">
                    <button 
                      class="btn btn-outline-primary view-shop-btn" 
                      data-shop-id="${shop.id}" 
                      data-shop-name="${shop.name}"
                    >
                      View
                    </button>
                    ${shop.status === 'pending' ? `
                      <button 
                        class="btn btn-outline-success approve-shop-btn" 
                        data-shop-id="${shop.id}" 
                        data-shop-name="${shop.name}"
                      >
                        Approve
                      </button>
                      <button 
                        class="btn btn-outline-danger reject-shop-btn" 
                        data-shop-id="${shop.id}" 
                        data-shop-name="${shop.name}"
                      >
                        Reject
                      </button>
                    ` : 
                    shop.status === 'rejected' ? `
                      <button 
                        class="btn btn-outline-success approve-shop-btn" 
                        data-shop-id="${shop.id}" 
                        data-shop-name="${shop.name}"
                      >
                        Approve
                      </button>
                    ` : 
                    shop.status === 'approved' ? `
                      <button 
                        class="btn btn-outline-danger reject-shop-btn" 
                        data-shop-id="${shop.id}" 
                        data-shop-name="${shop.name}"
                      >
                        Suspend
                      </button>
                    ` : ''}
                  </div>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
    
    shopsContainer.innerHTML = shopsHTML;
    
    // Add event listeners for shop actions
    setupRequestActionListeners(); // Reuse the same listeners for approve/reject
    
    // View shop details
    document.querySelectorAll('.view-shop-btn').forEach(button => {
      button.addEventListener('click', () => {
        const shopId = button.getAttribute('data-shop-id');
        const shopName = button.getAttribute('data-shop-name');
        viewShopDetails(shopId, shopName);
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

async function viewShopDetails(shopId, shopName) {
  // Show shop details modal
  const modalContainer = document.getElementById('modal-container');
  modalContainer.innerHTML = `
    <div class="modal fade" id="shop-details-modal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">${shopName} - Details</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div id="shop-details">
              <div class="text-center"><div class="spinner-border" role="status"></div></div>
            </div>
            
            <hr>
            
            <h6>Products</h6>
            <div id="shop-products">
              <div class="text-center"><div class="spinner-border" role="status"></div></div>
            </div>
            
            <hr>
            
            <h6>Recent Orders</h6>
            <div id="shop-orders">
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
  
  const modal = new bootstrap.Modal(document.getElementById('shop-details-modal'));
  modal.show();
  
  // Load shop details
  try {
    const [shop, products, orders] = await Promise.all([
      apiRequest(`/api/shops/${shopId}`),
      apiRequest(`/api/shops/${shopId}/products`),
      apiRequest(`/api/orders?shop_id=${shopId}`)
    ]);
    
    // Display shop details
    document.getElementById('shop-details').innerHTML = `
      <div class="card">
        <div class="card-body">
          <h5 class="card-title">${shop.name}</h5>
          <p class="card-text"><strong>Owner:</strong> ${shop.owner}</p>
          <p class="card-text"><strong>Status:</strong> 
            <span class="badge ${getStatusBadgeClass(shop.status)}">${shop.status}</span>
          </p>
          <p class="card-text"><strong>Description:</strong> ${shop.description}</p>
          <p class="card-text"><strong>Created:</strong> ${formatDate(shop.created_at)}</p>
        </div>
      </div>
    `;
    
    // Display products
    if (!products || products.length === 0) {
      document.getElementById('shop-products').innerHTML = `
        <div class="alert alert-info">
          This shop has no products yet.
        </div>
      `;
    } else {
      document.getElementById('shop-products').innerHTML = `
        <div class="table-responsive">
          <table class="table table-sm">
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Price</th>
                <th>Stock</th>
              </tr>
            </thead>
            <tbody>
              ${products.map(product => `
                <tr>
                  <td>${product.name}</td>
                  <td>${product.description}</td>
                  <td>${formatPrice(product.price)}</td>
                  <td>${product.stock}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    }
    
    // Display orders
    if (!orders || orders.length === 0) {
      document.getElementById('shop-orders').innerHTML = `
        <div class="alert alert-info">
          This shop has no orders yet.
        </div>
      `;
    } else {
      // Sort by newest first
      orders.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      
      // Limit to 5 most recent
      const recentOrders = orders.slice(0, 5);
      
      document.getElementById('shop-orders').innerHTML = `
        <div class="table-responsive">
          <table class="table table-sm">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>User</th>
                <th>Date</th>
                <th>Total</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${recentOrders.map(order => `
                <tr>
                  <td>${order.id}</td>
                  <td>${order.user}</td>
                  <td>${formatDate(order.created_at)}</td>
                  <td>${formatPrice(order.total_price)}</td>
                  <td>
                    <span class="badge ${getOrderStatusBadgeClass(order.status)}">${order.status}</span>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    }
    
  } catch (error) {
    document.getElementById('shop-details').innerHTML = `
      <div class="alert alert-danger">
        Error loading shop details: ${error.message}
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
