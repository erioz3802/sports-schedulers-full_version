
// Role-based access control functions
function getCurrentUserRole() {
    return APP_CONFIG.current_user ? APP_CONFIG.current_user.role : 'official';
}

function hasPermission(action, role = null) {
    const userRole = role || getCurrentUserRole();
    const permissions = {
        'superadmin': ['view_all', 'edit_all', 'delete_all', 'manage_users', 'manage_leagues'],
        'admin': ['view_league', 'edit_league', 'delete_league', 'manage_league_users', 'assign_games'],
        'assigner': ['view_league', 'assign_games', 'manage_officials'],
        'official': ['view_assignments', 'update_profile']
    };
    
    return permissions[userRole] && permissions[userRole].includes(action);
}

function filterDataByRole(data, dataType) {
    const userRole = getCurrentUserRole();
    const userId = APP_CONFIG.current_user ? APP_CONFIG.current_user.id : null;
    
    if (userRole === 'superadmin') {
        return data; // Superadmin sees everything
    }
    
    if (userRole === 'official') {
        // Officials only see their assignments
        if (dataType === 'games') {
            return data.filter(item => item.assigned_official_id === userId);
        }
        if (dataType === 'assignments') {
            return data.filter(item => item.official_id === userId);
        }
        return [];
    }
    
    // Admin and Assigner see league-restricted data
    // This would need to be implemented based on league assignments
    return data;
}

// Update role badge display
function getRoleBadgeColor(role) {
    const colors = {
        'superadmin': 'danger',
        'admin': 'warning', 
        'assigner': 'info',
        'official': 'success'
    };
    return colors[role.toLowerCase()] || 'secondary';
}



// Role-based access control functions
function getCurrentUserRole() {
    return APP_CONFIG.current_user ? APP_CONFIG.current_user.role : 'official';
}

function hasPermission(action, role = null) {
    const userRole = role || getCurrentUserRole();
    const permissions = {
        'superadmin': ['view_all', 'edit_all', 'delete_all', 'manage_users', 'manage_leagues'],
        'admin': ['view_league', 'edit_league', 'delete_league', 'manage_league_users', 'assign_games'],
        'assigner': ['view_league', 'assign_games', 'manage_officials'],
        'official': ['view_assignments', 'update_profile']
    };
    
    return permissions[userRole] && permissions[userRole].includes(action);
}

function filterDataByRole(data, dataType) {
    const userRole = getCurrentUserRole();
    const userId = APP_CONFIG.current_user ? APP_CONFIG.current_user.id : null;
    
    if (userRole === 'superadmin') {
        return data; // Superadmin sees everything
    }
    
    if (userRole === 'official') {
        // Officials only see their assignments
        if (dataType === 'games') {
            return data.filter(item => item.assigned_official_id === userId);
        }
        if (dataType === 'assignments') {
            return data.filter(item => item.official_id === userId);
        }
        return [];
    }
    
    // Admin and Assigner see league-restricted data
    // This would need to be implemented based on league assignments
    return data;
}

// Update role badge display
function getRoleBadgeColor(role) {
    const colors = {
        'superadmin': 'danger',
        'admin': 'warning', 
        'assigner': 'info',
        'official': 'success'
    };
    return colors[role.toLowerCase()] || 'secondary';
}




// =====================================
// USERS MANAGEMENT - Sports Schedulers
// Jose Ortiz (2025)
// =====================================

// Global users data
let allUsers = [];
let editingUserId = null;

// Load users from API
function loadUsers() {
    const tableBody = document.getElementById('usersTableBody');
    if (!tableBody) return;
    
    // Show loading state
    tableBody.innerHTML = '<tr><td colspan="8" class="text-center"><div class="spinner-border spinner-border-sm me-2"></div>Loading users...</td></tr>';
    
    fetch('/api/users')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            allUsers = Array.isArray(data) ? data : (data.users || []);
            displayUsers(allUsers);
        })
        .catch(error => {
            console.error('Error loading users:', error);
            tableBody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Failed to load users: ${error.message}</td></tr>`;
        });
}

// Display users in table
function displayUsers(users) {
    const tableBody = document.getElementById('usersTableBody');
    if (!tableBody) return;
    
    if (!users || users.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4"><i class="fas fa-users fa-2x mb-2"></i><br>No users found</td></tr>';
        return;
    }
    
    tableBody.innerHTML = users.map(user => {
        const statusBadge = user.is_active ? 
            '<span class="badge bg-success">Active</span>' : 
            '<span class="badge bg-secondary">Inactive</span>';
        
        const roleBadge = getRoleBadge(user.role);
        const createdDate = user.created_date ? new Date(user.created_date).toLocaleDateString() : 'N/A';
        const fullName = user.full_name || '';
        const email = user.email || '';
        
        return `
            <tr>
                <td>${user.id || ''}</td>
                <td><strong>${escapeHtml(user.username || '')}</strong></td>
                <td>${escapeHtml(fullName)}</td>
                <td>${escapeHtml(email)}</td>
                <td>${roleBadge}</td>
                <td>${statusBadge}</td>
                <td>${createdDate}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary btn-sm" onclick="editUser(${user.id})" title="Edit User">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-info btn-sm" onclick="viewUser(${user.id})" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-sm" onclick="deleteUser(${user.id}, '${escapeHtml(user.username)}')" title="Delete User">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
    }).join('');
}

// Get role badge HTML
function getRoleBadge(role) {
    const roleClasses = {
        'Superadmin': 'bg-danger',
        'Admin': 'bg-warning text-dark',
        'Official': 'bg-primary'
    };
    const badgeClass = roleClasses[role] || 'bg-secondary';
    return `<span class="badge ${badgeClass}">${escapeHtml(role || 'Unknown')}</span>`;
}

// Filter users
function filterUsers() {
    const searchTerm = (document.getElementById('userSearch')?.value || '').toLowerCase();
    const roleFilter = document.getElementById('roleFilter')?.value || '';
    const statusFilter = document.getElementById('statusFilter')?.value || '';
    
    const filteredUsers = allUsers.filter(user => {
        const matchesSearch = !searchTerm || 
            (user.username && user.username.toLowerCase().includes(searchTerm)) ||
            (user.full_name && user.full_name.toLowerCase().includes(searchTerm)) ||
            (user.email && user.email.toLowerCase().includes(searchTerm));
        
        const matchesRole = !roleFilter || user.role === roleFilter;
        const matchesStatus = !statusFilter || user.is_active.toString() === statusFilter;
        
        return matchesSearch && matchesRole && matchesStatus;
    });
    
    displayUsers(filteredUsers);
}

// Open user modal
function openUserModal(userId = null) {
    editingUserId = userId;
    const modal = new bootstrap.Modal(document.getElementById('userModal'));
    const form = document.getElementById('userForm');
    const title = document.getElementById('userModalLabel');
    const passwordResetDiv = document.getElementById('passwordResetDiv');
    
    // Reset form
    form.reset();
    form.classList.remove('was-validated');
    
    if (userId) {
        title.textContent = 'Edit User';
        passwordResetDiv.style.display = 'block';
        
        const user = allUsers.find(u => u.id === userId);
        if (user) {
            document.getElementById('userId').value = user.id;
            document.getElementById('username').value = user.username || '';
            document.getElementById('email').value = user.email || '';
            
            // Parse full name
            const nameParts = (user.full_name || '').split(' ');
            document.getElementById('firstName').value = nameParts[0] || '';
            document.getElementById('lastName').value = nameParts.slice(1).join(' ') || '';
            
            document.getElementById('phone').value = user.phone || '';
            document.getElementById('userRole').value = user.role || '';
            document.getElementById('address').value = user.address || '';
            document.getElementById('isActive').checked = user.is_active;
        }
    } else {
        title.textContent = 'Add New User';
        passwordResetDiv.style.display = 'none';
        document.getElementById('isActive').checked = true;
    }
    
    modal.show();
}

// Edit user
function editUser(userId) {
    openUserModal(userId);
}

// View user details
function viewUser(userId) {
    const user = allUsers.find(u => u.id === userId);
    if (!user) {
        showAlert('User not found', 'error');
        return;
    }
    
    const detailsModal = new bootstrap.Modal(document.getElementById('userDetailsModal'));
    const detailsContent = document.getElementById('userDetailsContent');
    
    detailsContent.innerHTML = `
        <div class="row">
            <div class="col-sm-4"><strong>Username:</strong></div>
            <div class="col-sm-8">${escapeHtml(user.username || 'N/A')}</div>
        </div>
        <div class="row mt-2">
            <div class="col-sm-4"><strong>Full Name:</strong></div>
            <div class="col-sm-8">${escapeHtml(user.full_name || 'N/A')}</div>
        </div>
        <div class="row mt-2">
            <div class="col-sm-4"><strong>Email:</strong></div>
            <div class="col-sm-8">${escapeHtml(user.email || 'N/A')}</div>
        </div>
        <div class="row mt-2">
            <div class="col-sm-4"><strong>Phone:</strong></div>
            <div class="col-sm-8">${escapeHtml(user.phone || 'N/A')}</div>
        </div>
        <div class="row mt-2">
            <div class="col-sm-4"><strong>Role:</strong></div>
            <div class="col-sm-8">${getRoleBadge(user.role)}</div>
        </div>
        <div class="row mt-2">
            <div class="col-sm-4"><strong>Status:</strong></div>
            <div class="col-sm-8">${user.is_active ? '<span class="badge bg-success">Active</span>' : '<span class="badge bg-secondary">Inactive</span>'}</div>
        </div>
        <div class="row mt-2">
            <div class="col-sm-4"><strong>Created:</strong></div>
            <div class="col-sm-8">${user.created_date ? new Date(user.created_date).toLocaleString() : 'N/A'}</div>
        </div>
    `;
    
    detailsModal.show();
}

// Save user
function saveUser() {
    const form = document.getElementById('userForm');
    const saveButton = form.querySelector('button[onclick="saveUser()"]');
    const saveButtonText = document.getElementById('saveButtonText');
    const saveSpinner = document.getElementById('saveSpinner');
    
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
    }
    
    // Show loading
    saveButton.disabled = true;
    saveButtonText.textContent = editingUserId ? 'Updating...' : 'Creating...';
    saveSpinner.style.display = 'inline-block';
    
    const formData = new FormData(form);
    const userData = {
        username: formData.get('username'),
        email: formData.get('email'),
        full_name: `${formData.get('firstName')} ${formData.get('lastName')}`.trim(),
        phone: formData.get('phone') || '',
        role: formData.get('role'),
        address: formData.get('address') || '',
        is_active: formData.has('isActive'),
        reset_password: formData.has('resetPassword')
    };
    
    const url = editingUserId ? `/api/users/${editingUserId}` : '/api/users';
    const method = editingUserId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(data => {
        showAlert(editingUserId ? 'User updated successfully' : 'User created successfully', 'success');
        bootstrap.Modal.getInstance(document.getElementById('userModal')).hide();
        loadUsers();
    })
    .catch(error => {
        console.error('Error saving user:', error);
        showAlert(error.message || 'Failed to save user', 'error');
    })
    .finally(() => {
        saveButton.disabled = false;
        saveButtonText.textContent = 'Save User';
        saveSpinner.style.display = 'none';
    });
}

// Delete user
function deleteUser(userId, username) {
    if (!confirm(`Are you sure you want to delete user "${username}"?\n\nThis action cannot be undone.`)) {
        return;
    }
    
    fetch(`/api/users/${userId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(data => {
        showAlert('User deleted successfully', 'success');
        loadUsers();
    })
    .catch(error => {
        console.error('Error deleting user:', error);
        showAlert(error.message || 'Failed to delete user', 'error');
    });
}

// Refresh users
function refreshUsers() {
    loadUsers();
}

// Initialize users tab when shown
function initializeUsersTab() {
    if (document.getElementById('users-content')) {
        loadUsers();
    }
}

// Utility function for escaping HTML (if not already defined)
if (typeof escapeHtml === 'undefined') {
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text ? text.toString().replace(/[&<>"']/g, function(m) { return map[m]; }) : '';
    }
}

// Utility function for showing alerts (if not already defined)
if (typeof showAlert === 'undefined') {
    function showAlert(message, type = 'info') {
        console.log(`${type.toUpperCase()}: ${message}`);
        // You can enhance this with a proper alert system
    }
}

// Auto-initialize when users tab is clicked
document.addEventListener('DOMContentLoaded', function() {
    const usersTab = document.querySelector('[data-tab="users"]');
    if (usersTab) {
        usersTab.addEventListener('click', function() {
            setTimeout(initializeUsersTab, 100); // Small delay to ensure tab content is visible
        });
    }
});