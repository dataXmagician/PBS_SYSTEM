# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/claude-code) when working with code in this repository.

## Project Overview

PBS System (Budget System) is a corporate budget planning and management application with SAP integration capabilities. It features a FastAPI backend with PostgreSQL database and a React TypeScript frontend.

## Project Location

**Single project directory**: `C:\Users\Egemen\Desktop\budget-system`

All development work should be done in this directory. Virtual environment is included in the same directory.

### CRITICAL: Worktree Sync Rule
Claude Code may run from a git worktree directory (e.g., `C:\Users\Egemen\.claude-worktrees\...`). This worktree shares the same git repo but has its **own working tree**. Python's `import app` resolves from CWD, so worktree files must always match the main repo.

**Rules:**
1. **Truth source**: `C:\Users\Egemen\Desktop\budget-system` is always the canonical directory
2. **After editing ANY file**, immediately copy it to the worktree equivalent path so Python/Vite picks up changes
3. **Before starting services**, verify worktree files match main repo: `diff -rq worktree/app main/app --exclude=__pycache__`
4. **Clean pycache** after syncing: `find <dir>/app -type d -name "__pycache__" -exec rm -rf {} +`
5. **NEVER start/stop backend or frontend services** — ask the user to do this manually

### Service Management Rule
**Do NOT start, stop, or restart backend (uvicorn) or frontend (npm run dev) services.** Always ask the user to manage services themselves. This avoids zombie processes and port conflicts.

### Zombie Process Warning
When restarting uvicorn, **always kill ALL processes on port 8000 first**. Multiple uvicorn instances can bind to the same port on Windows, and curl may connect to an old instance that doesn't have new routes. Before starting uvicorn:
```powershell
# Kill all processes on port 8000
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
# Verify port is free
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
```

## Tech Stack

### Backend
- **Framework**: FastAPI 0.104
- **Database**: PostgreSQL 15 with SQLAlchemy 2.0 ORM
- **Migrations**: Alembic
- **Auth**: JWT tokens (python-jose, passlib, bcrypt)
- **Caching**: Redis 5.0
- **Task Queue**: Celery 5.3
- **File Upload**: python-multipart (required for CSV import)
- **Testing**: pytest, pytest-asyncio, httpx

### Frontend
- **Framework**: React 18 with TypeScript
- **Build**: Vite 5
- **Styling**: Tailwind CSS (dark theme body with explicit light text on white backgrounds)
- **State Management**: Zustand
- **Data Tables**: TanStack Table
- **Charts**: Recharts
- **HTTP Client**: Axios
- **Routing**: React Router v6

## Common Commands

### Backend
```bash
# Start development server
cd C:\Users\Egemen\Desktop\budget-system
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run database migrations
.\venv\Scripts\python.exe -m alembic upgrade head

# Create new migration
.\venv\Scripts\python.exe -m alembic revision --autogenerate -m "description"

# Run tests
.\venv\Scripts\python.exe -m pytest

# Code formatting
.\venv\Scripts\python.exe -m black app/
.\venv\Scripts\python.exe -m isort app/
.\venv\Scripts\python.exe -m flake8 app/
```

### Frontend
```bash
cd C:\Users\Egemen\Desktop\budget-system\frontend
npm install          # Install dependencies
npm run dev          # Start dev server (Vite) - runs on http://localhost:5173
npm run build        # Production build
npm run lint         # ESLint check
```

### Docker (for PostgreSQL & Redis)
```bash
cd C:\Users\Egemen\Desktop\budget-system
docker-compose up -d              # Start PostgreSQL, Redis, pgAdmin
docker-compose -f docker-compose.prod.yml up -d  # Production setup
```

## Architecture

### Backend Structure
```
app/
├── config.py             # Application settings (Pydantic BaseSettings)
├── main.py               # FastAPI app, router registration, CORS, error handlers
├── dependencies.py       # FastAPI dependencies (JWT auth, DB session)
├── api/
│   ├── auth.py           # Auth endpoints (login, register, me, verify-token)
│   └── v1/               # API v1 route handlers
│       ├── budgets.py    # Budget CRUD + budget lines
│       ├── companies.py  # Company CRUD
│       ├── customers.py  # Customer CRUD
│       ├── products.py   # Product CRUD
│       ├── periods.py    # Fiscal period CRUD
│       ├── forecasts.py  # Forecast calculation & CRUD
│       ├── reports.py    # Report generation (summary, detailed, variance)
│       ├── scenarios.py  # Scenario analysis (create, compare)
│       ├── rules.py      # Calculation rules CRUD
│       ├── audit_logs.py # Audit log endpoints
│       ├── sync.py       # SAP synchronization
│       └── dynamic/      # Dynamic master data endpoints
│           ├── meta_entities.py    # Entity type CRUD (uses joinedload)
│           ├── meta_attributes.py  # Attribute CRUD
│           ├── master_data.py      # Master data CRUD + CSV import/export
│           ├── fact_definitions.py # Fact definition CRUD
│           └── fact_data.py        # Fact data operations
├── models/               # SQLAlchemy ORM models
│   ├── user.py           # User (UUID PK, username, email, hashed_password)
│   ├── company.py        # Company (UUID PK, sap_company_code, budget_detail_level)
│   ├── customer.py       # Customer (UUID PK, sap_customer_number, sales_org)
│   ├── product.py        # Product (UUID PK, sap_material_number, category)
│   ├── period.py         # Period (UUID PK, fiscal_year, period 1-12, is_open, is_locked)
│   ├── budget.py         # Budget (UUID PK, company_id, fiscal_year, status, total_amount)
│   ├── budget_line.py    # BudgetLine (UUID PK, original/revised/actual/forecast amounts)
│   ├── forecast.py       # Forecast (UUID PK, forecast_method, confidence_score)
│   ├── report.py         # Report (UUID PK, report_type, report_format, file_path)
│   ├── scenario.py       # Scenario (UUID PK, adjustment_percentage, impact)
│   ├── rule.py           # CalculationRule (UUID PK, rule_type, condition, action)
│   ├── audit_log.py      # AuditLog (UUID PK, user_id, action, target_table)
│   └── dynamic/          # Dynamic entity models
│       ├── meta_entity.py      # MetaEntity (Integer PK, code, default_name, icon, color)
│       ├── meta_attribute.py   # MetaAttribute (Integer PK, data_type enum, options, reference)
│       ├── meta_translation.py # MetaTranslation (Integer PK, language_code, translated_name)
│       ├── master_data.py      # MasterData (Integer PK, entity_id, code, name)
│       ├── master_data_value.py # MasterDataValue (Integer PK, attribute_id, value)
│       ├── dim_time.py         # DimTime (Integer PK, date_key YYYYMMDD, Turkish month names)
│       ├── fact_definition.py  # FactDefinition + FactDimension
│       ├── fact_measure.py     # FactMeasure (MeasureType, AggregationType enums)
│       └── fact_data.py        # FactData + FactDataValue
├── schemas/              # Pydantic request/response schemas
│   ├── user.py           # UserRegister, UserLogin, UserResponse, TokenResponse
│   ├── company.py        # Company create/update/response schemas
│   ├── customer.py       # Customer schemas
│   ├── product.py        # Product schemas
│   ├── period.py         # Period schemas
│   ├── budget.py         # Budget + BudgetLine schemas
│   ├── forecast.py       # Forecast schemas
│   ├── rule.py           # CalculationRule schemas
│   └── dynamic/          # Dynamic entity schemas
│       ├── meta_entity.py
│       ├── meta_attribute.py
│       ├── meta_translation.py
│       ├── master_data.py
│       ├── fact_definition.py
│       └── fact_data.py
├── services/             # Business logic layer
│   ├── auth_service.py       # Registration, login, JWT token management
│   ├── audit_log_service.py  # Audit logging
│   ├── budget_service.py     # Budget operations
│   ├── calculation_engine.py # Budget calculation engine
│   ├── company_service.py    # Company operations
│   ├── customer_service.py   # Customer operations
│   ├── product_service.py    # Product operations
│   ├── period_service.py     # Period operations
│   ├── forecast_service.py   # Forecast calculations
│   ├── report_service.py     # Report generation
│   ├── scenario_service.py   # Scenario analysis
│   └── sap_connector.py      # SAP integration (placeholder)
├── repositories/         # Data access layer
│   ├── user_repository.py
│   ├── audit_log_repository.py
│   ├── budget_repository.py
│   ├── company_repository.py
│   ├── customer_repository.py
│   ├── period_repository.py
│   └── product_repository.py
├── db/                   # Database configuration
│   ├── base.py           # SQLAlchemy Base + BaseModel (auto created_date/updated_date)
│   └── session.py        # Engine, session factory, get_db dependency
├── scripts/              # Utility scripts
│   └── seed_dim_time.py  # Seed DimTime table with Turkish month/day names
└── utils/
    └── auth_utils.py     # Auth utility functions
```

### Frontend Structure
```
frontend/src/
├── api/                  # API client configuration
│   └── client.ts         # Axios instance + legacy API wrappers (auth, budget, master, forecast, report, scenario)
├── components/           # Reusable UI components
│   ├── Dashboard.tsx           # Main dashboard (meta-entities summary cards + charts)
│   ├── LayoutProvider.tsx      # Main layout with Sidebar and Header (ACTIVE)
│   ├── LoginForm.tsx           # Login/Register page
│   ├── Navigation.tsx          # Legacy navigation (NOT USED - kept for reference)
│   ├── CompanyForm.tsx         # Company create/edit form
│   ├── CustomerForm.tsx        # Customer create/edit form
│   ├── ProductForm.tsx         # Product create/edit form
│   ├── DataGrid.tsx            # Generic data grid component
│   ├── DataGridTable.tsx       # Data grid table variant
│   ├── EnhancedDataGridTable.tsx # Enhanced data grid
│   ├── ExcelImport.tsx         # Excel import component
│   └── SAPSync.tsx             # SAP synchronization UI
├── pages/                # Page-level components
│   ├── MetaEntitiesPage.tsx    # Entity type management (2-step wizard: basic info + attributes)
│   ├── MasterDataPage.tsx      # Master data CRUD + CSV import/export modals
│   ├── EntityEditPage.tsx      # Attribute management for an entity
│   ├── AnalyticsDashboard.tsx  # Analytics with Recharts (bar, pie, area charts)
│   └── AuditLogsPage.tsx       # Audit log viewer
├── services/             # API service functions
│   └── masterDataApi.ts  # Dynamic master data API (metaEntitiesApi, metaAttributesApi, masterDataApi + CSV)
└── stores/               # Zustand state stores
    └── authStore.ts      # Auth state (token, user, login/logout) - persisted in localStorage
```

### Important: Layout Component
The actual sidebar/navigation is in `LayoutProvider.tsx` (Sidebar function), NOT in `Navigation.tsx`.
When modifying navigation items, edit `LayoutProvider.tsx`.

## Key Concepts

### Authentication
- Endpoints at `/api/v1/auth/`: `POST /register`, `POST /login`, `GET /me`, `POST /verify-token`
- JWT tokens (HS256) via `python-jose`, stored in `localStorage`
- Frontend uses `authStore.ts` (Zustand) to manage token/user state
- Axios interceptor adds `Authorization: Bearer <token>` to all requests
- 401 responses auto-redirect to `/login`

### Dynamic Master Data System
The system supports configurable master data entities through a metadata-driven architecture:
- **MetaEntity**: Defines entity types (e.g., CostCenter, Department, Customer)
- **MetaAttribute**: Defines attributes for each entity type with data types
- **MasterData**: Actual master data records
- **MasterDataValue**: Attribute values for master data records
- **DimTime**: Time dimension for temporal data (Turkish locale, seeded via `seed_dim_time.py`)

### Fact Data System
The fact system enables data entry with configurable dimensions and measures:
- **FactDefinition**: Data entry template (code, name, time_granularity: day/week/month/quarter/year)
- **FactDimension**: Links fact definitions to meta entities as dimensions (sort_order, is_required)
- **FactMeasure**: Measure definitions with types (integer/decimal/currency/percentage), aggregation (sum/avg/min/max/count/last), optional formula for calculated fields
- **FactData**: Actual data entries with JSONB dimension_values, time_id, version (BUDGET/FORECAST/ACTUAL)
- **FactDataValue**: Measure values for each fact data entry

### Legacy SAP-Integrated Modules
These modules support the original SAP-integrated budget workflow:
- **Company** (`/api/v1/companies`): SAP company codes, `budget_detail_level` (PRODUCT/PRODUCT_CUSTOMER/PERIOD_ONLY)
- **Product** (`/api/v1/products`): SAP material master, linked to company
- **Customer** (`/api/v1/customers`): SAP customer master, linked to company (sales_org, distribution_channel, division)
- **Period** (`/api/v1/periods`): Fiscal year periods (1-12), `is_open`/`is_locked` flags, linked to company
- **Budget** (`/api/v1/budgets`): Budget header per company+fiscal year, status (DRAFT/APPROVED/LOCKED/ARCHIVED), `total_amount`, `currency`
- **BudgetLine**: Detail rows with original/revised/actual/forecast amounts, variance calculations
- **Forecast** (`/api/v1/forecasts`): Forecast methods (default MOVING_AVERAGE), confidence scores, upper/lower bounds
- **Report** (`/api/v1/reports`): Generated reports (SUMMARY/DETAILED/VARIANCE in PDF/EXCEL format)
- **Scenario** (`/api/v1/scenarios`): Scenario analysis with adjustment percentages and impact calculations
- **CalculationRule** (`/api/v1/rules`): Auto-calculation rules (PERCENTAGE/FORMULA/THRESHOLD) with conditions and actions
- **Sync** (`/api/v1/sync`): SAP synchronization endpoints

### Attribute Data Types (PostgreSQL Enum: `attributetype`)
- `string` - Text values
- `integer` - Whole numbers
- `decimal` - Decimal numbers
- `boolean` - True/False
- `date` - Date only
- `datetime` - Date and time
- `list` - Predefined options
- `reference` - Foreign key to another entity

### API Patterns
- All API routes prefixed with `/api/v1/`
- JWT Bearer token authentication required for protected endpoints
- API docs available at `/api/docs` (Swagger) and `/api/redoc`

### CSV Import/Export
Master data supports CSV import/export:
- **Export**: `GET /api/v1/master-data/export/{entity_id}/csv` - Downloads CSV with UTF-8 BOM
- **Import**: `POST /api/v1/master-data/import/{entity_id}/csv` - Uploads CSV file (multipart/form-data)
- CSV format: Semicolon (;) delimiter, first row headers (CODE;NAME;custom_attributes...)
- Import behavior: Existing codes are updated, new codes are created

### Frontend Routes (App.tsx)
| Route | Component | Purpose |
|-------|-----------|---------|
| `/login` | `LoginForm` | Login/register (public) |
| `/dashboard` | `Dashboard` | Main dashboard with entity summary cards |
| `/analytics` | `AnalyticsDashboard` | Charts and analytics (Recharts) |
| `/meta-entities` | `MetaEntitiesPage` | Entity type management (2-step wizard) |
| `/meta-entities/:entityId/edit` | `EntityEditPage` | Attribute management |
| `/master-data/:entityId` | `MasterDataPage` | Master data CRUD + CSV |
| `/audit-logs` | `AuditLogsPage` | System activity logs |
| `/` | Redirect to `/dashboard` | |

### Frontend Sidebar Navigation (LayoutProvider.tsx)
1. **Dashboard** (`/dashboard`) - Budget overview
2. **Anaveri Yonetimi** (`/meta-entities`) - Dynamic master data types
3. **Analytics** (`/analytics`) - Charts and analysis
4. **Audit Logs** (`/audit-logs`) - System activity logs

### Frontend API Clients
- **`api/client.ts`**: Main Axios client with wrappers for `authAPI`, `budgetAPI`, `masterAPI` (companies, products, customers), `forecastAPI`, `reportAPI`, `scenarioAPI`
- **`services/masterDataApi.ts`**: Separate Axios client for dynamic master data — `metaEntitiesApi`, `metaAttributesApi`, `masterDataApi` (including CSV endpoints)
- Both use `localStorage.getItem('token')` for auth via interceptors
- Base URL: `VITE_API_URL` env var or `http://localhost:8000/api/v1`

## Database

- PostgreSQL 15 running on port 5432 (via Docker)
- Connection configured in `.env` file
- pgAdmin available at http://localhost:5050

### Two Model Base Classes
- **`Base`** (from `declarative_base()`): Used by legacy models. These use `UUID(as_uuid=True)` primary keys.
- **`BaseModel(Base)`**: Used by dynamic models (MetaEntity, MetaAttribute, etc.). Adds `created_date` and `updated_date` automatically. These use `Integer` auto-increment primary keys with a separate `uuid` string column.

### Important: PostgreSQL Enums
The `meta_attributes.data_type` column uses a PostgreSQL native enum (`attributetype`). When inserting data, use lowercase string values like `'string'`, `'integer'`, etc. - not Python Enum members.

When creating new PostgreSQL enums in migrations:
- Use `create_type=False` in the SQLAlchemy model Column definition
- Use `checkfirst=True` when creating the enum in Alembic migrations to avoid duplicate type errors

### Important: SQLAlchemy Relationships
When fetching entities with related data (e.g., MetaEntity with attributes), use `joinedload`:
```python
entity = db.query(MetaEntity)\
    .options(joinedload(MetaEntity.attributes))\
    .filter(MetaEntity.id == entity_id)\
    .first()
```
Without joinedload, related collections may not be loaded and will return empty in API responses.

### Important: UUID Handling
PostgreSQL UUID columns return `uuid.UUID` objects. Pydantic schemas must use `uuid: UUID` (from `uuid import UUID`), NOT `uuid: str` — Pydantic v2 doesn't auto-coerce UUID to str.

## Router Registration (app/main.py)
All routers registered with prefix `/api/v1`:
```python
# Auth
app.include_router(auth.router, prefix="/api/v1")

# Legacy CRUD
app.include_router(companies.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(periods.router, prefix="/api/v1")
app.include_router(budgets.router, prefix="/api/v1")
app.include_router(forecasts.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(scenarios.router, prefix="/api/v1")
app.include_router(rules.router, prefix="/api/v1")
app.include_router(audit_logs.router, prefix="/api/v1")

# Dynamic Master Data
app.include_router(meta_entities_router, prefix="/api/v1")
app.include_router(meta_attributes_router, prefix="/api/v1")
app.include_router(master_data_router, prefix="/api/v1")
app.include_router(fact_definitions_router, prefix="/api/v1")
app.include_router(fact_data_router, prefix="/api/v1")
```

## Adding a New Module Checklist
1. **Model** (`app/models/`): Add SQLAlchemy model class
2. **Migration**: Run `alembic revision --autogenerate -m "description"` then `alembic upgrade head`
3. **Schema** (`app/schemas/`): Add Pydantic request/response schemas
   - Use `uuid: UUID` (from `uuid import UUID`), NOT `uuid: str`
   - Use `Optional[type] = None` for nullable fields
   - Use `from_attributes = True` in Config for ORM mode
4. **API** (`app/api/v1/`): Add FastAPI router with endpoints
5. **Register router** in `app/main.py`
6. **Frontend API** (`frontend/src/services/`): Add Axios client + TypeScript interfaces
7. **Frontend Pages** (`frontend/src/pages/`): Add page components
8. **Add route** in `frontend/src/App.tsx`
9. **Add sidebar item** in `frontend/src/components/LayoutProvider.tsx` (navItems array)
10. **Sync to worktree**: Copy ALL changed files to worktree path, clean pycache, then ask user to restart services

## Code Style Guidelines

### Python
- Use Black for formatting
- Use isort for import sorting
- Follow PEP 8 conventions
- Type hints encouraged for function signatures

### TypeScript/React
- Functional components with hooks
- TypeScript strict mode
- Tailwind for styling (avoid inline styles)
- ESLint for linting
- **Important**: Define interfaces locally in page components to avoid Vite cache issues with type exports

### UI Color Guidelines
The application uses a dark theme body (`text-gray-100`). When creating white background containers:
- Always add `text-gray-900` to white background containers
- Form inputs: `bg-white text-gray-900`
- Buttons on white: `bg-white text-gray-700`
- Modals: Add `text-gray-900` to modal container

## Environment Variables

Backend environment configured in `.env`:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing key
- `CORS_ORIGINS`: Allowed CORS origins

## Development Notes

### Vite Cache Issues
If frontend shows stale code after changes:
```powershell
cd C:\Users\Egemen\Desktop\budget-system\frontend
Remove-Item -Recurse -Force node_modules\.vite -ErrorAction SilentlyContinue
npm run dev
```

### Interface Exports
Due to Vite HMR issues, TypeScript interfaces are defined locally in each page component rather than imported from `masterDataApi.ts`.

## Notes

- Comments and some UI text are in Turkish (Kurumsal Butce Sistemi = Corporate Budget System)
- The application is designed for enterprise budget planning workflows
- SAP integration is planned (sap_connector.py exists but may be placeholder)
