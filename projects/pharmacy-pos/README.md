# 💊 PharmaPOS - Multi-Branch Point of Sale & FEFO Analytics System

A comprehensive Pharmacy Point of Sale (POS) and inventory administration suite engineered in Python, featuring a modern rose-accented graphical user interface, robust bcrypt credential security, an automated **FEFO (First Expired, First Out)** stock deduction engine, **multi-branch inventory synchronization**, and an interactive **Matplotlib Business Intelligence (KPI) dashboard**.

---

## 🌟 Key Architectural Features

- **Multi-Branch Operations**: Independent inventory tracking across multiple branches (e.g., Central, North Branch, South Branch) with per-branch reporting.
- **FEFO Inventory Algorithm**: Automatic dispatch of items based on expiration dates to minimize pharmaceutical waste.
- **Role-Based Access Control (RBAC)**: Secure privilege separation between Cashiers/Employees and System Administrators.
- **Interactive BI & Visual Analytics**: Live real-time KPIs (Daily Sales, Monthly Volume, Average Ticket Size) and embedded Matplotlib analytical trend charts.
- **Dual Database Persistence**: Native support for SQLite (zero-config local development) and enterprise MySQL Workbench / SQL Server.
- **Thermal Receipt Generation**: Formatted printable sales tickets with full batch numbers, expiration dates, and branch letterhead metadata.

---

## 🏗️ Architecture & File Structure

```text
pharmacy-pos/
├── farmacia_pos/
│   ├── assets/              # Branding logos, window icons, and UI graphics
│   ├── database/            # Database schema models & multivariant connection engine
│   │   ├── db.py            # SQLite/MySQL/SQLServer connection factory & migrations
│   │   └── models.py        # SQLAlchemy / Peewee schemas: Branches, Users, Products, Batches, Sales
│   ├── services/            # Core business logic layer
│   │   ├── auth_service.py      # Bcrypt hashing, session & RBAC management
│   │   ├── inventory_service.py # Multi-branch inventory tracking & FEFO batch selection
│   │   ├── sales_service.py     # Shopping cart, subtotal/tax calculations & transactions
│   │   └── analytics_service.py # Real-time KPI computations & chart aggregations
│   ├── ui/                  # TTK/Tkinter modern graphic interfaces
│   │   ├── styles.py        # Color palette (#C75B7A, #FDFBFB) & responsive TTK styling
│   │   ├── login_view.py    # Authentication portal with branch selector
│   │   ├── admin_view.py    # Executive dashboard (Charts, Branches, Batches, Reports)
│   │   └── pos_view.py      # Rapid checkout counter screen with barcode & FEFO validation
│   ├── utils/
│   │   └── printer.py       # Thermal ticket layout formatter and file export
│   └── main.py              # Application lifecycle & navigation router
├── requirements.txt         # Project dependencies
├── test_system.py           # Comprehensive integration & unit test suite
├── run_prod.py              # Production environment launcher
├── run_test.py              # Test environment launcher
└── README.md                # System documentation
```

---

## 🚀 Quickstart & Installation

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/nibeshlofreak-byte/portfolio.git
cd portfolio/projects/pharmacy-pos
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 2. Install Requirements
```bash
pip install -r requirements.txt
```

### 3. Run System Tests
```bash
python test_system.py
```

### 4. Launch Application
```bash
# Default mode (test with auto-seeded demo stock):
python main.py

# Explicit environment flag:
python main.py --env test
python main.py --env prod
```

---

## 📊 Technologies Used
- **Language**: Python 3.9+
- **GUI Engine**: Tkinter & TTK Custom Themes
- **Data Visualization**: Matplotlib
- **Security**: Bcrypt cryptographic password hashing
- **Data Persistence**: SQLite / MySQL / SQL Server
