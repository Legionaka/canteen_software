bash

cat > /home/claude/campuseats/CAMPUSEATS_SPEC.md << 'ENDOFFILE'
# CampusEats — Full Project Specification
> College canteen ordering system · Flask + SQLite + HTML/CSS/JS

---

## 👥 Team

| Developer | Role | Responsibility |
|-----------|------|----------------|
| **Legion** | Backend | Flask app, database models, API routes, business logic |
| **Tino** | Frontend | HTML templates, CSS styling, JavaScript interactivity |

---

## 🗂️ Project Structure

```
campuseats/
│
├── app.py                  # Legion — Flask app factory, config, run
├── models.py               # Legion — All SQLAlchemy database models
├── routes/
│   ├── auth.py             # Legion — Login, register, logout
│   ├── student.py          # Legion — Menu, cart, place order, track order
│   ├── staff.py            # Legion — Order queue, mark ready, sold out toggle
│   └── admin.py            # Legion — Menu CRUD, stats, user management
│
├── templates/
│   ├── base.html           # Tino — Shared layout, navbar, footer
│   ├── auth/
│   │   ├── login.html      # Tino
│   │   └── register.html   # Tino
│   ├── student/
│   │   ├── menu.html       # Tino — Main menu + cart UI
│   │   └── track.html      # Tino — Order tracking screen
│   ├── staff/
│   │   └── dashboard.html  # Tino — Kanban order queue
│   └── admin/
│       ├── dashboard.html  # Tino — Stats + charts
│       ├── menu.html       # Tino — Menu manager table
│       ├── orders.html     # Tino — All orders table
│       └── students.html   # Tino — Student accounts table
│
├── static/
│   ├── css/
│   │   └── style.css       # Tino — Global styles
│   └── js/
│       ├── menu.js         # Tino — Cart logic, add/remove items
│       ├── staff.js        # Tino — Move orders between columns
│       └── admin.js        # Tino — Charts, table filters
│
├── seed.py                 # Legion — Populate DB with sample data
└── requirements.txt        # Legion — Python dependencies
```

---

## 🗄️ Database — Legion

### How the tables connect

```
users ──────────< orders >──────────< order_items >────────── menu_items
                     │
                     ├──────────── promotions
                     │
                     └──────────── loyalty_points
```

### Table descriptions

#### `users`
Stores every person using the app. One table for all roles.

| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | Auto-increment |
| student_number | VARCHAR | e.g. STU2024001, nullable for staff/admin |
| name | VARCHAR | Full name |
| email | VARCHAR UNIQUE | Login email |
| password_hash | VARCHAR | Never store plain passwords — use `werkzeug.security` |
| role | VARCHAR | `'student'` · `'staff'` · `'admin'` |
| is_active | BOOL | Soft disable accounts without deleting |
| created_at | DATETIME | Auto-set on insert |

**Connected to:** `orders` (one user → many orders), `loyalty_points` (one user → many records)

---

#### `menu_items`
Every item the canteen sells.

| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | Auto-increment |
| name | VARCHAR | e.g. "Beef Bunny Chow" |
| description | VARCHAR | Short description shown on menu card |
| price | FLOAT | In Rands, e.g. 38.0 |
| category | VARCHAR | `'mains'` · `'snacks'` · `'drinks'` · `'breakfast'` |
| emoji | VARCHAR | Single emoji for the card, e.g. 🍞 |
| dietary | VARCHAR | `'none'` · `'vegetarian'` · `'halal'` · `'vegan'` |
| is_available | BOOL | Staff toggle sold-out from dashboard |
| created_at | DATETIME | Auto-set on insert |

**Connected to:** `order_items` (one menu item → many order_items across all orders)

---

#### `orders`
One row per student order placed.

| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | Auto-increment |
| user_id | INT FK → users.id | Who placed the order |
| promo_id | INT FK → promotions.id | Nullable — only set if promo applied |
| status | VARCHAR | `'new'` → `'preparing'` → `'ready'` → `'collected'` |
| pickup_slot | VARCHAR | e.g. "12:15" |
| subtotal | FLOAT | Sum of all order_items line totals |
| service_fee | FLOAT | Default R2.00 |
| total | FLOAT | subtotal + service_fee − discount |
| pickup_code | VARCHAR UNIQUE | 5-char code shown to student, e.g. "AB7K2" |
| created_at | DATETIME | Auto-set on insert |

**Connected to:** `users` (FK), `order_items` (one order → many items), `promotions` (FK, nullable), `loyalty_points` (one order → one loyalty record)

---

#### `order_items`
Junction table — links orders to menu items. One row per item line in an order.

| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | Auto-increment |
| order_id | INT FK → orders.id | Which order |
| menu_item_id | INT FK → menu_items.id | Which item |
| quantity | INT | How many of this item |
| unit_price | FLOAT | **Snapshot** of price at time of order (price may change later) |

> ⚠️ **Why unit_price?** If the canteen changes a price, old orders must still show the original price. Always copy `menu_item.price` into `unit_price` when creating the order.

**Connected to:** `orders` (FK) and `menu_items` (FK)

---

#### `promotions`
Discounts, daily specials, and loyalty rewards.

| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | Auto-increment |
| name | VARCHAR | e.g. "Bunny Chow + Coke Friday Special" |
| type | VARCHAR | `'flat'` (R10 off) · `'percent'` (15% off) · `'loyalty'` (free item) |
| discount_value | FLOAT | Amount or percentage to deduct |
| is_active | BOOL | Toggle on/off from admin panel |
| valid_from | DATE | Nullable — optional date range |
| valid_until | DATE | Nullable |

**Connected to:** `orders` (one promo → many orders that used it)

---

#### `loyalty_points`
Tracks points earned per order and maintains a running balance per student.

| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | Auto-increment |
| user_id | INT FK → users.id | Which student |
| order_id | INT FK → orders.id | Which order earned these points |
| points_earned | INT | Usually 1 point per order |
| points_balance | INT | Running total at time of this record |
| awarded_at | DATETIME | Auto-set on insert |

> 💡 Every time an order reaches `'collected'`, Legion's backend creates a `LoyaltyPoints` row. At 10 points the student gets a free item.

---

## ⚙️ Backend — Legion

### `app.py`
Sets up Flask, connects the database, registers route blueprints.

```python
# What Legion needs to do here:
# 1. Create Flask app instance
# 2. Configure SQLite database URI
# 3. Initialise SQLAlchemy with the app (db.init_app)
# 4. Register blueprints: auth, student, staff, admin
# 5. Create all tables on first run (db.create_all)
# 6. Set a SECRET_KEY for session management
```

**Connects to:** `models.py` (imports db), all files in `routes/`

---

### `routes/auth.py`
Handles login, registration, logout. Uses Flask sessions.

| Route | Method | What it does |
|-------|--------|--------------|
| `/login` | GET | Render login.html |
| `/login` | POST | Check email + password → set `session['user_id']` and `session['role']` → redirect |
| `/register` | GET | Render register.html |
| `/register` | POST | Create new User, hash password, save to DB → redirect to login |
| `/logout` | GET | Clear session → redirect to login |

**Key functions:**
- `login()` — query `User` by email, call `user.check_password()`, set session
- `register()` — validate form, create `User`, call `user.set_password()`, `db.session.add()`, `db.session.commit()`
- `login_required` decorator — check `session['user_id']` exists, else redirect to `/login`
- `role_required(role)` decorator — check `session['role']` matches, else 403

---

### `routes/student.py`
Everything the student interacts with after login.

| Route | Method | What it does |
|-------|--------|--------------|
| `/menu` | GET | Query all available `MenuItem` → render menu.html |
| `/order` | POST | Receive cart JSON, create `Order` + `OrderItem` rows, return order id |
| `/order/<id>/track` | GET | Query `Order` by id → render track.html with status |
| `/order/<id>/status` | GET | JSON endpoint — Tino's JS polls this every 5s to update status live |

**Key functions:**
- `place_order()` — receives `{cart: [{menu_item_id, quantity}], pickup_slot}` as JSON. Validates each item is available. Calculates subtotal. Creates `Order` then loops through cart to create `OrderItem` rows. Commits everything together.
- `get_order_status()` — returns `{"status": "preparing"}` as JSON for the polling endpoint

**Connects to:** `MenuItem`, `Order`, `OrderItem` models

---

### `routes/staff.py`
The kitchen-facing order queue.

| Route | Method | What it does |
|-------|--------|--------------|
| `/staff` | GET | Query all non-collected orders → render staff/dashboard.html |
| `/staff/order/<id>/status` | POST | Update `order.status` → redirect back |
| `/staff/menu/<id>/toggle` | POST | Flip `menu_item.is_available` → redirect back |
| `/staff/orders/live` | GET | JSON of all active orders — for auto-refresh |

**Key functions:**
- `update_order_status()` — receives `new_status` from form, validates it's a legal transition, updates and commits. If status becomes `'collected'`, also calls `award_loyalty_point()`
- `award_loyalty_point()` — creates a `LoyaltyPoints` row. Gets the student's previous balance, adds 1.
- `toggle_availability()` — flips `is_available` on a `MenuItem`

**Connects to:** `Order`, `MenuItem`, `LoyaltyPoints` models

---

### `routes/admin.py`
Full control panel for the canteen manager.

| Route | Method | What it does |
|-------|--------|--------------|
| `/admin` | GET | Aggregate stats + recent orders → render admin/dashboard.html |
| `/admin/menu` | GET | All menu items → render admin/menu.html |
| `/admin/menu/add` | POST | Create new `MenuItem` from form data |
| `/admin/menu/<id>/edit` | POST | Update existing `MenuItem` |
| `/admin/menu/<id>/delete` | POST | Delete `MenuItem` |
| `/admin/orders` | GET | All orders, filterable by status/date |
| `/admin/students` | GET | All students + order count + loyalty balance |
| `/admin/stats` | GET | JSON stats for charts (orders per hour, top items) |

**Key functions:**
- `dashboard()` — runs aggregate queries: total orders today, total revenue today, avg wait time, active student count
- `get_stats()` — returns JSON used by Tino's chart JS: `{hourly: [...], top_items: [...]}`
- `add_menu_item()` — validates form, creates and commits new `MenuItem`
- `delete_menu_item()` — checks no active orders use this item before deleting

**Connects to:** All models

---

## 🎨 Frontend — Tino

### Design rules
- Dark theme for Staff dashboard (`#111210` background)
- Light warm theme for Student menu and Admin panel (`#F7F4EF` background)
- Font: `DM Sans` for body, `Syne` for headings (Google Fonts)
- No box-shadow or glow effects — use `border: 0.5px solid` for card outlines
- Accent colour: `#E85D24` (orange) for buttons and highlights
- All hover states: change `border-color` only, no shadows
- Rounded cards: `border-radius: 10px–12px`

---

### `templates/base.html`
The shared layout every other template extends.

```html
<!-- What Tino builds here: -->
<!-- 1. <head> with Google Fonts link, CSS link, meta tags -->
<!-- 2. <nav> with logo, role-aware links (student/staff/admin show different navs) -->
<!-- 3. {% block content %}{% endblock %} for page content -->
<!-- 4. Flash message display (Legion will flash messages from routes) -->
<!-- 5. <script> tags for JS files at bottom -->
```

**Jinja variables Legion will pass:** `current_user` (name, role), `flash messages`

---

### `templates/student/menu.html`
The main student screen. Extends `base.html`.

**What Tino builds:**
- Category filter tabs (All / Mains / Snacks / Drinks / Breakfast)
- Search bar
- Menu item cards in a 2-column grid showing emoji, name, description, price, add button
- Sticky cart panel on the right showing items, subtotal, total, pickup slot selector
- "Place order" button that submits cart to Legion's `/order` POST route

**JS file: `static/js/menu.js`**
- Manages cart state (add, remove, change quantity) in a JS object
- On "Place order" click: `fetch('/order', {method:'POST', body: JSON.stringify(cart)})` → redirect to `/order/<id>/track`
- Category filter: show/hide cards by `data-category` attribute
- Search: filter cards by name as user types

**Jinja variables Legion will pass:** `menu_items` (list of dicts from `MenuItem.to_dict()`)

---

### `templates/student/track.html`
Order tracking page after placing an order.

**What Tino builds:**
- Large pickup code display (e.g. `AB7K2`)
- 4-step progress bar: Placed → Preparing → Ready → Collected
- Order items summary
- Auto-refreshing status (every 5 seconds)

**JS in page:**
```javascript
// Poll Legion's status endpoint every 5 seconds
setInterval(async () => {
  const res = await fetch('/order/{{ order.id }}/status');
  const data = await res.json();
  updateProgressBar(data.status); // Tino writes updateProgressBar()
}, 5000);
```

**Jinja variables Legion will pass:** `order` (id, status, pickup_code, items, pickup_slot)

---

### `templates/staff/dashboard.html`
Three-column Kanban board for kitchen staff.

**What Tino builds:**
- 3 columns: New Orders / Preparing / Ready for Pickup
- Each order card shows: order ID, student name, pickup slot, item list, action button
- Stats bar at top: new count, preparing count, completed today, avg wait
- Sold-out toggle chips at the bottom of the Ready column

**JS file: `static/js/staff.js`**
- "Start cooking" button → `fetch('/staff/order/<id>/status', {method:'POST', body: 'new_status=preparing'})` then move card to Preparing column
- "Mark ready" → same but `new_status=ready`
- "Collected" → `new_status=collected`
- Auto-refresh orders every 10 seconds via `/staff/orders/live` JSON endpoint

**Jinja variables Legion will pass:** `new_orders`, `preparing_orders`, `ready_orders` (lists of order dicts)

---

### `templates/admin/dashboard.html`
Overview page with stats and charts.

**What Tino builds:**
- 4 stat cards: Orders today, Revenue today, Avg wait, Active students
- Bar chart (orders per hour) — use Chart.js from CDN
- Horizontal bar chart (top items)
- Recent orders table

**JS file: `static/js/admin.js`**
```javascript
// Fetch stats from Legion's /admin/stats endpoint and render charts
fetch('/admin/stats')
  .then(r => r.json())
  .then(data => {
    renderHourlyChart(data.hourly);   // Tino writes this
    renderTopItems(data.top_items);   // Tino writes this
  });
```

**Jinja variables Legion will pass:** `stats` dict, `recent_orders` list

---

### `templates/admin/menu.html`
Menu management table.

**What Tino builds:**
- Category filter tabs
- Table with columns: Item, Category, Price, Dietary, Available toggle, Edit/Delete buttons
- "Add item" button that opens a modal form
- Modal form: name, emoji, price, category, description, dietary dropdowns

**How it connects to Legion:**
- The available toggle is a `<form method="POST" action="/admin/menu/<id>/toggle">` — no JS needed, plain form submit
- Add item modal submits to `POST /admin/menu/add`
- Delete button submits to `POST /admin/menu/<id>/delete`

---

## 🔗 How everything connects end-to-end

### Example flow: Student places an order

```
1. Tino's menu.html loads
   └── Legion's GET /menu route queries MenuItem table, passes list to template

2. Student adds items → Tino's menu.js updates cart object in memory

3. Student clicks "Place Order"
   └── Tino's menu.js sends POST /order with JSON cart

4. Legion's place_order() route:
   └── Creates Order row (status='new', generates pickup_code)
   └── Loops cart → creates OrderItem rows (copies price snapshot)
   └── Commits to DB
   └── Returns {"order_id": 42}

5. Tino's JS redirects to /order/42/track

6. Tino's track.html renders with order data
   └── JS polls GET /order/42/status every 5s

7. Staff sees order in New column on staff dashboard
   └── Clicks "Start cooking" → POST /staff/order/42/status (preparing)
   └── Clicks "Mark ready" → POST /staff/order/42/status (ready)

8. Tino's polling detects status='ready'
   └── Progress bar jumps to step 3, student goes to collect

9. Staff clicks "Collected" → POST /staff/order/42/status (collected)
   └── Legion's route also calls award_loyalty_point(user_id=student.id, order_id=42)
```

---

## 📦 Dependencies — Legion sets up

**`requirements.txt`**
```
flask
flask-sqlalchemy
werkzeug
```

Install with:
```bash
pip install -r requirements.txt
```

---

## 🚀 How to run

```bash
# 1. Clone / set up the project folder
cd campuseats

# 2. Install dependencies (Legion)
pip install -r requirements.txt

# 3. Seed the database with sample data (Legion)
python seed.py

# 4. Run the app
python app.py

# 5. Open in browser
# http://localhost:5000
```

---

## ✅ Task Checklist

### Legion — Backend
- [ ] `app.py` — Flask setup, DB config, blueprint registration
- [ ] `models.py` — All 6 SQLAlchemy models
- [ ] `routes/auth.py` — Login, register, logout, decorators
- [ ] `routes/student.py` — Menu GET, order POST, track GET, status JSON
- [ ] `routes/staff.py` — Dashboard, status update, toggle availability, live JSON
- [ ] `routes/admin.py` — Dashboard, menu CRUD, orders list, stats JSON
- [ ] `seed.py` — Sample menu items, test users (student/staff/admin)
- [ ] `requirements.txt`

### Tino — Frontend
- [ ] `templates/base.html` — Shared layout, nav, flash messages
- [ ] `templates/auth/login.html`
- [ ] `templates/auth/register.html`
- [ ] `templates/student/menu.html` — Menu grid + cart panel
- [ ] `templates/student/track.html` — Pickup code + progress bar
- [ ] `templates/staff/dashboard.html` — 3-column Kanban
- [ ] `templates/admin/dashboard.html` — Stats + charts
- [ ] `templates/admin/menu.html` — Menu table + add modal
- [ ] `templates/admin/orders.html` — Orders table + filters
- [ ] `templates/admin/students.html` — Student accounts table
- [ ] `static/css/style.css` — Global styles
- [ ] `static/js/menu.js` — Cart logic + order submission
- [ ] `static/js/staff.js` — Order column movement + auto-refresh
- [ ] `static/js/admin.js` — Chart rendering

---

## 📌 Important rules for both

1. **Never store plain passwords** — Legion uses `werkzeug.security.generate_password_hash`
2. **Always snapshot `unit_price`** — copy `menu_item.price` into `order_item.unit_price` at order creation time
3. **Check `is_available`** — Legion's `place_order()` must reject items with `is_available=False`
4. **Role checks on every route** — use the `login_required` and `role_required` decorators
5. **Tino uses `{{ url_for('blueprint.function') }}`** — never hardcode URLs in templates
6. **Legion flashes messages** — use `flash('Order placed!')` so Tino's base template can display them

ENDOFFILE
echo "Done"