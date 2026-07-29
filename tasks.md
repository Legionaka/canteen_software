# CampusEats — Project Specification
> College canteen ordering system · Flask + Supabase (PostgreSQL) + HTML/CSS/JS

---

## 👥 Team

| Developer | Role | Owns |
|-----------|------|------|
| **Ammara** | Database | Supabase schema, `models.py`, `seed.py` |
| **Legion** | Backend | `app.py`, `utils.py`, all files in `routes/` |
| **Tino** | Frontend | All `templates/`, `static/css/`, `static/js/` |

> Legion imports from `models.py` but never edits it. Ammara imports nothing from routes. Tino always uses `{{ url_for() }}`, never hardcoded URLs.

---

## 🗂️ Project Structure

```
campuseats/
│
├── app.py
├── models.py
├── seed.py
├── utils.py
├── .env                        # never commit
├── .gitignore
│
├── routes/
│   ├── auth.py
│   ├── student.py
│   ├── staff.py
│   └── admin.py
│
├── templates/
│   ├── base.html
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── student/
│   │   ├── menu.html
│   │   └── track.html
│   ├── staff/
│   │   └── dashboard.html
│   └── admin/
│       ├── dashboard.html
│       ├── menu.html
│       ├── orders.html
│       └── students.html
│
├── static/
│   ├── css/style.css
│   └── js/
│       ├── menu.js
│       ├── staff.js
│       └── admin.js
│
└── requirements.txt
```

---

## 🗄️ AMMARA — Database

### Supabase Project
- Project name: `campuseats`
- Share `DATABASE_URL` and `SECRET_KEY` with Legion via `.env`
- RLS disabled on all tables for development

---

### Tables & Columns

#### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | Serial PK | |
| student_number | VARCHAR | Nullable — staff/admin have none |
| name | VARCHAR | |
| email | VARCHAR UNIQUE | |
| password_hash | VARCHAR | |
| role | VARCHAR | `'student'` · `'staff'` · `'admin'` |
| is_active | Boolean | Default true |
| created_at | Timestamp | Auto |

#### `menu_items`
| Column | Type | Notes |
|--------|------|-------|
| id | Serial PK | |
| name | VARCHAR | |
| description | VARCHAR | |
| price | Float | In Rands |
| category | VARCHAR | `'mains'` · `'snacks'` · `'drinks'` · `'breakfast'` |
| emoji | VARCHAR | |
| dietary | VARCHAR | `'none'` · `'vegetarian'` · `'halal'` · `'vegan'` |
| is_available | Boolean | Default true |
| created_at | Timestamp | Auto |

#### `promotions`
| Column | Type | Notes |
|--------|------|-------|
| id | Serial PK | |
| name | VARCHAR | |
| type | VARCHAR | `'flat'` · `'percent'` · `'loyalty'` |
| discount_value | Float | |
| is_active | Boolean | Default true |
| valid_from | Date | Nullable |
| valid_until | Date | Nullable |

#### `orders`
| Column | Type | Notes |
|--------|------|-------|
| id | Serial PK | |
| user_id | Integer FK | → users.id |
| promo_id | Integer FK | → promotions.id, nullable |
| status | VARCHAR | `'new'` · `'preparing'` · `'ready'` · `'collected'` |
| pickup_slot | VARCHAR | e.g. `"12:15"` |
| subtotal | Float | |
| service_fee | Float | Default 2.0 |
| total | Float | |
| pickup_code | VARCHAR UNIQUE | 5-char, auto-generated |
| created_at | Timestamp | Auto |

#### `order_items`
| Column | Type | Notes |
|--------|------|-------|
| id | Serial PK | |
| order_id | Integer FK | → orders.id, cascade delete |
| menu_item_id | Integer FK | → menu_items.id |
| quantity | Integer | |
| unit_price | Float | Snapshot of price at time of order |

#### `loyalty_points`
| Column | Type | Notes |
|--------|------|-------|
| id | Serial PK | |
| user_id | Integer FK | → users.id |
| order_id | Integer FK | → orders.id |
| points_earned | Integer | Default 1 |
| points_balance | Integer | Running total |
| awarded_at | Timestamp | Auto |

---

### Table Relationships

```
users ──────────< orders >──────────< order_items >────────── menu_items
                     │
                     ├──────────── promotions (nullable)
                     │
                     └──────────── loyalty_points
```

---

### `models.py` — SQLAlchemy Classes

| Class | Table | Relationships | Methods |
|-------|-------|---------------|---------|
| `User` | users | `orders`, `loyalty` | `set_password()`, `check_password()`, `loyalty_balance` (property) |
| `MenuItem` | menu_items | `order_items` | `to_dict()` |
| `Promotion` | promotions | `orders` | — |
| `Order` | orders | `items` (cascade), `loyalty_record` | `__init__()` auto pickup_code, `to_dict()` |
| `OrderItem` | order_items | — | `to_dict()` |
| `LoyaltyPoints` | loyalty_points | — | — |

`Order.to_dict()` includes a nested list from `OrderItem.to_dict()`
`MenuItem.to_dict()` is what Legion passes to every template and JSON response

---

### `seed.py` — Sample Data(Placeholders - will obtain real menu items in future)

**Users**
| Name | Email | Role | Student No. |
|------|-------|------|-------------|
| Legion C | legion@campus.ac.za | student | STU2024001 |
| Staff User | staff@campus.ac.za | staff | — |
| Admin User | admin@campus.ac.za | admin | — |
All passwords: `password123`

**Menu Items**
| Name | Price | Category | Dietary | Available |
|------|-------|----------|---------|-----------|
| Beef Bunny Chow | R38 | mains | none | ✅ |
| Grilled Chicken Wrap | R42 | mains | halal | ✅ |
| Veggie Burger | R35 | mains | vegetarian | ✅ |
| Pap & Chakalaka | R28 | mains | vegetarian | ✅ |
| Boerewors Roll | R30 | snacks | none | ✅ |
| Samoosa x2 | R15 | snacks | halal | ✅ |
| Fruit Cup | R22 | snacks | vegetarian | ✅ |
| Cheese Toastie | R20 | snacks | vegetarian | ❌ |
| Rooibos Tea | R12 | drinks | vegetarian | ✅ |
| Coke 330ml | R14 | drinks | none | ✅ |
| Jungle Oats | R18 | breakfast | vegetarian | ✅ |
| Egg & Bacon Roll | R25 | breakfast | none | ✅ |

**Promotions**
| Name | Type | Discount |
|------|------|----------|
| Daily Special: Bunny Chow + Coke | flat | R9.00 |
| 10th Meal Free | loyalty | R30.00 |

**Orders** — one each with status `'new'`, `'preparing'`, `'collected'`
The `'collected'` order must have a matching `loyalty_points` row.

---

## ⚙️ LEGION — Backend

### Dependencies (`requirements.txt`)
`flask` · `flask-sqlalchemy` · `werkzeug` · `python-dotenv` · `psycopg2-binary`

---

### `app.py`
- Flask app factory
- Reads DB config from `.env`
- Connection pooling enabled
- Registers all 4 blueprints

### `utils.py`
- `login_required` — checks `session['user_id']`
- `role_required(*roles)` — checks `session['role']`

---

### `routes/auth.py`

| Route | Method | Action |
|-------|--------|--------|
| `/login` | GET | Render login page |
| `/login` | POST | Validate credentials → set session → redirect by role |
| `/register` | GET | Render register page |
| `/register` | POST | Create student user → redirect to login |
| `/logout` | GET | Clear session → redirect to login |

Session keys set on login: `user_id`, `role`
Role redirects: `student → /menu` · `staff → /staff` · `admin → /admin`

---

### `routes/student.py`

| Route | Method | Accepts | Returns |
|-------|--------|---------|---------|
| `/menu` | GET | — | Template + `items` list |
| `/order` | POST | Cart JSON | `{"order_id": id}` |
| `/order/<id>/track` | GET | — | Template + `order` dict |
| `/order/<id>/status` | GET | — | `{"status": "..."}` |

Cart JSON shape: `{ cart: [{menu_item_id, quantity}], pickup_slot }`
`/order` validates `is_available=True` for every item before creating anything.
`unit_price` on each `OrderItem` is copied from `MenuItem.price` at creation time — never referenced live.

---

### `routes/staff.py`

| Route | Method | Accepts | Returns |
|-------|--------|---------|---------|
| `/staff` | GET | — | Template + order lists + menu items |
| `/staff/order/<id>/status` | POST | `new_status` | Redirect `/staff` |
| `/staff/menu/<id>/toggle` | POST | — | Redirect `/staff` |
| `/staff/orders/live` | GET | — | JSON of all active orders |

Status progression: `new → preparing → ready → collected`
When status becomes `collected`: a `LoyaltyPoints` row is created (balance = previous + 1)
Template receives: `new_orders`, `preparing_orders`, `ready_orders`, `menu_items`

---

### `routes/admin.py`

| Route | Method | Returns |
|-------|--------|---------|
| `/admin` | GET | Template + stats dict + recent orders |
| `/admin/stats` | GET | `{hourly: [...], top_items: [...]}` |
| `/admin/menu` | GET | Template + all menu items |
| `/admin/menu/add` | POST | Redirect `/admin/menu` |
| `/admin/menu/<id>/edit` | POST | Redirect `/admin/menu` |
| `/admin/menu/<id>/delete` | POST | Redirect `/admin/menu` |
| `/admin/orders` | GET | Template + all orders |
| `/admin/students` | GET | Template + all students |

Stats dict contains: `total_orders_today`, `revenue_today`, `active_students`, `avg_wait_minutes`
Delete is blocked if the item exists in any non-collected order.

---

## 🎨 TINO — Frontend

### Design Tokens

| Token | Value |
|-------|-------|
| Student/Admin bg | `#F7F4EF` |
| Student/Admin surface | `#FFFFFF` |
| Student/Admin border | `#E2DDD6` |
| Staff bg | `#111210` |
| Staff surface | `#1C1D1A` |
| Staff border | `#2E2F2B` |
| Accent orange | `#E85D24` |
| Accent navy | `#2E4057` |
| Body font | DM Sans (Google Fonts) |
| Heading font | Syne (Google Fonts) |
| Card radius | `10–12px` |
| Pill radius | `20px` |
| Input radius | `7–8px` |

No `box-shadow`. No glow. Hover = `border-color` change only.

---

### Templates

| File | Variables from Legion | Key UI Elements |
|------|-----------------------|-----------------|
| `base.html` | `current_user_name`, `current_role` | Role-aware nav, flash messages |
| `auth/login.html` | — | Email + password form |
| `auth/register.html` | — | Name, student number, email, password |
| `student/menu.html` | `items` | Category tabs, search, 2-col card grid, cart sidebar, pickup slot select |
| `student/track.html` | `order` | Pickup code (large), 4-step progress bar, items list |
| `staff/dashboard.html` | `new_orders`, `preparing_orders`, `ready_orders`, `menu_items` | 3-col Kanban (dark), stats bar, sold-out chips |
| `admin/dashboard.html` | `stats`, `recent_orders` | Stat cards, hourly bar chart, top items, orders table |
| `admin/menu.html` | `menu_items` | Filter tabs, table, add item modal |
| `admin/orders.html` | `orders` | Orders table, status pills, date filter |
| `admin/students.html` | `students` | Table with order count + loyalty balance |

---

### JS Files

| File | Connects to | Responsibility |
|------|-------------|----------------|
| `menu.js` | `POST /order` | Cart state, add/remove items, submit order, redirect on success |
| `staff.js` | `POST /staff/order/<id>/status`, `POST /staff/menu/<id>/toggle`, `GET /staff/orders/live` | Move order cards, toggle sold-out chips, auto-refresh every 10s |
| `admin.js` | `GET /admin/stats` | Render Chart.js hourly bar, render top items bars |

`track.html` has inline JS only — polls `GET /order/<id>/status` every 5s to update the progress bar.

---

## 🔗 How Everything Connects

```
Ammara's models.py
    ↓ imported by
Legion's routes → query Supabase → pass data as dicts to
    ↓ render_template() with variables
Tino's templates → display data, forms and JS send requests back to
    ↓ Legion's routes
```

**Key data contracts between Legion and Tino:**

| What Legion passes | Where Tino uses it |
|--------------------|--------------------|
| `items` → list of `MenuItem.to_dict()` | `student/menu.html` card grid |
| `order` → `Order.to_dict()` (includes nested items) | `student/track.html` |
| `new_orders`, `preparing_orders`, `ready_orders` | `staff/dashboard.html` columns |
| `menu_items` | `staff/dashboard.html` sold-out chips + `admin/menu.html` table |
| `stats` dict | `admin/dashboard.html` stat cards + chart data |

---

## ✅ Task Checklists

### Ammara
- [✓] Supabase project set up, `DATABASE_URL` shared with Legion
- [✓] All 6 tables created in Supabase
- [✓] RLS disabled on all tables
- [ ] `models.py` — all 6 classes with relationships and methods
- [ ] `seed.py` — users, menu items, promotions, sample orders

### Legion
- [ ] `.gitignore`
- [ ] `requirements.txt`
- [ ] `app.py`
- [ ] `utils.py` — `login_required`, `role_required`
- [ ] `routes/auth.py`
- [ ] `routes/student.py`
- [ ] `routes/staff.py`
- [ ] `routes/admin.py`

### Tino
- [ ] `base.html`
- [ ] `auth/login.html`, `auth/register.html`
- [ ] `student/menu.html`, `student/track.html`
- [ ] `staff/dashboard.html`
- [ ] `admin/dashboard.html`, `admin/menu.html`, `admin/orders.html`, `admin/students.html`
- [ ] `static/css/style.css`
- [ ] `static/js/menu.js`, `static/js/staff.js`, `static/js/admin.js`

---

## 🚀 Test Logins (from seed data)

| Email | Password | Role |
|-------|----------|------|
| legion@campus.ac.za | password123 | Student |
| staff@campus.ac.za | password123 | Staff |
| admin@campus.ac.za | password123 | Admin |
