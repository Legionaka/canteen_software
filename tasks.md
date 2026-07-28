# CampusEats — Full Project Specification
> College canteen ordering system · Flask + Supabase (PostgreSQL) + HTML/CSS/JS

---

## 👥 Team

| Developer | Role | Owns |
|-----------|------|------|
| **Ammara** | Database | Supabase schema, `models.py`, `seed.py`, migrations |
| **Legion** | Backend | `app.py`, `routes/auth.py`, `routes/student.py`, `routes/staff.py`, `routes/admin.py` |
| **Tino** | Frontend | All `templates/`, `static/css/`, `static/js/` |

> ⚠️ **Ground rule:** Legion imports from `models.py` but never edits it. Ammara imports nothing from routes. Tino uses `{{ url_for() }}` and never hardcodes URLs.

---

## 🗄️ Why Supabase + SQLAlchemy

We use **SQLAlchemy** (the same ORM as before) but point it at **Supabase's hosted PostgreSQL** database instead of a local SQLite file.

**What this means per person:**
- **Ammara** — creates tables in the Supabase dashboard (or via SQL editor) instead of relying on `db.create_all()`. She also provides the connection URL to Legion.
- **Legion** — only changes one line in `app.py` (the DB URL). All routes stay exactly the same.
- **Tino** — zero changes. Frontend is unaffected.

---

## 🗂️ Project Structure

```
campuseats/
│
├── app.py                  # Legion — Flask app factory, config, blueprints
├── models.py               # Ammara — SQLAlchemy models (maps to Supabase tables)
├── seed.py                 # Ammara — Populate Supabase with sample data
├── .env                    # Ammara sets up — stores Supabase credentials (never commit this)
├── .gitignore              # Legion — must include .env
│
├── routes/
│   ├── auth.py             # Legion
│   ├── student.py          # Legion
│   ├── staff.py            # Legion
│   └── admin.py            # Legion
│
├── templates/
│   ├── base.html           # Tino
│   ├── auth/
│   │   ├── login.html      # Tino
│   │   └── register.html   # Tino
│   ├── student/
│   │   ├── menu.html       # Tino
│   │   └── track.html      # Tino
│   ├── staff/
│   │   └── dashboard.html  # Tino
│   └── admin/
│       ├── dashboard.html  # Tino
│       ├── menu.html       # Tino
│       ├── orders.html     # Tino
│       └── students.html   # Tino
│
├── static/
│   ├── css/style.css       # Tino
│   └── js/
│       ├── menu.js         # Tino
│       ├── staff.js        # Tino
│       └── admin.js        # Tino
│
└── requirements.txt        # Legion
```

---

## 🗄️ AMMARA — Database (Supabase)

Ammara owns everything database-related. Legion and Tino depend on her finishing first.

---

### Step 1 — Create the Supabase project

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Click **New Project** — name it `campuseats`
3. Choose a strong database password and save it somewhere safe
4. Wait for the project to provision (~2 minutes)
5. Go to **Project Settings → Database** and copy the **Connection string** (URI format)
   It looks like: `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
6. Share this URL with Legion (privately — never put it in the GitHub repo)

---

### Step 2 — Create tables in Supabase

Go to the **SQL Editor** in the Supabase dashboard and run this SQL to create all tables:

```sql
-- Users table
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  student_number VARCHAR(20) UNIQUE,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(120) UNIQUE NOT NULL,
  password_hash VARCHAR(256) NOT NULL,
  role VARCHAR(10) NOT NULL DEFAULT 'student',
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Menu items table
CREATE TABLE menu_items (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description VARCHAR(200),
  price FLOAT NOT NULL,
  category VARCHAR(30) NOT NULL,
  emoji VARCHAR(5) DEFAULT '🍽️',
  dietary VARCHAR(20) DEFAULT 'none',
  is_available BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Promotions table
CREATE TABLE promotions (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  type VARCHAR(20) NOT NULL,
  discount_value FLOAT DEFAULT 0.0,
  is_active BOOLEAN DEFAULT TRUE,
  valid_from DATE,
  valid_until DATE
);

-- Orders table
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) NOT NULL,
  promo_id INTEGER REFERENCES promotions(id),
  status VARCHAR(20) DEFAULT 'new',
  pickup_slot VARCHAR(20) NOT NULL,
  subtotal FLOAT NOT NULL,
  service_fee FLOAT DEFAULT 2.0,
  total FLOAT NOT NULL,
  pickup_code VARCHAR(6) UNIQUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Order items table (junction table)
CREATE TABLE order_items (
  id SERIAL PRIMARY KEY,
  order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE NOT NULL,
  menu_item_id INTEGER REFERENCES menu_items(id) NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 1,
  unit_price FLOAT NOT NULL
);

-- Loyalty points table
CREATE TABLE loyalty_points (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) NOT NULL,
  order_id INTEGER REFERENCES orders(id) NOT NULL,
  points_earned INTEGER DEFAULT 1,
  points_balance INTEGER DEFAULT 0,
  awarded_at TIMESTAMP DEFAULT NOW()
);
```

> ✅ Run each block in the SQL Editor. Check the **Table Editor** after to confirm all 6 tables appeared.

---

### Step 3 — Disable Row Level Security (RLS) for development

Supabase enables RLS by default which will block all queries. For development, disable it:

```sql
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE menu_items DISABLE ROW LEVEL SECURITY;
ALTER TABLE promotions DISABLE ROW LEVEL SECURITY;
ALTER TABLE orders DISABLE ROW LEVEL SECURITY;
ALTER TABLE order_items DISABLE ROW LEVEL SECURITY;
ALTER TABLE loyalty_points DISABLE ROW LEVEL SECURITY;
```

> ⚠️ Re-enable and configure RLS properly before going to production.

---

### Step 4 — Set up the `.env` file

Create a `.env` file in the project root (Ammara fills this in, shares with Legion):

```
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
SECRET_KEY=some-random-secret-string-change-this
```

> 🚫 Add `.env` to `.gitignore` — never push credentials to GitHub.

---

### Step 5 — `models.py` (Ammara writes this)

Same SQLAlchemy models as before — the only difference is PostgreSQL-specific types.
Use `Text` instead of `String` where content could be long, and `SERIAL` is handled automatically by SQLAlchemy's `Integer` primary key.

#### Key differences from SQLite version:

| SQLite (old) | PostgreSQL/Supabase (new) |
|---|---|
| `db.String(n)` | Still fine for short fields, use `db.Text` for long ones |
| `db.create_all()` creates tables | Tables already created via SQL Editor — `db.create_all()` just verifies |
| Local `.db` file | Hosted Supabase cloud DB |
| No connection pooling needed | Add `pool_pre_ping=True` to engine config (Legion handles in app.py) |

#### All 6 model classes Ammara must write:

**`User`** — columns: id, student_number, name, email, password_hash, role, is_active, created_at
- Relationships: `orders`, `loyalty`
- Methods: `set_password()`, `check_password()`, `loyalty_balance` property

**`MenuItem`** — columns: id, name, description, price, category, emoji, dietary, is_available, created_at
- Relationships: `order_items`
- Methods: `to_dict()`

**`Promotion`** — columns: id, name, type, discount_value, is_active, valid_from, valid_until
- Relationships: `orders`

**`Order`** — columns: id, user_id (FK), promo_id (FK nullable), status, pickup_slot, subtotal, service_fee, total, pickup_code, created_at
- Relationships: `items` (cascade delete), `loyalty_record`
- Methods: `__init__()` (auto pickup_code), `to_dict()`

**`OrderItem`** — columns: id, order_id (FK), menu_item_id (FK), quantity, unit_price
- Methods: `to_dict()`

**`LoyaltyPoints`** — columns: id, user_id (FK), order_id (FK), points_earned, points_balance, awarded_at

> ⚠️ `unit_price` must always be copied from `MenuItem.price` at order creation time —
> never referenced live, so price changes don't break order history.

---

### Step 6 — `seed.py` (Ammara writes this)

```python
# What seed.py must create:

# Users (one of each role):
#   student: legion@campus.ac.za  / password123 / STU2024001
#   staff:   staff@campus.ac.za   / password123
#   admin:   admin@campus.ac.za   / password123

# Menu items (12 items across all categories):
#   Mains:     Beef Bunny Chow R38, Grilled Chicken Wrap R42,
#              Veggie Burger R35, Pap & Chakalaka R28
#   Snacks:    Boerewors Roll R30, Samoosa x2 R15, Fruit Cup R22,
#              Cheese Toastie R20 (is_available=False)
#   Drinks:    Rooibos Tea R12, Coke 330ml R14
#   Breakfast: Jungle Oats R18, Egg & Bacon Roll R25

# Promotions (2):
#   "Daily Special: Bunny Chow + Coke" — type='flat', discount_value=9.0, is_active=True
#   "10th Meal Free"                   — type='loyalty', discount_value=30.0, is_active=True

# Sample orders (3, different statuses):
#   Order 1: status='new'
#   Order 2: status='preparing'
#   Order 3: status='collected' + matching LoyaltyPoints row
```

Run seed with: `python seed.py`

---

### How tables connect

```
users ──────────< orders >──────────< order_items >────────── menu_items
                     │
                     ├──────────── promotions (nullable FK)
                     │
                     └──────────── loyalty_points
```

---

## ⚙️ LEGION — Backend

---

### `app.py` — Updated for Supabase

```python
import os
from flask import Flask
from models import db
from dotenv import load_dotenv

load_dotenv()  # reads .env file

def create_app():
    app = Flask(__name__)

    # Supabase PostgreSQL connection (from .env)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,       # reconnects if connection dropped
        'pool_recycle': 300,         # recycle connections every 5 min
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-fallback-key')

    db.init_app(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.staff import staff_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()  # safe to run — won't overwrite existing Supabase tables

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
```

> Legion must add `python-dotenv` to `requirements.txt` to load the `.env` file.

---

### `requirements.txt`

```
flask
flask-sqlalchemy
werkzeug
python-dotenv
psycopg2-binary
```

> `psycopg2-binary` is the PostgreSQL driver SQLAlchemy needs. Without it, the DB connection will fail.

---

### `utils.py` — Decorators Legion writes

```python
def login_required(f):
    # Check session['user_id'] exists
    # If not → redirect to /login

def role_required(*roles):
    # Check session['role'] is in allowed roles
    # If not → abort(403)
```

---

### `routes/auth.py`

| Route | Method | Action |
|-------|--------|--------|
| `/login` | GET | Render `auth/login.html` |
| `/login` | POST | Validate → set session → redirect by role |
| `/register` | GET | Render `auth/register.html` |
| `/register` | POST | Create User → redirect to `/login` |
| `/logout` | GET | Clear session → redirect to `/login` |

**`login()` logic:**
```
1. Get email + password from form
2. User.query.filter_by(email=email).first()
3. If no user or user.check_password() is False → flash error, re-render
4. session['user_id'] = user.id, session['role'] = user.role
5. Redirect: student→/menu | staff→/staff | admin→/admin
```

**`register()` logic:**
```
1. Get name, email, student_number, password from form
2. Check email not already in DB
3. Create User, call user.set_password(password)
4. db.session.add(user), db.session.commit()
5. flash('Account created.'), redirect to /login
```

---

### `routes/student.py`

| Route | Method | Action |
|-------|--------|--------|
| `/menu` | GET | Query available items → render student/menu.html |
| `/order` | POST | Receive cart JSON → create Order + OrderItems |
| `/order/<int:id>/track` | GET | Query Order → render student/track.html |
| `/order/<int:id>/status` | GET | Return `{"status": "..."}` JSON |

**`place_order()` logic:**
```
1. Parse JSON: {cart: [{menu_item_id, quantity}], pickup_slot}
2. Validate each item exists and is_available=True
3. Calculate subtotal
4. Create Order (pickup_code auto-generated by Ammara's __init__)
5. db.session.flush() to get order.id
6. Create OrderItem for each cart item (unit_price = menu_item.price snapshot)
7. db.session.commit()
8. Return {"order_id": order.id}
```

---

### `routes/staff.py`

| Route | Method | Action |
|-------|--------|--------|
| `/staff` | GET | Query active orders → render staff/dashboard.html |
| `/staff/order/<int:id>/status` | POST | Update order status |
| `/staff/menu/<int:id>/toggle` | POST | Flip MenuItem.is_available |
| `/staff/orders/live` | GET | JSON of all active orders |

**`update_status()` logic:**
```
1. Validate new_status is in ['preparing', 'ready', 'collected']
2. Update order.status, commit
3. If collected → call award_loyalty_point(order)
```

**`award_loyalty_point(order)` helper:**
```
1. Get student's last LoyaltyPoints row → current_balance
2. Create LoyaltyPoints(user_id, order_id, points_earned=1, points_balance=current_balance+1)
3. Commit
```

---

### `routes/admin.py`

| Route | Method | Action |
|-------|--------|--------|
| `/admin` | GET | Stats + recent orders → render admin/dashboard.html |
| `/admin/stats` | GET | JSON for charts |
| `/admin/menu` | GET | All items → render admin/menu.html |
| `/admin/menu/add` | POST | Create MenuItem |
| `/admin/menu/<int:id>/edit` | POST | Update MenuItem |
| `/admin/menu/<int:id>/delete` | POST | Delete MenuItem |
| `/admin/orders` | GET | All orders → render admin/orders.html |
| `/admin/students` | GET | All students → render admin/students.html |

**Stats queries:**
```python
from datetime import date
today = date.today()

total_orders  = Order.query.filter(db.func.date(Order.created_at) == today).count()
revenue       = db.session.query(db.func.sum(Order.total))\
                  .filter(db.func.date(Order.created_at) == today).scalar() or 0
active_students = User.query.filter_by(role='student', is_active=True).count()
```

---

## 🎨 TINO — Frontend

No changes from the original spec. Tino's work is completely unaffected by the SQLite → Supabase switch.

---

### Design rules (unchanged)
- **Student + Admin:** Light warm bg `#F7F4EF`, surface `#FFFFFF`, border `#E2DDD6`
- **Staff:** Dark bg `#111210`, surface `#1C1D1A`, border `#2E2F2B`
- **Accent orange:** `#E85D24` · **Accent navy:** `#2E4057`
- **Fonts:** `DM Sans` (body) + `Syne` (headings) via Google Fonts
- No box-shadow — `border: 0.5px solid` only
- Hover = `border-color` change only
- Border radius: `10–12px` cards, `20px` pills, `7–8px` inputs

---

### Templates Tino builds

| Template | Key elements |
|----------|-------------|
| `base.html` | Nav (role-aware), flash messages, font + CSS imports |
| `auth/login.html` | Email + password form, submit to POST /login |
| `auth/register.html` | Name, student number, email, password form |
| `student/menu.html` | Category tabs, search, 2-col card grid, sticky cart sidebar |
| `student/track.html` | Pickup code, 4-step progress bar, 5s polling JS |
| `staff/dashboard.html` | 3-col Kanban dark UI, stats bar, sold-out chips |
| `admin/dashboard.html` | Stats cards, Chart.js bar chart, top items, recent orders table |
| `admin/menu.html` | Filter tabs, table, add modal, toggle + delete forms |
| `admin/orders.html` | Orders table with status pills, date filter |
| `admin/students.html` | Student table with order count + loyalty points |

---

### JS files Tino builds

**`menu.js`**
```javascript
// Cart state: { menu_item_id: {name, emoji, price, quantity} }
// addItem(), removeItem(), renderCart()
// placeOrder() → POST /order → redirect to /order/{id}/track
```

**`staff.js`**
```javascript
// moveOrder(orderId, newStatus) → POST /staff/order/{id}/status
// toggleSoldOut(itemId) → POST /staff/menu/{id}/toggle
// Auto-refresh every 10s via GET /staff/orders/live
```

**`admin.js`**
```javascript
// On load: GET /admin/stats
// renderHourlyChart(data.hourly) — Chart.js
// renderTopItems(data.top_items) — CSS bars
```

---

## 🔗 End-to-end flow: Student places an order

```
1. Tino's menu.html loads
   └── Legion's GET /menu queries Supabase via SQLAlchemy (Ammara's MenuItem model)

2. Student adds items → Tino's menu.js manages cart in memory

3. Student clicks "Place Order"
   └── Tino's menu.js POSTs JSON cart to Legion's /order route

4. Legion's place_order():
   └── Validates items against Supabase (Ammara's MenuItem)
   └── Creates Order row in Supabase (pickup_code auto-generated)
   └── Creates OrderItem rows (unit_price snapshot)
   └── Returns {"order_id": 42}

5. Tino's JS redirects to /order/42/track

6. Tino's track.html polls /order/42/status every 5s

7. Staff sees order on Tino's Kanban dashboard
   └── "Start cooking" → Legion updates Supabase: status='preparing'
   └── "Mark ready"    → status='ready'
   └── "Collected"     → status='collected' + LoyaltyPoints row created

8. Tino's progress bar advances with each status change
```

---

## ✅ Task Checklists

### Ammara — Database
- [ ] Create Supabase project, copy connection URL
- [ ] Run SQL schema in Supabase SQL Editor (all 6 tables)
- [ ] Disable RLS for development
- [ ] Create `.env` file, share DATABASE_URL with Legion privately
- [ ] `models.py` — all 6 SQLAlchemy model classes + relationships + methods
- [ ] `seed.py` — 3 users, 12 menu items, 2 promos, 3 sample orders

### Legion — Backend
- [ ] `app.py` — Flask + Supabase DB config via `.env`, blueprint registration
- [ ] `.gitignore` — must include `.env` and `__pycache__`
- [ ] `utils.py` — `login_required`, `role_required` decorators
- [ ] `routes/auth.py` — login, register, logout
- [ ] `routes/student.py` — menu, place_order, track, status JSON
- [ ] `routes/staff.py` — dashboard, update_status, toggle, live JSON
- [ ] `routes/admin.py` — dashboard, stats JSON, menu CRUD, orders, students
- [ ] `requirements.txt` — flask, flask-sqlalchemy, werkzeug, python-dotenv, psycopg2-binary

### Tino — Frontend
- [ ] `base.html`, `login.html`, `register.html`
- [ ] `student/menu.html` + `student/track.html`
- [ ] `staff/dashboard.html`
- [ ] `admin/dashboard.html`, `menu.html`, `orders.html`, `students.html`
- [ ] `style.css`
- [ ] `menu.js`, `staff.js`, `admin.js`

---

## 📌 Rules for everyone

1. **Ammara never edits routes. Legion never edits models. Tino never hardcodes URLs.**
2. **`.env` is never committed to GitHub** — each dev runs with their own local copy
3. **Legion uses `python-dotenv`** — `load_dotenv()` at the top of `app.py`
4. **unit_price is always a snapshot** — copy `menu_item.price` at order creation time
5. **Passwords are never stored plain** — always call `user.set_password()`
6. **Legion checks `is_available`** before accepting any item in an order
7. **Tino uses `{{ url_for('blueprint.function') }}`** — never raw paths

---

## 🚀 Running the project

```bash
# 1. Clone the repo
git clone <repo-url>
cd campuseats

# 2. Install dependencies
pip install -r requirements.txt

# 3. Get the .env file from Ammara and place it in the project root

# 4. Seed the database (Ammara runs this first — only needs to be done once)
python seed.py

# 5. Run the Flask app
python app.py

# 6. Open in browser
http://localhost:5000

# Test logins (from Ammara's seed data):
# Student → legion@campus.ac.za / password123
# Staff   → staff@campus.ac.za  / password123
# Admin   → admin@campus.ac.za  / password123
```