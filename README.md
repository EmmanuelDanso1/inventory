# InventoryDB

A full-stack inventory management system built with Flask and PostgreSQL, featuring a normalized (3NF) schema alongside a denormalized schema for performance comparison research.

---

## Features

- **Item Management** — Create, edit, delete, and search inventory items
- **Category & Supplier Management** — Organize items by category and supplier
- **Stock Transactions** — Record stock in, stock out, and adjustments
- **Reports** — Stock levels, low stock alerts, movement history, category summary, inventory valuation, and monthly summary
- **Performance Benchmarks** — Live query benchmarks comparing normalized vs denormalized schema performance
- **Dashboard** — Real-time stock overview with charts and recent transactions

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask 3.1.3 |
| Database | PostgreSQL + SQLAlchemy 2.0 |
| Migrations | Flask-Migrate (Alembic) |
| Forms | Flask-WTF + WTForms |
| Frontend | Jinja2 + Bootstrap 5 + Chart.js |
| Testing | pytest + pytest-flask + pytest-cov |
| Data Generation | Faker |
| Load Testing | Locust |

---

## Project Structure

```
inventory/
├── run.py                          # Application entry point
├── wsgi.py                         # WSGI entry point for production
├── config.py                       # Configuration classes
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (git-ignored)
│
├── invent_app/                     # Main Flask application
│   ├── __init__.py                 # App factory
│   ├── models/
│   │   ├── normalized/             # 3NF schema models
│   │   │   ├── category.py
│   │   │   ├── supplier.py
│   │   │   ├── location.py
│   │   │   ├── item.py
│   │   │   ├── transaction.py
│   │   │   └── transaction_type.py
│   │   └── denormalized/           # Flat schema models (for benchmarking)
│   │       ├── item_denorm.py
│   │       └── transaction_denorm.py
│   ├── routes/
│   │   ├── main.py                 # Dashboard
│   │   ├── items.py
│   │   ├── categories.py
│   │   ├── suppliers.py
│   │   ├── transactions.py
│   │   └── reports.py
│   ├── forms/
│   ├── templates/
│   └── static/
│
├── performance/                    # Performance testing framework
│   ├── benchmarks/
│   │   ├── query_benchmarks.py
│   │   └── write_benchmarks.py
│   └── results/
│
├── tests/                          # Test suite
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_models.py
│   │   └── test_services.py
│   ├── integration/
│   │   ├── test_routes.py
│   │   └── test_database.py
│   └── performance/
│       └── test_performance.py
│
├── migrations/                     # Alembic migrations
└── scripts/
    ├── seed_data.py
    └── generate_test_data.py
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 13+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/EmmanuelDanso1/inventory.git
cd inventory
```

### 2. Create and activate virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://username:password@localhost:5432/inventorydb
SQLALCHEMY_ECHO=False
```

### 5. Create the database

```bash
# In PostgreSQL
create Database inventorydb;
```

### 6. Run migrations

```bash
python -m flask --app invent_app:create_app db init
python -m flask --app invent_app:create_app db migrate""
python -m flask --app invent_app:create_app db upgrade
```

### 7. Seed transaction types

```bash
python -m flask --app invent_app:create_app shell
```

Then in the shell:

```python
from invent_app import db
from invent_app.models.normalized.transaction_type import TransactionType

for name in ['STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT']:
    if not db.session.query(TransactionType).filter_by(type_name=name).first():
        db.session.add(TransactionType(type_name=name))

db.session.commit()
print("Done!")
```

### 8. Run the application

```bash
python run.py
```

Visit `http://127.0.0.1:5000`

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=invent_app

# Run specific suites
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# Verbose output with print statements
pytest -v -s
```

---

## Database Schema

### Normalized (3NF)

The primary schema follows Third Normal Form to eliminate data redundancy:

```
categories ──< items >── suppliers
                │
                └──< transactions >── transaction_types
```

- **categories** — Item categories (Electronics, Furniture, etc.)
- **suppliers** — Supplier information
- **locations** — Warehouse/shelf locations
- **items** — Core inventory items with FK references
- **transaction_types** — STOCK_IN, STOCK_OUT, ADJUSTMENT
- **transactions** — Every stock movement event

### Denormalized (Flat)

A flat schema used for performance benchmarking:

- **items_denormalized** — All item + category + supplier + location data in one table
- **transactions_denormalized** — All transaction + item + type data in one table

---

## Performance Benchmarks

Visit `/reports/performance` and click **Run Benchmarks** to compare query performance between both schemas. The benchmark runs 6 query types × 5 iterations each and reports average, min, and max times in milliseconds.

Typical results on a local PostgreSQL instance:

| Query | Normalized | Denormalized | Winner |
|---|---|---|---|
| Get All Items | ~2ms | ~0.3ms | Denormalized |
| Filter by Category | ~0.5ms | ~0.3ms | Denormalized |
| Low Stock Items | ~0.4ms | ~0.5ms | Normalized |
| Stock Value by Category | ~0.6ms | ~0.6ms | Tie |
| Recent Transactions | ~0.7ms | ~0.3ms | Denormalized |
| Stock In Totals | ~0.7ms | ~0.4ms | Denormalized |

---

## Key Routes

| Route | Description |
|---|---|
| `/dashboard` | Main overview dashboard |
| `/items/` | Item list with search and filter |
| `/items/create` | Add new item |
| `/transactions/stock-in` | Record stock in |
| `/transactions/stock-out` | Record stock out |
| `/reports/stock-levels` | Current stock levels |
| `/reports/low-stock` | Low stock alerts |
| `/reports/movement-history` | Transaction history |
| `/reports/category-summary` | Summary by category |
| `/reports/inventory-valuation` | Total inventory value |
| `/reports/performance` | Schema performance benchmarks |

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Flask secret key | `supersecretkey123` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost/inventorydb` |
| `SQLALCHEMY_ECHO` | Log SQL queries to console | `False` |

---