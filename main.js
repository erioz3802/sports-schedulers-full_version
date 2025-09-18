// ============================================================================
// Sports Schedulers - Complete Working Main JavaScript
// Author: Jose Ortiz
// Copyright: Jose Ortiz 2025
// ============================================================================

// Global APP_CONFIG initialization
window.APP_CONFIG = {
    API_BASE_URL: '/api',
    SOCKET_URL: window.location.origin,
    current_user: null,
    socket: null
};

// Google Maps callback - Properly defined
window.initializeGoogleMaps = function() {
    console.log('Google Maps API loaded successfully');
    window.googleMapsLoaded = true;
};

// Global variables
let currentTab = 'dashboard';
let currentUser = null;
let currentUsers = [];
let userToDelete = null;
let currentLeagues = [];
let currentFees = [];
let currentBillToEntities = [];
let selectedLeagueId = null;
let currentGames = [];
let selectedGames = new Set();
let currentLocations = [];

// ============================================================================
// CORE FUNCTIONS
// ============================================================================

function getCurrentUserRole() {
    if (window.APP_CONFIG && window.APP_CONFIG.current_user) {
        return window.APP_CONFIG.current_user.role;
    }
    return 'official';
}

function showTab(tabName) {
    console.log('Showing tab:', tabName);
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.style.display = 'none';
    });
    
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    const targetContent = document.getElementById(tabName + '-content');
    if (targetContent) {
        targetContent.style.display = 'block';
    }
    
    const targetNav = document.getElementById(tabName + '-nav');
    if (targetNav) {
        targetNav.classList.add('active');
    }
    
    const titleElement = document.getElementById('page-title');
    if (titleElement) {
        titleElement.textContent = tabName.charAt(0).toUpperCase() + tabName.slice(1);
    }
    
    currentTab = tabName;
    loadTabData(tabName);
}

function loadTabData(tabName) {
    switch(tabName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'games':
            loadGames();
            break;
        case 'officials':
            loadOfficials();
            break;
        case 'assignments':
            loadAssignments();
            break;
        case 'leagues':
            loadLeagues();
            break;
        case 'locations':
            loadLocations();
            break;
        case 'users':
            loadUsers();
            break;
        case 'reports':
            loadReports();
            break;
    }
}

function showSuccess(message) {
    console.log('Success:', message);
    alert('✅ ' + message);
}

function showError(message) {
    console.error('Error:', message);
    alert('❌ ' + message);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

// ============================================================================
// LEAGUES FUNCTIONALITY - COMPLETE WORKING IMPLEMENTATION
// ============================================================================

async function loadLeagues() {
    try {
        console.log('Loading leagues...');
        const response = await fetch('/api/leagues');
        
        if (!response.ok) {
            throw new Error(`Failed to load leagues: ${response.status}`);
        }
        
        const result = await response.json();
        const leagues = result.leagues || result;
        
        console.log('Leagues loaded:', leagues);
        currentLeagues = leagues;
        displayLeagues(leagues);
        
    } catch (error) {
        console.error('Error loading leagues:', error);
        showError('Failed to load leagues: ' + error.message);
        const tbody = document.getElementById('leaguesTableBody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Failed to load leagues</td></tr>';
        }
    }
}

function displayLeagues(leagues) {
    const tbody = document.getElementById('leaguesTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (!leagues || leagues.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No leagues found</td></tr>';
        return;
    }
    
    leagues.forEach(league => {
        const row = document.createElement('tr');
        row.style.cursor = 'pointer';
        row.onclick = () => selectLeague(league.id);
        
        row.innerHTML = `
            <td>
                <strong>${escapeHtml(league.name || '')}</strong>
                ${league.description ? `<br><small class="text-muted">${escapeHtml(league.description)}</small>` : ''}
            </td>
            <td>${escapeHtml(league.sport || '')}</td>
            <td>${escapeHtml(league.season || '')}</td>
            <td>${escapeHtml(league.level || '')}</td>
            <td>
                <span class="badge bg-${league.is_active ? 'success' : 'secondary'}">
                    ${league.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>${formatDate(league.start_date)}</td>
            <td>${formatDate(league.end_date)}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="event.stopPropagation(); editLeague(${league.id})" title="Edit">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-info" onclick="event.stopPropagation(); manageLeagueFees(${league.id})" title="Manage Fees">
                        <i class="bi bi-currency-dollar"></i>
                    </button>
                    <button class="btn btn-outline-success" onclick="event.stopPropagation(); manageLeagueBilling(${league.id})" title="Billing">
                        <i class="bi bi-receipt"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="event.stopPropagation(); deleteLeague(${league.id})" title="Delete">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

function selectLeague(leagueId) {
    selectedLeagueId = leagueId;
    
    document.querySelectorAll('#leaguesTableBody tr').forEach(row => {
        row.classList.remove('table-primary');
    });
    
    event.target.closest('tr').classList.add('table-primary');
    console.log('Selected league:', leagueId);
}

function showAddLeagueModal() {
    console.log('Showing add league modal');
    
    const existingModal = document.getElementById('addLeagueModal');
    if (existingModal) existingModal.remove();
    
    const modalHTML = `
        <div class="modal fade" id="addLeagueModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Add New League</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="addLeagueForm" onsubmit="createLeague(event)">
                            <div class="row">
                                <div class="col-md-6">
                                    <label for="leagueName" class="form-label">League Name *</label>
                                    <input type="text" class="form-control" id="leagueName" required maxlength="255">
                                </div>
                                <div class="col-md-6">
                                    <label for="leagueSport" class="form-label">Sport *</label>
                                    <select class="form-control" id="leagueSport" required>
                                        <option value="">Select Sport</option>
                                        <option value="Basketball">Basketball</option>
                                        <option value="Football">Football</option>
                                        <option value="Soccer">Soccer</option>
                                        <option value="Baseball">Baseball</option>
                                        <option value="Volleyball">Volleyball</option>
                                        <option value="Tennis">Tennis</option>
                                        <option value="Other">Other</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-md-4">
                                    <label for="leagueSeason" class="form-label">Season</label>
                                    <select class="form-control" id="leagueSeason">
                                        <option value="">Select Season</option>
                                        <option value="Fall">Fall</option>
                                        <option value="Winter">Winter</option>
                                        <option value="Spring">Spring</option>
                                        <option value="Summer">Summer</option>
                                    </select>
                                </div>
                                <div class="col-md-4">
                                    <label for="leagueLevel" class="form-label">Level</label>
                                    <input type="text" class="form-control" id="leagueLevel" maxlength="100">
                                </div>
                                <div class="col-md-4">
                                    <label for="leagueStatus" class="form-label">Status</label>
                                    <select class="form-control" id="leagueStatus">
                                        <option value="1">Active</option>
                                        <option value="0">Inactive</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-md-6">
                                    <label for="leagueStartDate" class="form-label">Start Date</label>
                                    <input type="date" class="form-control" id="leagueStartDate">
                                </div>
                                <div class="col-md-6">
                                    <label for="leagueEndDate" class="form-label">End Date</label>
                                    <input type="date" class="form-control" id="leagueEndDate">
                                </div>
                            </div>
                            <div class="mt-3">
                                <label for="leagueDescription" class="form-label">Description</label>
                                <textarea class="form-control" id="leagueDescription" rows="3" maxlength="500"></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" form="addLeagueForm" class="btn btn-primary">Create League</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    new bootstrap.Modal(document.getElementById('addLeagueModal')).show();
}

async function createLeague(event) {
    event.preventDefault();
    
    const data = {
        name: document.getElementById('leagueName').value.trim(),
        sport: document.getElementById('leagueSport').value,
        season: document.getElementById('leagueSeason').value,
        level: document.getElementById('leagueLevel').value.trim(),
        is_active: document.getElementById('leagueStatus').value === '1',
        start_date: document.getElementById('leagueStartDate').value || null,
        end_date: document.getElementById('leagueEndDate').value || null,
        description: document.getElementById('leagueDescription').value.trim()
    };
    
    if (!data.name || !data.sport) {
        showError('League name and sport are required');
        return;
    }
    
    try {
        const response = await fetch('/api/leagues', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to create league');
        }
        
        showSuccess('League created successfully');
        bootstrap.Modal.getInstance(document.getElementById('addLeagueModal')).hide();
        loadLeagues();
        
    } catch (error) {
        console.error('Error creating league:', error);
        showError('Failed to create league: ' + error.message);
    }
}

function editLeague(leagueId) {
    const league = currentLeagues.find(l => l.id === leagueId);
    if (!league) {
        showError('League not found');
        return;
    }
    
    const existingModal = document.getElementById('editLeagueModal');
    if (existingModal) existingModal.remove();
    
    const modalHTML = `
        <div class="modal fade" id="editLeagueModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Edit League - ${escapeHtml(league.name)}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="editLeagueForm" onsubmit="updateLeague(event, ${league.id})">
                            <div class="row">
                                <div class="col-md-6">
                                    <label for="editLeagueName" class="form-label">League Name *</label>
                                    <input type="text" class="form-control" id="editLeagueName" required maxlength="255" value="${escapeHtml(league.name || '')}">
                                </div>
                                <div class="col-md-6">
                                    <label for="editLeagueSport" class="form-label">Sport *</label>
                                    <select class="form-control" id="editLeagueSport" required>
                                        <option value="">Select Sport</option>
                                        <option value="Basketball" ${league.sport === 'Basketball' ? 'selected' : ''}>Basketball</option>
                                        <option value="Football" ${league.sport === 'Football' ? 'selected' : ''}>Football</option>
                                        <option value="Soccer" ${league.sport === 'Soccer' ? 'selected' : ''}>Soccer</option>
                                        <option value="Baseball" ${league.sport === 'Baseball' ? 'selected' : ''}>Baseball</option>
                                        <option value="Volleyball" ${league.sport === 'Volleyball' ? 'selected' : ''}>Volleyball</option>
                                        <option value="Tennis" ${league.sport === 'Tennis' ? 'selected' : ''}>Tennis</option>
                                        <option value="Other" ${league.sport === 'Other' ? 'selected' : ''}>Other</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-md-4">
                                    <label for="editLeagueSeason" class="form-label">Season</label>
                                    <select class="form-control" id="editLeagueSeason">
                                        <option value="">Select Season</option>
                                        <option value="Fall" ${league.season === 'Fall' ? 'selected' : ''}>Fall</option>
                                        <option value="Winter" ${league.season === 'Winter' ? 'selected' : ''}>Winter</option>
                                        <option value="Spring" ${league.season === 'Spring' ? 'selected' : ''}>Spring</option>
                                        <option value="Summer" ${league.season === 'Summer' ? 'selected' : ''}>Summer</option>
                                    </select>
                                </div>
                                <div class="col-md-4">
                                    <label for="editLeagueLevel" class="form-label">Level</label>
                                    <input type="text" class="form-control" id="editLeagueLevel" maxlength="100" value="${escapeHtml(league.level || '')}">
                                </div>
                                <div class="col-md-4">
                                    <label for="editLeagueStatus" class="form-label">Status</label>
                                    <select class="form-control" id="editLeagueStatus">
                                        <option value="1" ${league.is_active ? 'selected' : ''}>Active</option>
                                        <option value="0" ${!league.is_active ? 'selected' : ''}>Inactive</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-md-6">
                                    <label for="editLeagueStartDate" class="form-label">Start Date</label>
                                    <input type="date" class="form-control" id="editLeagueStartDate" value="${league.start_date || ''}">
                                </div>
                                <div class="col-md-6">
                                    <label for="editLeagueEndDate" class="form-label">End Date</label>
                                    <input type="date" class="form-control" id="editLeagueEndDate" value="${league.end_date || ''}">
                                </div>
                            </div>
                            <div class="mt-3">
                                <label for="editLeagueDescription" class="form-label">Description</label>
                                <textarea class="form-control" id="editLeagueDescription" rows="3" maxlength="500">${escapeHtml(league.description || '')}</textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" form="editLeagueForm" class="btn btn-primary">Update League</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    new bootstrap.Modal(document.getElementById('editLeagueModal')).show();
}

async function updateLeague(event, leagueId) {
    event.preventDefault();
    
    const data = {
        name: document.getElementById('editLeagueName').value.trim(),
        sport: document.getElementById('editLeagueSport').value,
        season: document.getElementById('editLeagueSeason').value,
        level: document.getElementById('editLeagueLevel').value.trim(),
        is_active: document.getElementById('editLeagueStatus').value === '1',
        start_date: document.getElementById('editLeagueStartDate').value || null,
        end_date: document.getElementById('editLeagueEndDate').value || null,
        description: document.getElementById('editLeagueDescription').value.trim()
    };
    
    if (!data.name || !data.sport) {
        showError('League name and sport are required');
        return;
    }
    
    try {
        const response = await fetch(`/api/leagues/${leagueId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to update league');
        }
        
        showSuccess('League updated successfully');
        bootstrap.Modal.getInstance(document.getElementById('editLeagueModal')).hide();
        loadLeagues();
        
    } catch (error) {
        console.error('Error updating league:', error);
        showError('Failed to update league: ' + error.message);
    }
}

async function manageLeagueFees(leagueId) {
    console.log('Managing fees for league:', leagueId);
    
    try {
        const response = await fetch(`/api/leagues/${leagueId}/fees`);
        if (!response.ok) throw new Error('Failed to load fees');
        
        const result = await response.json();
        const fees = result.fees || [];
        const leagueName = result.league_name || 'Unknown League';
        
        currentFees = fees;
        showFeeManagementModal(leagueId, leagueName, fees);
        
    } catch (error) {
        console.error('Error loading fees:', error);
        showError('Failed to load fees: ' + error.message);
    }
}

function showFeeManagementModal(leagueId, leagueName, fees) {
    const existingModal = document.getElementById('feeManagementModal');
    if (existingModal) existingModal.remove();
    
    const feesTableRows = fees.map(fee => `
        <tr>
            <td>${escapeHtml(fee.level_name)}</td>
            <td>$${parseFloat(fee.official_fee).toFixed(2)}</td>
            <td>${escapeHtml(fee.notes || '')}</td>
            <td>${formatDate(fee.created_date)}</td>
            <td>
                <button class="btn btn-outline-danger btn-sm" onclick="deleteFee(${leagueId}, '${escapeHtml(fee.level_name)}')">
                    <i class="bi bi-trash"></i> Delete
                </button>
            </td>
        </tr>
    `).join('');
    
    const modalHTML = `
        <div class="modal fade" id="feeManagementModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Fee Management - ${escapeHtml(leagueName)}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h6>Current Fee Structure</h6>
                            <button class="btn btn-primary btn-sm" onclick="showAddFeeForm(${leagueId})">
                                <i class="bi bi-plus-circle"></i> Add Fee
                            </button>
                        </div>
                        
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Level</th>
                                        <th>Official Fee</th>
                                        <th>Notes</th>
                                        <th>Created</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${feesTableRows || '<tr><td colspan="5" class="text-center text-muted">No fees configured</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                        
                        <div id="addFeeForm" style="display: none;" class="mt-4 p-3 border rounded bg-light">
                            <h6>Add New Fee</h6>
                            <form onsubmit="addNewFee(event, ${leagueId})">
                                <div class="row">
                                    <div class="col-md-4">
                                        <label for="newFeeLevel" class="form-label">Level Name</label>
                                        <input type="text" class="form-control" id="newFeeLevel" required maxlength="100">
                                    </div>
                                    <div class="col-md-4">
                                        <label for="newFeeAmount" class="form-label">Official Fee ($)</label>
                                        <input type="number" class="form-control" id="newFeeAmount" step="0.01" min="0.01" max="999999.99" required>
                                    </div>
                                    <div class="col-md-4">
                                        <label for="newFeeNotes" class="form-label">Notes (Optional)</label>
                                        <input type="text" class="form-control" id="newFeeNotes" maxlength="500">
                                    </div>
                                </div>
                                <div class="mt-3">
                                    <button type="submit" class="btn btn-success btn-sm">Save Fee</button>
                                    <button type="button" class="btn btn-secondary btn-sm" onclick="hideFeeForm()">Cancel</button>
                                </div>
                            </form>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    new bootstrap.Modal(document.getElementById('feeManagementModal')).show();
}

function showAddFeeForm(leagueId) {
    const form = document.getElementById('addFeeForm');
    if (form) {
        form.style.display = 'block';
        document.getElementById('newFeeLevel').focus();
    }
}

function hideFeeForm() {
    const form = document.getElementById('addFeeForm');
    if (form) {
        form.style.display = 'none';
        form.querySelector('form').reset();
    }
}

async function addNewFee(event, leagueId) {
    event.preventDefault();
    
    const levelName = document.getElementById('newFeeLevel').value.trim();
    const amount = document.getElementById('newFeeAmount').value;
    const notes = document.getElementById('newFeeNotes').value.trim();
    
    if (!levelName || !amount) {
        showError('Level name and fee amount are required');
        return;
    }
    
    try {
        const response = await fetch(`/api/leagues/${leagueId}/fees`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                level_name: levelName,
                official_fee: parseFloat(amount),
                notes: notes
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to create fee');
        }
        
        showSuccess('Fee created successfully');
        
        // Close the modal properly
        const modal = bootstrap.Modal.getInstance(document.getElementById('feeManagementModal'));
        if (modal) {
            modal.hide();
        }
        
        // Small delay then reload leagues to refresh the page
        setTimeout(() => {
            loadLeagues();
        }, 300);
        
    } catch (error) {
        console.error('Error creating fee:', error);
        showError('Failed to create fee: ' + error.message);
    }
}

async function deleteFee(leagueId, levelName) {
    if (!confirm(`Are you sure you want to delete the fee for ${levelName}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/leagues/${leagueId}/fees/${encodeURIComponent(levelName)}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to delete fee');
        }
        
        showSuccess('Fee deleted successfully');
        manageLeagueFees(leagueId);
        
    } catch (error) {
        console.error('Error deleting fee:', error);
        showError('Failed to delete fee: ' + error.message);
    }
}

async function manageLeagueBilling(leagueId) {
    console.log('Managing billing for league:', leagueId);
    
    try {
        // Load bill-to entities and league info
        const [entitiesResponse, leagueResponse] = await Promise.all([
            fetch('/api/bill-to-entities'),
            fetch(`/api/leagues/${leagueId}`)
        ]);
        
        if (!entitiesResponse.ok || !leagueResponse.ok) {
            throw new Error('Failed to load billing data');
        }
        
        const entitiesResult = await entitiesResponse.json();
        const leagueResult = await leagueResponse.json();
        
        currentBillToEntities = entitiesResult.entities || [];
        const league = leagueResult.league || leagueResult;
        const leagueName = league ? league.name : 'Unknown League';
        
        showBillingManagementModal(leagueId, leagueName);
        
    } catch (error) {
        console.error('Error loading billing data:', error);
        showError('Failed to load billing data: ' + error.message);
    }
}

/**
 * Show billing management modal - Complete implementation
 */
function showBillingManagementModal(leagueId, leagueName) {
    const existingModal = document.getElementById('billingManagementModal');
    if (existingModal) existingModal.remove();
    
    const entitiesTableRows = currentBillToEntities.map(entity => `
        <tr>
            <td><strong>${escapeHtml(entity.name)}</strong></td>
            <td>${escapeHtml(entity.contact_person || 'N/A')}</td>
            <td>${escapeHtml(entity.email || 'N/A')}</td>
            <td>${escapeHtml(entity.phone || 'N/A')}</td>
            <td>
                <span class="badge bg-${entity.is_active ? 'success' : 'secondary'}">
                    ${entity.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="editBillToEntity(${entity.id})" title="Edit">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-info" onclick="viewEntityDetails(${entity.id})" title="Details">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteBillToEntity(${entity.id})" title="Delete">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    const modalHTML = `
        <div class="modal fade" id="billingManagementModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Billing Management - ${escapeHtml(leagueName)}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle"></i>
                            <strong>Billing Management:</strong> Manage bill-to entities and configure billing amounts separate from official fees.
                        </div>
                        
                        <!-- Bill-To Entities Section -->
                        <div class="card mb-4">
                            <div class="card-header">
                                <div class="d-flex justify-content-between align-items-center">
                                    <h6 class="mb-0"><i class="bi bi-building"></i> Bill-To Entities</h6>
                                    <button class="btn btn-primary btn-sm" onclick="showAddBillToEntityForm()">
                                        <i class="bi bi-plus-circle"></i> Add Entity
                                    </button>
                                </div>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-striped table-hover">
                                        <thead class="table-dark">
                                            <tr>
                                                <th>Entity Name</th>
                                                <th>Contact Person</th>
                                                <th>Email</th>
                                                <th>Phone</th>
                                                <th>Status</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody id="billToEntitiesTableBody">
                                            ${entitiesTableRows || '<tr><td colspan="6" class="text-center text-muted">No billing entities found</td></tr>'}
                                        </tbody>
                                    </table>
                                </div>
                                
                                <!-- Add Entity Form -->
                                <div id="addBillToEntityForm" style="display: none;" class="mt-4 p-4 border rounded bg-light">
                                    <h6><i class="bi bi-plus-circle"></i> Add New Bill-To Entity</h6>
                                    <form onsubmit="createBillToEntity(event)">
                                        <div class="row">
                                            <div class="col-md-6">
                                                <label for="billToEntityName" class="form-label">Entity Name *</label>
                                                <input type="text" class="form-control" id="billToEntityName" required maxlength="255">
                                            </div>
                                            <div class="col-md-6">
                                                <label for="billToEntityContact" class="form-label">Contact Person</label>
                                                <input type="text" class="form-control" id="billToEntityContact" maxlength="255">
                                            </div>
                                        </div>
                                        <div class="row mt-3">
                                            <div class="col-md-4">
                                                <label for="billToEntityEmail" class="form-label">Email</label>
                                                <input type="email" class="form-control" id="billToEntityEmail" maxlength="255">
                                            </div>
                                            <div class="col-md-4">
                                                <label for="billToEntityPhone" class="form-label">Phone</label>
                                                <input type="text" class="form-control" id="billToEntityPhone" maxlength="20">
                                            </div>
                                            <div class="col-md-4">
                                                <label for="billToEntityTaxId" class="form-label">Tax ID</label>
                                                <input type="text" class="form-control" id="billToEntityTaxId" maxlength="50">
                                            </div>
                                        </div>
                                        <div class="row mt-3">
                                            <div class="col-md-8">
                                                <label for="billToEntityAddress" class="form-label">Address</label>
                                                <input type="text" class="form-control" id="billToEntityAddress" maxlength="500">
                                            </div>
                                            <div class="col-md-2">
                                                <label for="billToEntityCity" class="form-label">City</label>
                                                <input type="text" class="form-control" id="billToEntityCity" maxlength="100">
                                            </div>
                                            <div class="col-md-1">
                                                <label for="billToEntityState" class="form-label">State</label>
                                                <input type="text" class="form-control" id="billToEntityState" maxlength="2" placeholder="TX">
                                            </div>
                                            <div class="col-md-1">
                                                <label for="billToEntityZip" class="form-label">ZIP</label>
                                                <input type="text" class="form-control" id="billToEntityZip" maxlength="10">
                                            </div>
                                        </div>
                                        <div class="mt-3">
                                            <label for="billToEntityNotes" class="form-label">Notes</label>
                                            <textarea class="form-control" id="billToEntityNotes" rows="2" maxlength="500"></textarea>
                                        </div>
                                        <div class="mt-4">
                                            <button type="submit" class="btn btn-success">
                                                <i class="bi bi-check-circle"></i> Create Entity
                                            </button>
                                            <button type="button" class="btn btn-secondary ms-2" onclick="hideBillToEntityForm()">
                                                <i class="bi bi-x-circle"></i> Cancel
                                            </button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Billing Instructions -->
                        <div class="alert alert-warning">
                            <i class="bi bi-lightbulb"></i>
                            <strong>Next Steps:</strong> After creating bill-to entities, you can set up specific billing amounts per league level that may differ from official fees.
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="bi bi-x-circle"></i> Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    new bootstrap.Modal(document.getElementById('billingManagementModal')).show();
}

/**
 * Show add bill-to entity form
 */
function showAddBillToEntityForm() {
    const form = document.getElementById('addBillToEntityForm');
    if (form) {
        form.style.display = 'block';
        document.getElementById('billToEntityName').focus();
    }
}

/**
 * Hide bill-to entity form
 */
function hideBillToEntityForm() {
    const form = document.getElementById('addBillToEntityForm');
    if (form) {
        form.style.display = 'none';
        form.querySelector('form').reset();
    }
}

/**
 * Create new bill-to entity
 */
async function createBillToEntity(event) {
    event.preventDefault();
    
    const data = {
        name: document.getElementById('billToEntityName').value.trim(),
        contact_person: document.getElementById('billToEntityContact').value.trim(),
        email: document.getElementById('billToEntityEmail').value.trim(),
        phone: document.getElementById('billToEntityPhone').value.trim(),
        tax_id: document.getElementById('billToEntityTaxId').value.trim(),
        address: document.getElementById('billToEntityAddress').value.trim(),
        city: document.getElementById('billToEntityCity').value.trim(),
        state: document.getElementById('billToEntityState').value.trim(),
        zip_code: document.getElementById('billToEntityZip').value.trim(),
        notes: document.getElementById('billToEntityNotes').value.trim()
    };
    
    if (!data.name) {
        showError('Entity name is required');
        return;
    }
    
    try {
        const response = await fetch('/api/bill-to-entities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to create bill-to entity');
        }
        
        showSuccess('Bill-to entity created successfully');
        hideBillToEntityForm();
        
        // Refresh the billing management modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('billingManagementModal'));
        if (modal) {
            modal.hide();
        }
        
        // Small delay then reopen with updated data
        setTimeout(() => {
            if (selectedLeagueId) {
                manageLeagueBilling(selectedLeagueId);
            }
        }, 300);
        
    } catch (error) {
        console.error('Error creating bill-to entity:', error);
        showError('Failed to create bill-to entity: ' + error.message);
    }
}

/**
 * Edit bill-to entity with modal form
 */
function editBillToEntity(entityId) {
    console.log('Edit bill-to entity:', entityId);
    
    fetch('/api/bill-to-entities')
    .then(response => {
        if (!response.ok) throw new Error('Failed to fetch entities');
        return response.json();
    })
    .then(data => {
        const entity = data.entities.find(e => e.id === entityId);
        if (!entity) {
            showError('Entity not found');
            return;
        }
        
        // Create and show modal
        const modalHtml = `
            <div class="modal fade" id="editBillToEntityModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Edit Bill-To Entity</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <form id="editBillToEntityForm">
                            <div class="modal-body">
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label for="editEntityName" class="form-label">Entity Name *</label>
                                        <input type="text" class="form-control" id="editEntityName" value="${escapeHtml(entity.name)}" required>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <label for="editContactPerson" class="form-label">Contact Person *</label>
                                        <input type="text" class="form-control" id="editContactPerson" value="${escapeHtml(entity.contact_person)}" required>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label for="editEmail" class="form-label">Email</label>
                                        <input type="email" class="form-control" id="editEmail" value="${escapeHtml(entity.email || '')}">
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <label for="editPhone" class="form-label">Phone</label>
                                        <input type="text" class="form-control" id="editPhone" value="${escapeHtml(entity.phone || '')}">
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label for="editAddress" class="form-label">Address</label>
                                    <input type="text" class="form-control" id="editAddress" value="${escapeHtml(entity.address || '')}">
                                </div>
                                <div class="row">
                                    <div class="col-md-4 mb-3">
                                        <label for="editCity" class="form-label">City</label>
                                        <input type="text" class="form-control" id="editCity" value="${escapeHtml(entity.city || '')}">
                                    </div>
                                    <div class="col-md-4 mb-3">
                                        <label for="editState" class="form-label">State</label>
                                        <input type="text" class="form-control" id="editState" value="${escapeHtml(entity.state || '')}">
                                    </div>
                                    <div class="col-md-4 mb-3">
                                        <label for="editZip" class="form-label">Zip Code</label>
                                        <input type="text" class="form-control" id="editZip" value="${escapeHtml(entity.zip_code || '')}">
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label for="editTaxId" class="form-label">Tax ID</label>
                                    <input type="text" class="form-control" id="editTaxId" value="${escapeHtml(entity.tax_id || '')}">
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                <button type="submit" class="btn btn-primary">Update Entity</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('editBillToEntityModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('editBillToEntityModal'));
        modal.show();
        
        // Handle form submission
        document.getElementById('editBillToEntityForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                name: document.getElementById('editEntityName').value.trim(),
                contact_person: document.getElementById('editContactPerson').value.trim(),
                email: document.getElementById('editEmail').value.trim(),
                phone: document.getElementById('editPhone').value.trim(),
                address: document.getElementById('editAddress').value.trim(),
                city: document.getElementById('editCity').value.trim(),
                state: document.getElementById('editState').value.trim(),
                zip_code: document.getElementById('editZip').value.trim(),
                tax_id: document.getElementById('editTaxId').value.trim()
            };
            
            if (!formData.name) {
                showError('Entity name is required');
                return;
            }
            
            if (!formData.contact_person) {
                showError('Contact person is required');
                return;
            }
            
            fetch(`/api/bill-to-entities/${entityId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })
            .then(response => {
                if (!response.ok) throw new Error('Failed to update entity');
                return response.json();
            })
            .then(result => {
                modal.hide();
                showSuccess('Entity updated successfully');
                if (typeof loadBillToEntities === 'function') {
                    loadBillToEntities();
                } else {
                    window.location.reload();
                }
            })
            .catch(error => {
                console.error('Error updating entity:', error);
                showError('Failed to update entity: ' + error.message);
            });
        });
        
        // Clean up modal when hidden
        document.getElementById('editBillToEntityModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    })
    .catch(error => {
        console.error('Error editing entity:', error);
        showError('Failed to edit entity: ' + error.message);
    });
}

/**
 * View entity details
 */
function viewEntityDetails(entityId) {
    const entity = currentBillToEntities.find(e => e.id === entityId);
    if (!entity) {
        showError('Entity not found');
        return;
    }
    
    const addressParts = [entity.address, entity.city, entity.state, entity.zip_code].filter(x => x);
    const fullAddress = addressParts.join(', ');
    
    const detailsHTML = `
        <div class="modal fade" id="entityDetailsModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Entity Details - ${escapeHtml(entity.name)}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <table class="table">
                            <tr><th>Name:</th><td>${escapeHtml(entity.name)}</td></tr>
                            <tr><th>Contact Person:</th><td>${escapeHtml(entity.contact_person || 'N/A')}</td></tr>
                            <tr><th>Email:</th><td>${escapeHtml(entity.email || 'N/A')}</td></tr>
                            <tr><th>Phone:</th><td>${escapeHtml(entity.phone || 'N/A')}</td></tr>
                            <tr><th>Tax ID:</th><td>${escapeHtml(entity.tax_id || 'N/A')}</td></tr>
                            <tr><th>Address:</th><td>${escapeHtml(fullAddress || 'N/A')}</td></tr>
                            <tr><th>Status:</th><td>
                                <span class="badge bg-${entity.is_active ? 'success' : 'secondary'}">
                                    ${entity.is_active ? 'Active' : 'Inactive'}
                                </span>
                            </td></tr>
                            <tr><th>Notes:</th><td>${escapeHtml(entity.notes || 'None')}</td></tr>
                            <tr><th>Created:</th><td>${formatDate(entity.created_date)}</td></tr>
                        </table>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', detailsHTML);
    new bootstrap.Modal(document.getElementById('entityDetailsModal')).show();
}

/**
 * Delete bill-to entity
 */
// Enhanced delete function with better error handling
async function deleteBillToEntity(entityId) {
    console.log('Deleting bill-to entity:', entityId);
    
    if (!confirm('Are you sure you want to delete this bill-to entity?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/bill-to-entities/${entityId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            let errorMessage = 'Failed to delete entity';
            
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (jsonError) {
                // If response isn't JSON, use status text
                errorMessage = response.statusText || errorMessage;
            }
            
            throw new Error(errorMessage);
        }
        
        const result = await response.json();
        showSuccess(result.message || 'Entity deleted successfully');
        // Refresh the bill-to entities list
        if (typeof loadBillToEntities === 'function') {
            loadBillToEntities();
        } else {
            // Alternative refresh method
            window.location.reload();
        }
        
    } catch (error) {
        console.error('Error deleting entity:', error);
        showError('Failed to delete entity: ' + error.message);
    }
}

async function deleteLeague(leagueId) {
    const league = currentLeagues.find(l => l.id === leagueId);
    if (!league) return;
    
    if (!confirm(`Are you sure you want to delete the league "${league.name}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/leagues/${leagueId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to delete league');
        }
        
        showSuccess('League deleted successfully');
        loadLeagues();
        
    } catch (error) {
        console.error('Error deleting league:', error);
        showError('Failed to delete league: ' + error.message);
    }
}

// ============================================================================
// PLACEHOLDER FUNCTIONS FOR OTHER TABS
// ============================================================================

function loadDashboard() { console.log('Loading dashboard...'); }
function loadGames() { console.log('Loading games...'); }
function loadOfficials() { console.log('Loading officials...'); }
function loadAssignments() { console.log('Loading assignments...'); }
function loadLocations() { console.log('Loading locations...'); }
function loadUsers() { console.log('Loading users...'); }
function loadReports() { console.log('Loading reports...'); }

// ============================================================================
// INITIALIZATION
// ============================================================================

async function initializeApp() {
    try {
        console.log('Initializing Sports Schedulers application...');
        await loadCurrentUser();
        showTab('dashboard');
        console.log('Application initialized successfully');
    } catch (error) {
        console.error('App initialization failed:', error);
    }
}

async function loadCurrentUser() {
    try {
        const response = await fetch('/api/session');
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                APP_CONFIG.current_user = data.session;
                console.log('Current user loaded:', data.session);
                
                if (data.session.role === 'official' && window.location.pathname === '/') {
                    window.location.href = '/official';
                    return;
                }
            }
        }
    } catch (error) {
        console.error('Failed to load user session:', error);
    }
}

async function logout() {
    try {
        const response = await fetch('/api/auth/logout', { method: 'POST' });
        if (response.ok) {
            window.location.href = '/login';
        } else {
            showError('Logout failed');
        }
    } catch (error) {
        console.error('Logout error:', error);
        showError('Logout failed');
    }
}

document.addEventListener('DOMContentLoaded', initializeApp);

console.log('Sports Schedulers complete working main.js loaded successfully!');

// ============================================================================
// MODAL CLEANUP FUNCTIONS
// ============================================================================

/**
 * Force close all modals - Emergency cleanup
 */
function forceCloseAllModals() {
    // Remove all modal backdrops
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
        backdrop.remove();
    });
    
    // Hide all modals
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
        modal.classList.remove('show');
        modal.setAttribute('aria-hidden', 'true');
        modal.removeAttribute('aria-modal');
        
        // Try to get Bootstrap modal instance and hide it
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) {
            bsModal.hide();
        }
    });
    
    // Remove modal-open class from body
    document.body.classList.remove('modal-open');
    document.body.style.removeProperty('padding-right');
    document.body.style.removeProperty('overflow');
    
    console.log('All modals force closed');
}

/**
 * Add escape key handler to close modals
 */
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        forceCloseAllModals();
    }
});
