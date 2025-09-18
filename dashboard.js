
// ============================================================================
// ENHANCED USER MANAGEMENT JAVASCRIPT
// Added by Enhanced User Management Script - Jose Ortiz - September 8, 2025
// ============================================================================

// Global variables for user management
let currentUsersPage = 1;
let usersPerPage = 10;
let currentUsersData = [];

// User Management Functions
function loadUsers(page = 1) {
    currentUsersPage = page;
    const search = document.getElementById('user-search')?.value || '';
    const roleFilter = document.getElementById('role-filter')?.value || '';
    const statusFilter = document.getElementById('status-filter')?.value || '';
    
    const params = new URLSearchParams({
        page: page,
        per_page: usersPerPage,
        search: search,
        role: roleFilter,
        status: statusFilter
    });
    
    fetch(`/api/users?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.users) {
                currentUsersData = data.users;
                displayUsers(data.users);
                displayUsersPagination(data.page, data.pages, data.total);
            } else {
                showAlert('Error loading users: ' + (data.error || 'Unknown error'), 'error');
            }
        })
        .catch(error => {
            console.error('Error loading users:', error);
            showAlert('Error loading users', 'error');
        });
}

function displayUsers(users) {
    const tbody = document.getElementById('users-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    users.forEach(user => {
        const row = document.createElement('tr');
        const statusBadge = user.is_active ? 
            '<span class="badge badge-success">Active</span>' : 
            '<span class="badge badge-secondary">Inactive</span>';
        
        const createdDate = new Date(user.created_date).toLocaleDateString();
        
        row.innerHTML = `
            <td>${user.username}</td>
            <td>${user.full_name || ''}</td>
            <td>${user.email || ''}</td>
            <td><span class="badge badge-primary">${(user.role || '').replace('_', ' ').toUpperCase()}</span></td>
            <td>${statusBadge}</td>
            <td>${createdDate}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="editUser(${user.id})" title="Edit">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-warning" onclick="resetPassword(${user.id})" title="Reset Password">
                    <i class="fas fa-key"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${user.id})" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function displayUsersPagination(currentPage, totalPages, totalRecords) {
    const pagination = document.getElementById('users-pagination');
    if (!pagination) return;
    
    pagination.innerHTML = '';
    
    // Previous button
    const prevButton = document.createElement('li');
    prevButton.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevButton.innerHTML = `<a class="page-link" href="#" onclick="loadUsers(${currentPage - 1})">Previous</a>`;
    pagination.appendChild(prevButton);
    
    // Page numbers
    for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
        const pageButton = document.createElement('li');
        pageButton.className = `page-item ${i === currentPage ? 'active' : ''}`;
        pageButton.innerHTML = `<a class="page-link" href="#" onclick="loadUsers(${i})">${i}</a>`;
        pagination.appendChild(pageButton);
    }
    
    // Next button
    const nextButton = document.createElement('li');
    nextButton.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextButton.innerHTML = `<a class="page-link" href="#" onclick="loadUsers(${currentPage + 1})">Next</a>`;
    pagination.appendChild(nextButton);
}

function searchUsers() {
    loadUsers(1);
}

function filterUsers() {
    loadUsers(1);
}

function refreshUsers() {
    loadUsers(currentUsersPage);
}

function openUserModal(userId = null) {
    const modal = document.getElementById('userModal');
    const title = document.getElementById('userModalTitle');
    const form = document.getElementById('userForm');
    
    if (!modal || !title || !form) return;
    
    form.reset();
    
    if (userId) {
        title.textContent = 'Edit User';
        const user = currentUsersData.find(u => u.id === userId);
        if (user) {
            document.getElementById('user-id').value = user.id;
            document.getElementById('user-username').value = user.username;
            document.getElementById('user-role').value = user.role;
            document.getElementById('user-fullname').value = user.full_name || '';
            document.getElementById('user-email').value = user.email || '';
            document.getElementById('user-phone').value = user.phone || '';
            document.getElementById('user-address').value = user.address || '';
            document.getElementById('user-active').checked = user.is_active;
        }
    } else {
        title.textContent = 'Add User';
        document.getElementById('user-id').value = '';
        document.getElementById('user-active').checked = true;
    }
    
    // Use jQuery if available, otherwise try Bootstrap modal
    if (typeof $ !== 'undefined' && $.fn.modal) {
        $(modal).modal('show');
    } else if (typeof bootstrap !== 'undefined') {
        new bootstrap.Modal(modal).show();
    }
}

function editUser(userId) {
    openUserModal(userId);
}

function saveUser() {
    const form = document.getElementById('userForm');
    if (!form) return;
    
    const userId = document.getElementById('user-id').value;
    const userData = {
        username: document.getElementById('user-username').value,
        role: document.getElementById('user-role').value,
        full_name: document.getElementById('user-fullname').value,
        email: document.getElementById('user-email').value,
        phone: document.getElementById('user-phone').value,
        address: document.getElementById('user-address').value,
        is_active: document.getElementById('user-active').checked
    };
    
    // Validate form
    if (!userData.username || !userData.role || !userData.full_name || !userData.email) {
        showAlert('Please fill in all required fields', 'error');
        return;
    }
    
    const url = userId ? `/api/users/${userId}` : '/api/users';
    const method = userId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Close modal
            const modal = document.getElementById('userModal');
            if (typeof $ !== 'undefined' && $.fn.modal) {
                $(modal).modal('hide');
            } else if (typeof bootstrap !== 'undefined') {
                bootstrap.Modal.getInstance(modal)?.hide();
            }
            
            showAlert(userId ? 'User updated successfully' : 'User created successfully', 'success');
            loadUsers(currentUsersPage);
        } else {
            showAlert('Error: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error saving user:', error);
        showAlert('Error saving user', 'error');
    });
}

function resetPassword(userId) {
    const user = currentUsersData.find(u => u.id === userId);
    if (!user) return;
    
    document.getElementById('password-user-id').value = userId;
    document.getElementById('passwordForm').reset();
    
    // Hide current password field for admin reset
    const currentPasswordGroup = document.getElementById('current-password-group');
    const forceChangeGroup = document.getElementById('force-change-group');
    const currentPasswordField = document.getElementById('current-password');
    
    if (currentPasswordGroup) currentPasswordGroup.style.display = 'none';
    if (forceChangeGroup) forceChangeGroup.style.display = 'block';
    if (currentPasswordField) currentPasswordField.required = false;
    
    const modal = document.getElementById('passwordModal');
    if (typeof $ !== 'undefined' && $.fn.modal) {
        $(modal).modal('show');
    } else if (typeof bootstrap !== 'undefined') {
        new bootstrap.Modal(modal).show();
    }
}

function openPasswordModal() {
    // For self-service password change
    if (typeof currentUser !== 'undefined') {
        document.getElementById('password-user-id').value = currentUser.id;
    }
    document.getElementById('passwordForm').reset();
    
    // Show current password field for self-service
    const currentPasswordGroup = document.getElementById('current-password-group');
    const forceChangeGroup = document.getElementById('force-change-group');
    const currentPasswordField = document.getElementById('current-password');
    
    if (currentPasswordGroup) currentPasswordGroup.style.display = 'block';
    if (forceChangeGroup) forceChangeGroup.style.display = 'none';
    if (currentPasswordField) currentPasswordField.required = true;
    
    const modal = document.getElementById('passwordModal');
    if (typeof $ !== 'undefined' && $.fn.modal) {
        $(modal).modal('show');
    } else if (typeof bootstrap !== 'undefined') {
        new bootstrap.Modal(modal).show();
    }
}

function changePassword() {
    const userId = document.getElementById('password-user-id').value;
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const forceChange = document.getElementById('force-change').checked;
    
    // Validate passwords
    if (newPassword !== confirmPassword) {
        showAlert('New passwords do not match', 'error');
        return;
    }
    
    if (newPassword.length < 6) {
        showAlert('Password must be at least 6 characters', 'error');
        return;
    }
    
    const passwordData = {
        new_password: newPassword,
        force_change: forceChange
    };
    
    const currentPasswordGroup = document.getElementById('current-password-group');
    if (currentPasswordGroup && currentPasswordGroup.style.display !== 'none') {
        passwordData.current_password = currentPassword;
    }
    
    fetch(`/api/users/${userId}/password`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(passwordData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const modal = document.getElementById('passwordModal');
            if (typeof $ !== 'undefined' && $.fn.modal) {
                $(modal).modal('hide');
            } else if (typeof bootstrap !== 'undefined') {
                bootstrap.Modal.getInstance(modal)?.hide();
            }
            
            showAlert('Password changed successfully', 'success');
        } else {
            showAlert('Error: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error changing password:', error);
        showAlert('Error changing password', 'error');
    });
}

function deleteUser(userId) {
    const user = currentUsersData.find(u => u.id === userId);
    if (!user) return;
    
    if (confirm(`Are you sure you want to delete user "${user.username}"? This action cannot be undone.`)) {
        fetch(`/api/users/${userId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('User deleted successfully', 'success');
                loadUsers(currentUsersPage);
            } else if (data.requires_cascade) {
                showAlert(`Cannot delete user: Has dependencies (${data.dependencies.join(', ')})`, 'warning');
            } else {
                showAlert('Error: ' + (data.error || 'Unknown error'), 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting user:', error);
            showAlert('Error deleting user', 'error');
        });
    }
}

function exportUsers() {
    window.open('/api/users/export', '_blank');
}

// Profile Management Functions
function loadProfile() {
    fetch('/api/user/profile')
        .then(response => response.json())
        .then(data => {
            if (data.user) {
                const user = data.user;
                const setElementValue = (id, value) => {
                    const element = document.getElementById(id);
                    if (element) element.value = value || '';
                };
                
                setElementValue('profile-username', user.username);
                setElementValue('profile-role', (user.role || '').replace('_', ' ').toUpperCase());
                setElementValue('profile-fullname', user.full_name);
                setElementValue('profile-email', user.email);
                setElementValue('profile-phone', user.phone);
                setElementValue('profile-address', user.address);
                
                const setElementText = (id, value) => {
                    const element = document.getElementById(id);
                    if (element) element.textContent = value || '';
                };
                
                setElementText('profile-created', user.created_date ? new Date(user.created_date).toLocaleDateString() : 'Unknown');
                setElementText('profile-last-login', user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never');
                
                const statusElement = document.getElementById('profile-status');
                if (statusElement) {
                    statusElement.innerHTML = user.is_active ? 
                        '<span class="badge badge-success">Active</span>' : 
                        '<span class="badge badge-secondary">Inactive</span>';
                }
            }
        })
        .catch(error => {
            console.error('Error loading profile:', error);
            showAlert('Error loading profile', 'error');
        });
}

// System Information Functions
function loadSystemInfo() {
    fetch('/api/system/info')
        .then(response => response.json())
        .then(data => {
            // Update application info
            const setElementText = (id, value) => {
                const element = document.getElementById(id);
                if (element) element.textContent = value || '';
            };
            
            setElementText('app-version', data.version);
            setElementText('app-author', data.author);
            setElementText('app-copyright', data.copyright);
            setElementText('app-build-date', data.build_date);
            
            // Update system info
            if (data.system) {
                setElementText('sys-platform', data.system.platform);
                setElementText('sys-python', data.system.python_version);
                setElementText('sys-arch', data.system.architecture);
            }
            
            // Update database stats
            if (data.database_stats) {
                const statsContainer = document.getElementById('db-stats');
                if (statsContainer) {
                    statsContainer.innerHTML = '';
                    
                    Object.entries(data.database_stats).forEach(([table, count]) => {
                        const statCard = document.createElement('div');
                        statCard.className = 'col-md-4 mb-3';
                        statCard.innerHTML = `
                            <div class="card border-primary">
                                <div class="card-body text-center">
                                    <h5 class="card-title">${count}</h5>
                                    <p class="card-text">${table.charAt(0).toUpperCase() + table.slice(1)}</p>
                                </div>
                            </div>
                        `;
                        statsContainer.appendChild(statCard);
                    });
                }
            }
        })
        .catch(error => {
            console.error('Error loading system info:', error);
        });
}

// Profile form submission
document.addEventListener('DOMContentLoaded', function() {
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const profileData = {
                full_name: document.getElementById('profile-fullname')?.value || '',
                email: document.getElementById('profile-email')?.value || '',
                phone: document.getElementById('profile-phone')?.value || '',
                address: document.getElementById('profile-address')?.value || ''
            };
            
            if (typeof currentUser !== 'undefined' && currentUser.id) {
                fetch(`/api/users/${currentUser.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(profileData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showAlert('Profile updated successfully', 'success');
                        loadProfile(); // Reload profile data
                    } else {
                        showAlert('Error: ' + (data.error || 'Unknown error'), 'error');
                    }
                })
                .catch(error => {
                    console.error('Error updating profile:', error);
                    showAlert('Error updating profile', 'error');
                });
            } else {
                showAlert('Error: User information not available', 'error');
            }
        });
    }
});

// Enhanced switchTab function
(function() {
    // Store original switchTab function if it exists
    const originalSwitchTab = window.switchTab;
    
    window.switchTab = function(tabName) {
        // Call original function if it exists
        if (originalSwitchTab && typeof originalSwitchTab === 'function') {
            originalSwitchTab(tabName);
        } else {
            // Basic tab switching fallback
            document.querySelectorAll('.tab-pane').forEach(tab => {
                tab.style.display = 'none';
            });
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            
            const targetTab = document.getElementById(tabName + '-tab');
            if (targetTab) {
                targetTab.style.display = 'block';
            }
            
            const targetLink = document.querySelector(`[data-tab="${tabName}"]`);
            if (targetLink) {
                targetLink.classList.add('active');
            }
        }
        
        // Handle new tabs
        if (tabName === 'users') {
            setTimeout(() => loadUsers(), 100);
        } else if (tabName === 'profile') {
            setTimeout(() => loadProfile(), 100);
        } else if (tabName === 'about') {
            setTimeout(() => loadSystemInfo(), 100);
        }
    };
})();

// Alert function fallback
if (typeof showAlert !== 'function') {
    window.showAlert = function(message, type = 'info') {
        // Simple alert fallback
        alert(message);
    };
}

console.log('Enhanced User Management JavaScript loaded successfully');