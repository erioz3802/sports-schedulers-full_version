// Sports Schedulers - Leagues Management JavaScript
// Created by: Jose Ortiz - September 14, 2025

$(document).ready(function() {
    console.log('Leagues management JavaScript loaded');
    // Existing leagues functionality will go here
});


// ========================================================================
// PHASE 4.3: LEAGUE BILLING MANAGEMENT FUNCTIONALITY
// ========================================================================
// Created by: Jose Ortiz - September 14, 2025

// Global variables for billing management
let currentSelectedLeagueForBilling = null;
let billingStructures = [];
let billToEntities = [];
let editingBillingId = null;

// Initialize billing management on page load
$(document).ready(function() {
    initializeBillingManagement();
});

function initializeBillingManagement() {
    console.log('🔄 Initializing billing management...');
    
    // Load bill-to entities for dropdowns
    loadBillToEntitiesForBilling();
    
    // Populate league dropdown for billing
    populateLeagueDropdownForBilling();
    
    // Event handlers
    setupBillingEventHandlers();
}

function setupBillingEventHandlers() {
    // League selection for billing
    $('#billing-league-select').change(function() {
        const leagueId = $(this).val();
        currentSelectedLeagueForBilling = leagueId;
        
        if (leagueId) {
            $('#add-billing-btn').prop('disabled', false);
            loadBillingStructures(leagueId);
        } else {
            $('#add-billing-btn').prop('disabled', true);
            $('#billing-structures-container').hide();
        }
    });
    
    // Add billing structure button
    $('#add-billing-btn').click(function() {
        if (currentSelectedLeagueForBilling) {
            openBillingStructureModal('add');
        }
    });
    
    // Billing structure form submission
    $('#billingStructureForm').submit(function(e) {
        e.preventDefault();
        saveBillingStructure();
    });
    
    // Reset modal when hidden
    $('#billingStructureModal').on('hidden.bs.modal', function() {
        resetBillingStructureModal();
    });
}

function populateLeagueDropdownForBilling() {
    console.log('📋 Populating league dropdown for billing...');
    
    const $select = $('#billing-league-select');
    $select.empty().append('<option value="">Choose a league...</option>');
    
    // Fetch leagues
    $.ajax({
        url: '/api/leagues',
        method: 'GET',
        success: function(response) {
            if (response.success && response.leagues) {
                response.leagues.forEach(league => {
                    $select.append(`<option value="${league.id}">${league.name} (${league.sport})</option>`);
                });
            }
        },
        error: function() {
            showAlert('Error loading leagues for billing', 'danger');
        }
    });
}

function loadBillToEntitiesForBilling() {
    console.log('🏢 Loading bill-to entities for billing...');
    
    $.ajax({
        url: '/api/bill-to-entities',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                billToEntities = response.entities || [];
                populateBillToEntitiesDropdown();
                console.log(`✅ Loaded ${billToEntities.length} bill-to entities`);
            } else {
                showAlert('Failed to load bill-to entities', 'danger');
            }
        },
        error: function(xhr) {
            console.error('Error loading bill-to entities:', xhr);
            showAlert('Error loading bill-to entities', 'danger');
        }
    });
}

function populateBillToEntitiesDropdown() {
    const $select = $('#billing-entity-select');
    $select.empty().append('<option value="">Select entity to bill...</option>');
    
    billToEntities.forEach(entity => {
        $select.append(`<option value="${entity.id}">${entity.name}</option>`);
    });
}

function loadBillingStructures(leagueId) {
    console.log(`📊 Loading billing structures for league ${leagueId}...`);
    
    $.ajax({
        url: `/api/leagues/${leagueId}/billing`,
        method: 'GET',
        success: function(response) {
            if (response.success) {
                billingStructures = response.billing_structures || [];
                displayBillingStructures();
                console.log(`✅ Loaded ${billingStructures.length} billing structures`);
            } else {
                showAlert('Failed to load billing structures', 'danger');
            }
        },
        error: function(xhr) {
            console.error('Error loading billing structures:', xhr);
            if (xhr.status === 404) {
                // League exists but no billing structures yet
                billingStructures = [];
                displayBillingStructures();
            } else {
                showAlert('Error loading billing structures', 'danger');
            }
        }
    });
}

function displayBillingStructures() {
    const $container = $('#billing-structures-container');
    const $tbody = $('#billing-structures-table tbody');
    const $noMessage = $('#no-billing-message');
    
    $tbody.empty();
    
    if (billingStructures.length === 0) {
        $container.show();
        $noMessage.show();
        $('#billing-structures-table').hide();
    } else {
        $noMessage.hide();
        $('#billing-structures-table').show();
        $container.show();
        
        billingStructures.forEach(structure => {
            const row = createBillingStructureRow(structure);
            $tbody.append(row);
        });
    }
}

function createBillingStructureRow(structure) {
    const createdDate = new Date(structure.created_date).toLocaleDateString();
    const notes = structure.notes ? structure.notes.substring(0, 50) + (structure.notes.length > 50 ? '...' : '') : '-';
    
    return `
        <tr data-billing-id="${structure.id}">
            <td><strong>${structure.level_name}</strong></td>
            <td class="text-success"><strong>$${parseFloat(structure.bill_amount).toFixed(2)}</strong></td>
            <td>${structure.bill_to_name || 'Unknown Entity'}</td>
            <td>${createdDate}</td>
            <td><span class="text-muted small" title="${structure.notes || ''}">${notes}</span></td>
            <td>
                <button type="button" class="btn btn-sm btn-outline-primary me-1" 
                        onclick="editBillingStructure(${structure.id})" title="Edit">
                    <i class="fas fa-edit"></i>
                </button>
                <button type="button" class="btn btn-sm btn-outline-danger" 
                        onclick="deleteBillingStructure(${structure.id})" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `;
}

function openBillingStructureModal(mode, billingId = null) {
    editingBillingId = mode === 'edit' ? billingId : null;
    
    const modalTitle = mode === 'edit' ? 'Edit Billing Structure' : 'Add Billing Structure';
    $('#billingStructureModalLabel').text(modalTitle);
    
    if (mode === 'edit' && billingId) {
        const structure = billingStructures.find(s => s.id === billingId);
        if (structure) {
            $('#billing-level-name').val(structure.level_name);
            $('#billing-amount').val(parseFloat(structure.bill_amount).toFixed(2));
            $('#billing-entity-select').val(structure.bill_to_id);
            $('#billing-notes').val(structure.notes || '');
        }
    }
    
    $('#billingStructureModal').modal('show');
}

function resetBillingStructureModal() {
    $('#billingStructureForm')[0].reset();
    $('#billingStructureForm').removeClass('was-validated');
    editingBillingId = null;
}

function saveBillingStructure() {
    console.log('💾 Saving billing structure...');
    
    const form = document.getElementById('billingStructureForm');
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
    }
    
    const data = {
        level_name: $('#billing-level-name').val().trim(),
        bill_amount: parseFloat($('#billing-amount').val()).toFixed(2),
        bill_to_id: parseInt($('#billing-entity-select').val()),
        notes: $('#billing-notes').val().trim() || null
    };
    
    // Validation
    if (!data.level_name) {
        showAlert('Level name is required', 'danger');
        return;
    }
    
    if (isNaN(data.bill_amount) || parseFloat(data.bill_amount) <= 0) {
        showAlert('Valid bill amount is required', 'danger');
        return;
    }
    
    if (!data.bill_to_id) {
        showAlert('Bill-to entity selection is required', 'danger');
        return;
    }
    
    const url = editingBillingId 
        ? `/api/leagues/${currentSelectedLeagueForBilling}/billing/${editingBillingId}`
        : `/api/leagues/${currentSelectedLeagueForBilling}/billing`;
    
    const method = editingBillingId ? 'PUT' : 'POST';
    
    // Disable save button
    $('#save-billing-btn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Saving...');
    
    $.ajax({
        url: url,
        method: method,
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function(response) {
            if (response.success) {
                showAlert(response.message || 'Billing structure saved successfully', 'success');
                $('#billingStructureModal').modal('hide');
                loadBillingStructures(currentSelectedLeagueForBilling);
            } else {
                showAlert(response.error || 'Failed to save billing structure', 'danger');
            }
        },
        error: function(xhr) {
            console.error('Error saving billing structure:', xhr);
            let errorMessage = 'Error saving billing structure';
            
            if (xhr.responseJSON && xhr.responseJSON.error) {
                errorMessage = xhr.responseJSON.error;
            } else if (xhr.status === 409) {
                errorMessage = 'Billing structure already exists for this level in this league';
            }
            
            showAlert(errorMessage, 'danger');
        },
        complete: function() {
            $('#save-billing-btn').prop('disabled', false).html('<i class="fas fa-save"></i> Save Billing Structure');
        }
    });
}

function editBillingStructure(billingId) {
    console.log(`✏️ Editing billing structure ${billingId}...`);
    openBillingStructureModal('edit', billingId);
}

function deleteBillingStructure(billingId) {
    const structure = billingStructures.find(s => s.id === billingId);
    if (!structure) {
        showAlert('Billing structure not found', 'danger');
        return;
    }
    
    const confirmMessage = `Are you sure you want to delete the billing structure for "${structure.level_name}"?\n\nThis action cannot be undone.`;
    
    if (confirm(confirmMessage)) {
        console.log(`🗑️ Deleting billing structure ${billingId}...`);
        
        $.ajax({
            url: `/api/leagues/${currentSelectedLeagueForBilling}/billing/${billingId}`,
            method: 'DELETE',
            success: function(response) {
                if (response.success) {
                    showAlert(response.message || 'Billing structure deleted successfully', 'success');
                    loadBillingStructures(currentSelectedLeagueForBilling);
                } else {
                    showAlert(response.error || 'Failed to delete billing structure', 'danger');
                }
            },
            error: function(xhr) {
                console.error('Error deleting billing structure:', xhr);
                showAlert('Error deleting billing structure', 'danger');
            }
        });
    }
}

// Utility function for showing alerts (if not already defined)
if (typeof showAlert !== 'function') {
    function showAlert(message, type = 'info', duration = 5000) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Try to find a container for the alert
        let $container = $('.container-fluid').first();
        if ($container.length === 0) {
            $container = $('body');
        }
        
        $container.prepend(alertHtml);
        
        // Auto-dismiss after duration
        setTimeout(() => {
            $('.alert').first().alert('close');
        }, duration);
    }
}

console.log('✅ Phase 4.3 billing management JavaScript loaded successfully');

// ========================================================================
// END PHASE 4.3: LEAGUE BILLING MANAGEMENT FUNCTIONALITY
// ========================================================================


// ========================================================================
// PHASE 4.5B: FEE MANAGEMENT FRONTEND (Connects to Phase 4.5A APIs)
// ========================================================================
// Created by: Jose Ortiz - September 14, 2025

// Global variables for fee management
let currentSelectedLeagueForFees = null;
let feeStructures = [];
let editingFeeId = null;

// Initialize fee management on page load
$(document).ready(function() {
    initializeFeeManagement();
});

function initializeFeeManagement() {
    console.log('💰 Initializing fee management...');
    
    // Populate league dropdown for fees
    populateLeagueDropdownForFees();
    
    // Event handlers
    setupFeeEventHandlers();
}

function setupFeeEventHandlers() {
    // League selection for fees
    $('#fee-league-select').change(function() {
        const leagueId = $(this).val();
        currentSelectedLeagueForFees = leagueId;
        
        if (leagueId) {
            $('#add-fee-btn').prop('disabled', false);
            loadFeeStructures(leagueId);
        } else {
            $('#add-fee-btn').prop('disabled', true);
            $('#fee-structures-container').hide();
        }
    });
    
    // Add fee structure button
    $('#add-fee-btn').click(function() {
        if (currentSelectedLeagueForFees) {
            openFeeStructureModal('add');
        }
    });
    
    // Fee structure form submission
    $('#feeStructureForm').submit(function(e) {
        e.preventDefault();
        saveFeeStructure();
    });
    
    // Reset modal when hidden
    $('#feeStructureModal').on('hidden.bs.modal', function() {
        resetFeeStructureModal();
    });
}

function populateLeagueDropdownForFees() {
    console.log('📋 Populating league dropdown for fees...');
    
    const $select = $('#fee-league-select');
    $select.empty().append('<option value="">Choose a league...</option>');
    
    // Fetch leagues using existing endpoint
    $.ajax({
        url: '/api/leagues',
        method: 'GET',
        success: function(response) {
            if (response.success && response.leagues) {
                response.leagues.forEach(league => {
                    $select.append(`<option value="${league.id}">${league.name} (${league.sport})</option>`);
                });
                console.log(`✅ Loaded ${response.leagues.length} leagues for fee management`);
            }
        },
        error: function(xhr) {
            console.error('Error loading leagues for fee management:', xhr);
            showAlert('Error loading leagues for fee management', 'danger');
        }
    });
}

function loadFeeStructures(leagueId) {
    console.log(`💰 Loading fee structures for league ${leagueId}...`);
    
    $.ajax({
        url: `/api/leagues/${leagueId}/fees`,
        method: 'GET',
        success: function(response) {
            if (response.success) {
                feeStructures = response.fees || [];
                displayFeeStructures();
                console.log(`✅ Loaded ${feeStructures.length} fee structures`);
            } else {
                showAlert('Failed to load fee structures', 'danger');
            }
        },
        error: function(xhr) {
            console.error('Error loading fee structures:', xhr);
            if (xhr.status === 404) {
                // League exists but no fee structures yet
                feeStructures = [];
                displayFeeStructures();
            } else if (xhr.status === 401 || xhr.status === 403) {
                showAlert('Access denied. Admin privileges required for fee management.', 'warning');
            } else {
                showAlert('Error loading fee structures', 'danger');
            }
        }
    });
}

function displayFeeStructures() {
    const $container = $('#fee-structures-container');
    const $tbody = $('#fee-structures-table tbody');
    const $noMessage = $('#no-fees-message');
    
    $tbody.empty();
    
    if (feeStructures.length === 0) {
        $container.show();
        $noMessage.show();
        $('#fee-structures-table').hide();
    } else {
        $noMessage.hide();
        $('#fee-structures-table').show();
        $container.show();
        
        feeStructures.forEach(structure => {
            const row = createFeeStructureRow(structure);
            $tbody.append(row);
        });
    }
}

function createFeeStructureRow(structure) {
    const createdDate = new Date(structure.created_date).toLocaleDateString();
    const notes = structure.notes ? structure.notes.substring(0, 50) + (structure.notes.length > 50 ? '...' : '') : '-';
    
    return `
        <tr data-fee-id="${structure.id}">
            <td><strong>${structure.level_name}</strong></td>
            <td class="text-success"><strong>$${parseFloat(structure.official_fee).toFixed(2)}</strong></td>
            <td>${createdDate}</td>
            <td>${structure.created_by_username || 'System'}</td>
            <td><span class="text-muted small" title="${structure.notes || ''}">${notes}</span></td>
            <td>
                <button type="button" class="btn btn-sm btn-outline-primary me-1" 
                        onclick="editFeeStructure(${structure.id})" title="Edit">
                    <i class="fas fa-edit"></i>
                </button>
                <button type="button" class="btn btn-sm btn-outline-danger" 
                        onclick="deleteFeeStructure(${structure.id})" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `;
}

function openFeeStructureModal(mode, feeId = null) {
    editingFeeId = mode === 'edit' ? feeId : null;
    
    const modalTitle = mode === 'edit' ? 'Edit Fee Structure' : 'Add Fee Structure';
    $('#feeStructureModalLabel').text(modalTitle);
    
    if (mode === 'edit' && feeId) {
        const structure = feeStructures.find(s => s.id === feeId);
        if (structure) {
            $('#fee-level-name').val(structure.level_name);
            $('#fee-amount').val(parseFloat(structure.official_fee).toFixed(2));
            $('#fee-notes').val(structure.notes || '');
        }
    }
    
    $('#feeStructureModal').modal('show');
}

function resetFeeStructureModal() {
    $('#feeStructureForm')[0].reset();
    $('#feeStructureForm').removeClass('was-validated');
    editingFeeId = null;
}

function saveFeeStructure() {
    console.log('💾 Saving fee structure...');
    
    const form = document.getElementById('feeStructureForm');
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
    }
    
    const data = {
        level_name: $('#fee-level-name').val().trim(),
        official_fee: parseFloat($('#fee-amount').val()).toFixed(2),
        notes: $('#fee-notes').val().trim() || null
    };
    
    // Client-side validation
    if (!data.level_name) {
        showAlert('Level name is required', 'danger');
        return;
    }
    
    if (isNaN(data.official_fee) || parseFloat(data.official_fee) <= 0) {
        showAlert('Valid fee amount is required', 'danger');
        return;
    }
    
    const url = editingFeeId 
        ? `/api/leagues/${currentSelectedLeagueForFees}/fees/${editingFeeId}`
        : `/api/leagues/${currentSelectedLeagueForFees}/fees`;
    
    const method = editingFeeId ? 'PUT' : 'POST';
    
    // Disable save button
    $('#save-fee-btn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Saving...');
    
    $.ajax({
        url: url,
        method: method,
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function(response) {
            if (response.success) {
                showAlert(response.message || 'Fee structure saved successfully', 'success');
                $('#feeStructureModal').modal('hide');
                loadFeeStructures(currentSelectedLeagueForFees);
            } else {
                showAlert(response.error || 'Failed to save fee structure', 'danger');
            }
        },
        error: function(xhr) {
            console.error('Error saving fee structure:', xhr);
            let errorMessage = 'Error saving fee structure';
            
            if (xhr.responseJSON && xhr.responseJSON.error) {
                errorMessage = xhr.responseJSON.error;
            } else if (xhr.status === 409) {
                errorMessage = 'Fee structure already exists for this level in this league';
            } else if (xhr.status === 401 || xhr.status === 403) {
                errorMessage = 'Access denied. Admin privileges required.';
            }
            
            showAlert(errorMessage, 'danger');
        },
        complete: function() {
            $('#save-fee-btn').prop('disabled', false).html('<i class="fas fa-save"></i> Save Fee Structure');
        }
    });
}

function editFeeStructure(feeId) {
    console.log(`✏️ Editing fee structure ${feeId}...`);
    openFeeStructureModal('edit', feeId);
}

function deleteFeeStructure(feeId) {
    const structure = feeStructures.find(s => s.id === feeId);
    if (!structure) {
        showAlert('Fee structure not found', 'danger');
        return;
    }
    
    const confirmMessage = `Are you sure you want to delete the fee structure for "${structure.level_name}" ($${parseFloat(structure.official_fee).toFixed(2)})?\n\nThis action cannot be undone.`;
    
    if (confirm(confirmMessage)) {
        console.log(`🗑️ Deleting fee structure ${feeId}...`);
        
        $.ajax({
            url: `/api/leagues/${currentSelectedLeagueForFees}/fees/${feeId}`,
            method: 'DELETE',
            success: function(response) {
                if (response.success) {
                    showAlert(response.message || 'Fee structure deleted successfully', 'success');
                    loadFeeStructures(currentSelectedLeagueForFees);
                } else {
                    showAlert(response.error || 'Failed to delete fee structure', 'danger');
                }
            },
            error: function(xhr) {
                console.error('Error deleting fee structure:', xhr);
                let errorMessage = 'Error deleting fee structure';
                
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage = xhr.responseJSON.error;
                } else if (xhr.status === 401 || xhr.status === 403) {
                    errorMessage = 'Access denied. Admin privileges required.';
                }
                
                showAlert(errorMessage, 'danger');
            }
        });
    }
}

// Enhanced alert function with better UX
if (typeof showAlert !== 'function') {
    function showAlert(message, type = 'info', duration = 5000) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-triangle' : 'info-circle'}"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Try to find a container for the alert
        let $container = $('.container-fluid').first();
        if ($container.length === 0) {
            $container = $('body');
        }
        
        $container.prepend(alertHtml);
        
        // Auto-dismiss after duration
        setTimeout(() => {
            $('.alert').first().alert('close');
        }, duration);
    }
}

console.log('✅ Phase 4.5B fee management frontend loaded successfully');

// ========================================================================
// END PHASE 4.5B: FEE MANAGEMENT FRONTEND
// ========================================================================
