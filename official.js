/**
 * Sports Schedulers - Official Dashboard JavaScript
 * Author: Jose Ortiz
 * Copyright: 2025
 */

// Global configuration for official dashboard
window.OFFICIAL_CONFIG = {
    API_BASE_URL: '/api',
    current_user: null,
    games: [],
    assignments: []
};

// Initialize official dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeOfficialDashboard();
});

async function initializeOfficialDashboard() {
    console.log('Sports Schedulers Official Dashboard - Initializing...');
    
    try {
        await loadCurrentUser();
        await loadOfficialDashboard();
        updateCurrentDate();
        console.log('Sports Schedulers Official Dashboard - Ready!');
    } catch (error) {
        console.error('Failed to initialize official dashboard:', error);
        if (error.response && error.response.status === 401) {
            logout();
        }
    }
}

async function loadCurrentUser() {
    try {
        const response = await axios.get('/api/auth/me');
        OFFICIAL_CONFIG.current_user = response.data.user;
        
        document.getElementById('user-name').textContent = 
            response.data.user.full_name || response.data.user.username;
        
        if (response.data.user.role !== 'official') {
            console.warn('Non-official user accessing official dashboard');
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Failed to load user:', error);
        throw error;
    }
}

async function loadOfficialDashboard() {
    try {
        await Promise.all([
            loadOfficialGames(),
            loadOfficialStats()
        ]);
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

async function loadOfficialGames() {
    try {
        const response = await axios.get('/api/officials/my-games');
        OFFICIAL_CONFIG.games = response.data.games || [];
        
        updateUpcomingGamesList();
        updateMyGamesList();
    } catch (error) {
        console.error('Failed to load games:', error);
        showError('Failed to load your games');
    }
}

async function loadOfficialStats() {
    try {
        const response = await axios.get('/api/officials/my-stats');
        const stats = response.data.stats || {};
        
        document.getElementById('upcoming-games-count').textContent = stats.upcoming || 0;
        document.getElementById('completed-games-count').textContent = stats.completed || 0;
        document.getElementById('this-month-count').textContent = stats.this_month || 0;
        document.getElementById('total-games-count').textContent = stats.total || 0;
    } catch (error) {
        console.error('Failed to load stats:', error);
        document.getElementById('upcoming-games-count').textContent = '0';
        document.getElementById('completed-games-count').textContent = '0';
        document.getElementById('this-month-count').textContent = '0';
        document.getElementById('total-games-count').textContent = '0';
    }
}

function updateUpcomingGamesList() {
    const container = document.getElementById('upcoming-games-list');
    const upcomingGames = OFFICIAL_CONFIG.games
        .filter(game => new Date(game.date) >= new Date())
        .sort((a, b) => new Date(a.date) - new Date(b.date))
        .slice(0, 5);
    
    if (upcomingGames.length === 0) {
        container.innerHTML = `
            <div class="text-center p-4 text-muted">
                <i class="bi bi-calendar-x fs-1 mb-3 d-block"></i>
                <p>No upcoming games scheduled</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = upcomingGames.map(game => {
        const officialsInfo = getOfficialsDisplayInfo(game);
        const statusColor = getResponseStatusColor(game.response);
        
        return `
            <div class="game-item clickable" onclick="showGameDetails(${game.id})">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="flex-grow-1">
                        <div class="fw-bold">${escapeHtml(game.home_team)} vs ${escapeHtml(game.away_team)}</div>
                        <div class="text-muted small">
                            <i class="bi bi-calendar me-1"></i>
                            ${formatDate(game.date)} at ${formatTime(game.time)}
                        </div>
                        <div class="text-muted small">
                            <i class="bi bi-geo-alt me-1"></i>
                            ${escapeHtml(game.location || 'TBD')}
                        </div>
                        <div class="text-muted small mt-1">
                            <i class="bi bi-people me-1"></i>
                            ${officialsInfo}
                        </div>
                    </div>
                    <div class="text-end">
                        <div class="status-badge bg-primary text-white mb-1">
                            ${escapeHtml(game.sport || 'Game')}
                        </div>
                        <div class="status-badge bg-${statusColor} text-white small">
                            ${game.response}
                        </div>
                        ${game.level ? `<div class="text-muted small mt-1">${escapeHtml(game.level)}</div>` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function updateMyGamesList() {
    const container = document.getElementById('my-games-list');
    const filter = document.getElementById('games-filter')?.value || 'all';
    
    let filteredGames = OFFICIAL_CONFIG.games;
    
    if (filter === 'upcoming') {
        filteredGames = filteredGames.filter(game => new Date(game.date) >= new Date());
    } else if (filter === 'completed') {
        filteredGames = filteredGames.filter(game => new Date(game.date) < new Date());
    }
    
    filteredGames.sort((a, b) => new Date(b.date) - new Date(a.date));
    
    if (filteredGames.length === 0) {
        container.innerHTML = `
            <div class="text-center p-4 text-muted">
                <i class="bi bi-calendar-x fs-1 mb-3 d-block"></i>
                <p>No games found for the selected filter</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = filteredGames.map(game => {
        const isUpcoming = new Date(game.date) >= new Date();
        const gameStatusClass = isUpcoming ? 'bg-primary' : 'bg-success';
        const gameStatusText = isUpcoming ? 'Upcoming' : 'Completed';
        const responseStatusColor = getResponseStatusColor(game.response);
        const officialsInfo = getOfficialsDisplayInfo(game);
        
        return `
            <div class="game-item clickable" onclick="showGameDetails(${game.id})">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div class="fw-bold fs-5">${escapeHtml(game.home_team)} vs ${escapeHtml(game.away_team)}</div>
                            <div class="d-flex flex-column gap-1">
                                <span class="status-badge ${gameStatusClass} text-white">${gameStatusText}</span>
                                <span class="status-badge bg-${responseStatusColor} text-white small">
                                    Your Status: ${game.response}
                                </span>
                            </div>
                        </div>
                        
                        <div class="row text-muted small">
                            <div class="col-md-6">
                                <div class="mb-1">
                                    <i class="bi bi-calendar me-1"></i>
                                    ${formatDate(game.date)} at ${formatTime(game.time)}
                                </div>
                                <div class="mb-1">
                                    <i class="bi bi-geo-alt me-1"></i>
                                    ${escapeHtml(game.location || 'TBD')}
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-1">
                                    <i class="bi bi-trophy me-1"></i>
                                    ${escapeHtml(game.sport || 'Game')}
                                    ${game.level ? ` - ${escapeHtml(game.level)}` : ''}
                                </div>
                                ${game.league ? `
                                    <div class="mb-1">
                                        <i class="bi bi-diagram-3 me-1"></i>
                                        ${escapeHtml(game.league)}
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                        
                        <div class="mt-2 p-2 bg-light rounded">
                            <div class="small">
                                <i class="bi bi-people me-1"></i>
                                <strong>Officials:</strong> ${officialsInfo}
                            </div>
                        </div>
                        
                        <div class="mt-2 d-flex gap-2">
                            <button class="btn btn-outline-primary btn-sm" onclick="event.stopPropagation(); openGoogleMaps('${escapeHtml(game.location)}')">
                                <i class="bi bi-geo-alt"></i>
                            </button>
                            <button class="btn btn-outline-primary btn-sm" onclick="event.stopPropagation(); exportToCalendar('${game.date}', '${game.time}', '${escapeHtml(game.home_team)} vs ${escapeHtml(game.away_team)}', '${escapeHtml(game.location)}')">
                                <i class="bi bi-calendar-plus"></i>
                            </button>
                        </div>
                        
                        ${game.notes ? `
                            <div class="mt-2 p-2 bg-light rounded">
                                <small class="text-muted">
                                    <i class="bi bi-sticky me-1"></i>
                                    ${escapeHtml(game.notes)}
                                </small>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Enhanced Game Details and Actions
let currentGameId = null;

function showGameDetails(gameId) {
    currentGameId = gameId;
    loadGameDetails(gameId);
}

async function loadGameDetails(gameId) {
    try {
        const response = await axios.get(`/api/officials/game/${gameId}`);
        const game = response.data.game;
        
        const detailsHtml = `
            <div class="row">
                <div class="col-md-6">
                    <h6 class="fw-bold">Game Information</h6>
                    <table class="table table-sm">
                        <tr><td><strong>Teams:</strong></td><td>${escapeHtml(game.home_team)} vs ${escapeHtml(game.away_team)}</td></tr>
                        <tr><td><strong>Date:</strong></td><td>${formatDate(game.date)}</td></tr>
                        <tr><td><strong>Time:</strong></td><td>${game.time}</td></tr>
                        <tr><td><strong>Location:</strong></td><td>${escapeHtml(game.location || 'TBD')}</td></tr>
                        <tr><td><strong>Sport:</strong></td><td>${escapeHtml(game.sport)}</td></tr>
                        <tr><td><strong>League:</strong></td><td>${escapeHtml(game.league || 'N/A')}</td></tr>
                        <tr><td><strong>Level:</strong></td><td>${escapeHtml(game.level || 'N/A')}</td></tr>
                        <tr><td><strong>Your Position:</strong></td><td>${escapeHtml(game.position)}</td></tr>
                        <tr><td><strong>Status:</strong></td><td><span class="badge bg-${getStatusColor(game.response)}">${game.response}</span></td></tr>
                    </table>
                    
                    ${game.notes ? `
                        <h6 class="fw-bold mt-3">Game Notes</h6>
                        <div class="p-2 bg-light rounded">${escapeHtml(game.notes)}</div>
                    ` : ''}
                    
                    <div class="mt-3">
                        <button class="btn btn-primary btn-sm me-2" onclick="openGoogleMaps('${escapeHtml(game.location)}')">
                            <i class="bi bi-geo-alt me-1"></i>View in Maps
                        </button>
                        <button class="btn btn-outline-primary btn-sm me-2" onclick="exportToCalendar('${game.date}', '${game.time}', '${escapeHtml(game.home_team)} vs ${escapeHtml(game.away_team)}', '${escapeHtml(game.location)}')">
                            <i class="bi bi-calendar-plus me-1"></i>Add to Calendar
                        </button>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <h6 class="fw-bold">Assignment Details</h6>
                    <table class="table table-sm">
                        <tr><td><strong>Assigned Date:</strong></td><td>${formatDate(game.assigned_date)}</td></tr>
                        <tr><td><strong>Assigned By:</strong></td><td>${escapeHtml(game.assigned_by.name || 'N/A')}</td></tr>
                        ${game.assigned_by.email ? `<tr><td><strong>Contact Email:</strong></td><td><a href="mailto:${game.assigned_by.email}">${game.assigned_by.email}</a></td></tr>` : ''}
                        ${game.assigned_by.phone ? `<tr><td><strong>Contact Phone:</strong></td><td><a href="tel:${game.assigned_by.phone}">${game.assigned_by.phone}</a></td></tr>` : ''}
                    </table>
                    
                    <h6 class="fw-bold mt-3">Other Officials</h6>
                    <div class="list-group list-group-flush">
                        ${game.other_officials.map(official => `
                            <div class="list-group-item px-0 py-2">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <strong>${escapeHtml(official.name)}</strong> - ${escapeHtml(official.position)}
                                        <div class="small text-muted">
                                            ${official.email ? `<a href="mailto:${official.email}" class="me-2">${official.email}</a>` : ''}
                                            ${official.phone ? `<a href="tel:${official.phone}">${official.phone}</a>` : ''}
                                        </div>
                                    </div>
                                    <span class="badge bg-${getStatusColor(official.response)}">${official.response}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('gameDetailsContent').innerHTML = detailsHtml;
        
        // Show response buttons if game is pending
        if (game.response === 'pending') {
            document.getElementById('gameResponseButtons').style.display = 'block';
        } else {
            document.getElementById('gameResponseButtons').style.display = 'none';
        }
        
        // Show modal
        new bootstrap.Modal(document.getElementById('gameDetailsModal')).show();
        
    } catch (error) {
        console.error('Failed to load game details:', error);
        showError('Failed to load game details');
    }
}

async function respondToGame(response) {
    if (!currentGameId) return;
    
    try {
        const result = await axios.post(`/api/officials/game/${currentGameId}/respond`, {
            response: response,
            notes: ''
        });
        
        if (result.data.success) {
            showSuccess(result.data.message);
            
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('gameDetailsModal')).hide();
            
            // Refresh game lists
            await loadOfficialGames();
            updateMyGamesList();
            updateUpcomingGamesList();
        } else {
            showError(result.data.message);
        }
        
    } catch (error) {
        console.error('Failed to respond to game:', error);
        showError('Failed to respond to game');
    }
}

function getStatusColor(status) {
    switch(status) {
        case 'accepted': return 'success';
        case 'declined': return 'danger';
        case 'pending': return 'warning';
        default: return 'secondary';
    }
}

function openGoogleMaps(location) {
    if (location) {
        const encodedLocation = encodeURIComponent(location);
        window.open(`https://www.google.com/maps/search/?api=1&query=${encodedLocation}`, '_blank');
    }
}

function exportToCalendar(date, time, title, location) {
    try {
        // Validate and parse the date and time
        if (!date || !time) {
            showError('Invalid date or time for calendar export');
            return;
        }
        
        // Create date object more safely
        const dateTimeStr = `${date}T${time}:00`;
        const startDate = new Date(dateTimeStr);
        
        // Check if date is valid
        if (isNaN(startDate.getTime())) {
            showError('Invalid date format for calendar export');
            return;
        }
        
        const endDate = new Date(startDate.getTime() + 2 * 60 * 60 * 1000); // 2 hours later
        
        const formatDateForCalendar = (date) => {
            return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
        };
        
        const calendarData = {
            title: title,
            start: formatDateForCalendar(startDate),
            end: formatDateForCalendar(endDate),
            location: location || '',
            description: `Sports Schedulers Game Assignment`
        };
        
        // Create ICS content
        const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Sports Schedulers//Game Assignment//EN
BEGIN:VEVENT
UID:${Date.now()}@sportsschedulers.com
DTSTAMP:${formatDateForCalendar(new Date())}
DTSTART:${calendarData.start}
DTEND:${calendarData.end}
SUMMARY:${calendarData.title}
LOCATION:${calendarData.location}
DESCRIPTION:${calendarData.description}
END:VEVENT
END:VCALENDAR`;
        
        // Create download link
        const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `game-${date}.ics`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showSuccess('Calendar event downloaded successfully');
        
    } catch (error) {
        console.error('Calendar export error:', error);
        showError('Failed to export calendar event');
    }
}

// Availability Management
async function loadAvailability() {
    try {
        const startDate = new Date();
        startDate.setDate(1); // First day of current month
        const endDate = new Date();
        endDate.setMonth(endDate.getMonth() + 2); // Two months ahead
        
        const response = await axios.get('/api/officials/availability', {
            params: {
                start_date: startDate.toISOString().split('T')[0],
                end_date: endDate.toISOString().split('T')[0]
            }
        });
        
        if (response.data.success) {
            renderAvailabilityCalendar(response.data.availability, response.data.assignments);
        }
        
    } catch (error) {
        console.error('Failed to load availability:', error);
        showError('Failed to load availability calendar');
    }
}

function renderAvailabilityCalendar(availability, assignments) {
    const container = document.getElementById('availability-calendar');
    
    // Simple calendar implementation
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();
    
    let calendarHtml = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <button class="btn btn-outline-primary" onclick="changeMonth(-1)">
                <i class="bi bi-chevron-left"></i>
            </button>
            <h5>${new Date(currentYear, currentMonth).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</h5>
            <button class="btn btn-outline-primary" onclick="changeMonth(1)">
                <i class="bi bi-chevron-right"></i>
            </button>
        </div>
        
        <div class="alert alert-info">
            <i class="bi bi-info-circle me-2"></i>
            <strong>Default:</strong> All dates are available unless marked otherwise. Only mark dates when you're unavailable.
        </div>
        
        <div class="calendar-grid">
            <div class="row">
                <div class="col text-center fw-bold">Sun</div>
                <div class="col text-center fw-bold">Mon</div>
                <div class="col text-center fw-bold">Tue</div>
                <div class="col text-center fw-bold">Wed</div>
                <div class="col text-center fw-bold">Thu</div>
                <div class="col text-center fw-bold">Fri</div>
                <div class="col text-center fw-bold">Sat</div>
            </div>
    `;
    
    // Generate calendar days
    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    
    let dayCount = 1;
    for (let week = 0; week < 6; week++) {
        calendarHtml += '<div class="row">';
        for (let day = 0; day < 7; day++) {
            if (week === 0 && day < firstDay) {
                calendarHtml += '<div class="col calendar-day"></div>';
            } else if (dayCount <= daysInMonth) {
                const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(dayCount).padStart(2, '0')}`;
                
                // Only show explicit unavailable/partial entries
                const dayAvailability = availability.filter(a => a.date === dateStr);
                const dayAssignments = assignments.filter(a => a.date === dateStr);
                
                let dayClass = 'calendar-day clickable';
                let dayContent = `<div class="day-number">${dayCount}</div>`;
                
                // Show assignments
                if (dayAssignments.length > 0) {
                    dayClass += ' has-assignment';
                    dayContent += `<div class="assignment-indicator">${dayAssignments.length} game(s)</div>`;
                }
                
                // Show explicit unavailability only
                if (dayAvailability.length > 0) {
                    const availType = dayAvailability[0].type;
                    dayClass += ` availability-${availType}`;
                    dayContent += `<div class="availability-indicator">${availType}</div>`;
                } else {                    
                    // Leave blank for available days (default state)
                }
                
                calendarHtml += `
                    <div class="col ${dayClass}" onclick="selectDate('${dateStr}')">
                        ${dayContent}
                    </div>
                `;
                dayCount++;
            } else {
                calendarHtml += '<div class="col calendar-day"></div>';
            }
        }
        calendarHtml += '</div>';
        if (dayCount > daysInMonth) break;
    }
    
    calendarHtml += '</div>';
    
    container.innerHTML = calendarHtml;
}

function selectDate(dateStr) {
    // Set the date in the availability modal and show it
    document.getElementById('availability-date').value = dateStr;
    showAvailabilityModal('unavailable');
}

function showAvailabilityModal(type) {
    document.getElementById('availability-type').value = type;
    toggleTimeFields();
    new bootstrap.Modal(document.getElementById('availabilityModal')).show();
}

function toggleTimeFields() {
    const type = document.getElementById('availability-type').value;
    const timeFields = document.getElementById('time-fields');
    
    if (type === 'partial') {
        timeFields.style.display = 'block';
    } else {
        timeFields.style.display = 'none';
    }
}

async function saveAvailability() {
    try {
        const formData = {
            date: document.getElementById('availability-date').value,
            type: document.getElementById('availability-type').value,
            start_time: document.getElementById('start-time').value,
            end_time: document.getElementById('end-time').value,
            reason: document.getElementById('availability-reason').value
        };
        
        if (!formData.date || !formData.type) {
            showError('Please fill in all required fields');
            return;
        }
        
        const response = await axios.post('/api/officials/availability', formData);
        
        if (response.data.success) {
            showSuccess(response.data.message);
            bootstrap.Modal.getInstance(document.getElementById('availabilityModal')).hide();
            
            // Refresh availability calendar
            await loadAvailability();
            
            // Reset form
            document.getElementById('availabilityForm').reset();
            toggleTimeFields();
        } else {
            showError(response.data.message);
        }
        
    } catch (error) {
        console.error('Failed to save availability:', error);
        showError('Failed to save availability');
    }
}

// Tab management
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName + '-tab');
    if (selectedTab) {
        selectedTab.style.display = 'block';
    }
    
    // Add active class to clicked nav link
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    // Load tab-specific data
    if (tabName === 'my-profile') {
        loadProfile();
    } else if (tabName === 'availability') {
        loadAvailability();
    }
}

// Profile management
async function loadProfile() {
    try {
        const response = await axios.get('/api/officials/profile');
        const user = response.data.user;
        
        document.getElementById('full-name').value = user.full_name || '';
        document.getElementById('email').value = user.email || '';
        document.getElementById('phone').value = user.phone || '';
        document.getElementById('username').value = user.username || '';
        document.getElementById('address').value = user.address || '';
        
        document.getElementById('member-since').textContent = 
            user.created_date ? formatDate(user.created_date) : 'Unknown';
        document.getElementById('last-login').textContent = 
            user.last_login ? formatDateTime(user.last_login) : 'Never';
        
    } catch (error) {
        console.error('Failed to load profile:', error);
        showError('Failed to load profile information');
    }
}

function editProfile() {
    const fields = ['full-name', 'email', 'phone', 'address'];
    fields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.removeAttribute('readonly');
            field.classList.add('border-primary');
        }
    });
    
    document.querySelector('button[onclick="editProfile()"]').style.display = 'none';
    document.getElementById('edit-buttons').classList.remove('d-none');
}

async function saveProfile() {
    try {
        const profileData = {
            full_name: document.getElementById('full-name').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            address: document.getElementById('address').value
        };
        
        await axios.put('/api/officials/profile', profileData);
        
        showSuccess('Profile updated successfully');
        cancelEdit();
        
    } catch (error) {
        console.error('Failed to save profile:', error);
        showError('Failed to update profile');
    }
}

function cancelEdit() {
    const fields = ['full-name', 'email', 'phone', 'address'];
    fields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.setAttribute('readonly', true);
            field.classList.remove('border-primary');
        }
    });
    
    document.querySelector('button[onclick="editProfile()"]').style.display = 'inline-block';
    document.getElementById('edit-buttons').classList.add('d-none');
    
    loadProfile();
}

function changePassword() {
    alert('Password change functionality would be implemented here');
}

function filterMyGames() {
    updateMyGamesList();
}

// Utility functions
function updateCurrentDate() {
    const now = new Date();
    const dateElement = document.getElementById('current-date');
    if (dateElement) {
        dateElement.textContent = now.toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
    }
}

function formatDate(dateString) {
    if (!dateString) return 'TBD';
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatTime(timeString) {
    if (!timeString) return 'TBD';
    return timeString;
}

function formatDateTime(dateTimeString) {
    if (!dateTimeString) return 'Never';
    return new Date(dateTimeString).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showSuccess(message) {
    const toast = document.createElement('div');
    toast.className = 'position-fixed top-0 end-0 m-3 alert alert-success alert-dismissible';
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5000);
}

function showError(message) {
    const toast = document.createElement('div');
    toast.className = 'position-fixed top-0 end-0 m-3 alert alert-danger alert-dismissible';
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5000);
}

function logout() {
    window.location.href = '/logout';
}

// Helper function to get officials display information
function getOfficialsDisplayInfo(game) {
    if (!game.assigned_officials || game.assigned_officials.length === 0) {
        const needed = game.officials_needed || 1;
        return `${needed} slot${needed > 1 ? 's' : ''} open`;
    }
    
    const officials = game.assigned_officials.map(official => {
        const statusIcon = official.response === 'accepted' ? '✓' : 
                          official.response === 'pending' ? '⏳' : '?';
        const emphasis = official.is_current_user ? '<strong>' : '';
        const emphasisEnd = official.is_current_user ? '</strong>' : '';
        
        return `${emphasis}${escapeHtml(official.name)} (${escapeHtml(official.position)}) ${statusIcon}${emphasisEnd}`;
    }).join(', ');
    
    const emptySlots = game.empty_slots || 0;
    const emptyText = emptySlots > 0 ? `, ${emptySlots} slot${emptySlots > 1 ? 's' : ''} open` : '';
    
    return officials + emptyText;
}

// Helper function to get response status color
function getResponseStatusColor(response) {
    switch(response) {
        case 'accepted': return 'success';
        case 'declined': return 'danger';
        case 'pending': return 'warning';
        default: return 'secondary';
    }
}
