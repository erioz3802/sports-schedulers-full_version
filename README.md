# Sports Schedulers - Web Application

**Author: Jose Ortiz
**Copyright: Jose Ortiz 2025
**Version:** 2.0.0 (Web)

## Modular Architecture

This application follows a clean modular architecture pattern for maintainability and scalability.

### Project Structure

```
sports-scheduler-web/
├── app.py                          # Main application entry point
├── config/                         # Configuration management
│   └── __init__.py                # App configuration classes
├── models/                         # Database models (SQLAlchemy)
│   └── __init__.py                # All database models
├── api/                           # API endpoints (organized by feature)
│   ├── auth/                      # Authentication endpoints
│   ├── games/                     # Games management API
│   ├── officials/                 # Officials management API
│   ├── assignments/               # Assignment management API
│   ├── leagues/                   # League management API
│   └── venues/                    # Venue management API
├── utils/                         # Utility modules
│   ├── decorators.py              # Security decorators
│   ├── logger.py                  # Activity logging
│   └── validators.py              # Data validation
├── templates/                     # HTML templates
├── static/                        # Static files (CSS, JS, images)
│   ├── js/modules/               # Modular JavaScript
│   └── css/components/           # Component-based CSS
└── scheduler.db                   # SQLite database
```

## Quick Start

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Application:**
   ```bash
   python app.py
   ```

3. **Access Application:**
   Open http://localhost:5000 in your browser

## Default Login Credentials

- **Super Admin:** `jose_1` / `Josu2398-1`
- **Admin:** `admin` / `admin123`

## Key Features

- Modular Architecture - Clean separation of concerns
- Role-Based Access Control - 4-tier permission system
- Activity Logging - Complete audit trail
- Database Models - Proper SQLAlchemy relationships
- API Endpoints - RESTful API design
- Security - Authentication decorators and validation

## User Hierarchy

The Sports Schedulers application implements a 4-tier user hierarchy system:

### 1. Super Admin
- **Access:** Complete system access
- **Permissions:** Can manage everything including creating leagues, managing all users, and system configuration
- **Scope:** Global access across all leagues and data

### 2. Admin  
- **Access:** League-specific administrative access
- **Permissions:** Can manage leagues assigned to them, create levels within leagues, manage users within their leagues
- **Scope:** Limited to assigned leagues only
- **Restrictions:** Cannot create new leagues, only levels within existing leagues

### 3. Assigner
- **Access:** League-specific assignment access  
- **Permissions:** Can assign games within assigned leagues, manage officials, create levels within leagues
- **Scope:** Limited to assigned leagues only
- **Restrictions:** Cannot manage users (except officials), cannot create leagues

### 4. Official
- **Access:** View-only access to assigned games
- **Permissions:** Can only view their assignments and update their profile
- **Scope:** Limited to games they are assigned to
- **Restrictions:** No administrative capabilities

## Access Control Boundaries

- **League Isolation:** Admin and Assigner roles are confined to their assigned leagues
- **Role Enforcement:** UI and API endpoints enforce role-based permissions
- **Data Filtering:** Users only see data they have permission to access
- **Audit Trail:** All actions are logged with user attribution

## User Hierarchy

The Sports Schedulers application implements a 4-tier user hierarchy system:

### 1. Super Admin
- **Access:** Complete system access
- **Permissions:** Can manage everything including creating leagues, managing all users, and system configuration
- **Scope:** Global access across all leagues and data

### 2. Admin  
- **Access:** League-specific administrative access
- **Permissions:** Can manage leagues assigned to them, create levels within leagues, manage users within their leagues
- **Scope:** Limited to assigned leagues only
- **Restrictions:** Cannot create new leagues, only levels within existing leagues

### 3. Assigner
- **Access:** League-specific assignment access  
- **Permissions:** Can assign games within assigned leagues, manage officials, create levels within leagues
- **Scope:** Limited to assigned leagues only
- **Restrictions:** Cannot manage users (except officials), cannot create leagues

### 4. Official
- **Access:** View-only access to assigned games
- **Permissions:** Can only view their assignments and update their profile
- **Scope:** Limited to games they are assigned to
- **Restrictions:** No administrative capabilities

## Access Control Boundaries

- **League Isolation:** Admin and Assigner roles are confined to their assigned leagues
- **Role Enforcement:** UI and API endpoints enforce role-based permissions
- **Data Filtering:** Users only see data they have permission to access
- **Audit Trail:** All actions are logged with user attribution

## Development

### Adding New Features

1. **New API Endpoint:** Create in appropriate `api/` subdirectory
2. **New Model:** Add to `models/__init__.py`
3. **New Utility:** Add to `utils/` directory
4. **New Configuration:** Update `config/__init__.py`

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Include docstrings for all functions
- Maintain consistent error handling patterns

## Migration from Desktop

This web application maintains feature parity with the original desktop version while adding:

- **Multi-user Support** - Multiple users can access simultaneously
- **Web Interface** - Modern responsive design
- **API Access** - RESTful endpoints for integration
- **Cloud Ready** - Easily deployable to cloud platforms

## Development Roadmap

- [ ] **Phase 1:** Core API completion (Games, Officials, Assignments)
- [ ] **Phase 2:** Advanced features (CSV import/export, reporting)
- [ ] **Phase 3:** Real-time features (WebSocket notifications)
- [ ] **Phase 4:** Mobile optimization and PWA features

---

**Built with care by Jose Ortiz - 2025**
