# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/claude-code) when working with code in this repository.

## Project Overview

PBS System (Budget System) is a corporate budget planning and management application with SAP integration capabilities. It features a FastAPI backend with PostgreSQL database and a React TypeScript frontend.

## Project Location

**Single project directory**: `C:\Users\Egemen\Desktop\budget-system`

All development work should be done in this directory. Virtual environment is included in the same directory.

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
├── api/v1/           # API route handlers
│   ├── audit_logs.py # Audit log endpoints
│   └── dynamic/      # Dynamic master data endpoints
│       ├── meta_entities.py    # Entity type CRUD (uses joinedload for attributes)
│       ├── meta_attributes.py  # Attribute CRUD
│       ├── master_data.py      # Master data CRUD + CSV import/export
│       └── fact_data.py        # Fact data operations
├── models/           # SQLAlchemy ORM models
│   ├── audit_log.py  # Audit log model
│   └── dynamic/      # Dynamic entity models
│       ├── meta_entity.py      # Entity type definitions
│       ├── meta_attribute.py   # Attribute definitions (uses PostgreSQL enum)
│       ├── master_data.py      # Master data records
│       └── master_data_value.py # Attribute values
├── schemas/          # Pydantic request/response schemas
│   └── dynamic/      # Dynamic entity schemas
├── services/         # Business logic layer
│   └── audit_log_service.py
├── repositories/     # Data access layer
│   └── audit_log_repository.py
├── scripts/          # Utility scripts (e.g., seed_dim_time.py)
└── utils/            # Helper utilities
```

### Frontend Structure
```
frontend/src/
├── api/              # API client configuration
├── components/       # Reusable UI components
│   ├── Dashboard.tsx          # Main dashboard (meta-entities summary)
│   ├── LayoutProvider.tsx     # Main layout with Sidebar and Header (ACTIVE)
│   └── Navigation.tsx         # Legacy navigation (NOT USED - kept for reference)
├── pages/            # Page-level components
│   ├── MetaEntitiesPage.tsx   # Entity type management (2-step wizard)
│   ├── MasterDataPage.tsx     # Master data CRUD + CSV import/export modals
│   ├── EntityEditPage.tsx     # Attribute management
│   ├── AnalyticsDashboard.tsx # Analytics with charts (meta-entities data)
│   └── AuditLogsPage.tsx      # Audit log viewer
├── services/         # API service functions
│   └── masterDataApi.ts       # Master data API client (includes CSV endpoints)
└── stores/           # Zustand state stores
```

### Important: Layout Component
The actual sidebar/navigation is in `LayoutProvider.tsx` (Sidebar function), NOT in `Navigation.tsx`.
When modifying navigation items, edit `LayoutProvider.tsx`.

## Key Concepts

### Dynamic Master Data System
The system supports configurable master data entities through a metadata-driven architecture:
- **MetaEntity**: Defines entity types (e.g., CostCenter, Department, Customer)
- **MetaAttribute**: Defines attributes for each entity type with data types
- **MasterData**: Actual master data records
- **MasterDataValue**: Attribute values for master data records
- **DimTime**: Time dimension for temporal data

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

## Database

- PostgreSQL 15 running on port 5432 (via Docker)
- Connection configured in `.env` file
- pgAdmin available at http://localhost:5050

### Important: PostgreSQL Enums
The `meta_attributes.data_type` column uses a PostgreSQL native enum (`attributetype`). When inserting data, use lowercase string values like `'string'`, `'integer'`, etc. - not Python Enum members.

### Important: SQLAlchemy Relationships
When fetching entities with related data (e.g., MetaEntity with attributes), use `joinedload`:
```python
entity = db.query(MetaEntity)\
    .options(joinedload(MetaEntity.attributes))\
    .filter(MetaEntity.id == entity_id)\
    .first()
```
Without joinedload, related collections may not be loaded and will return empty in API responses.

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
