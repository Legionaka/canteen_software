# CampusEats — Full Project Specification
> College canteen ordering system · Flask + SQLite + HTML/CSS/JS

---

## 👥 Team

| Developer | Role | Owns |
|-----------|------|------|
| **Ammara** | Database | `models.py`, `seed.py`, DB schema, migrations |
| **Legion** | Backend | `app.py`, `routes/auth.py`, `routes/student.py`, `routes/staff.py`, `routes/admin.py` |
| **Tino** | Frontend | All `templates/`, `static/css/`, `static/js/` |

> ⚠️ **Ground rule:** Legion imports from `models.py` but never edits it. Ammara imports nothing from routes. Tino uses `{{ url_for() }}` and never hardcodes URLs.

---

## 🗂️ Project Structure

```
campuseats/
│
├── app.py                  # Legion — Flask app factory, config, blueprints
├── models.py               # Ammara — All SQLAlchemy models
├── seed.py                 # Ammara — Sample data for development
│
├── routes/
│   ├── auth.py             # Legion — Login, register, logout
│   ├── student.py          # Legion — Menu, place order, track order
│   ├── staff.py            # Legion — Order queue, status updates
│   └── admin.py            # Legion — Menu CRUD, stats, user management
│
├── templates/
│   ├── base.html           # Tino — Shared layout, navbar, flash messages
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── student/
│   │   ├── menu.html       # Tino — Menu grid + cart sidebar
│   │   └── track.html      # Tino — Pickup code + progress bar
│   ├── staff/
│   │   └── dashboard.html  # Tino — 3-column Kanban board
│   └── admin/
│       ├── dashboard.html  # Tino — Stats + charts
│       ├── menu.html       # Tino — Menu manager table
│       ├── orders.html     # Tino — All orders table
│       └── students.html   # Tino — Student accounts
│
├── static/
│   ├── css/style.css       # Tino — Global styles
│   └── js/
│       ├── menu.js         # Tino — Cart logic + order submission
│       ├── staff.js        # Tino — Column movement + auto-refresh
│       └── admin.js        # Tino — Chart rendering
│
└── requirements.txt
```

---

## 🗄️ AMMARA — Database (Supabase)

Ammara owns everything related to the database. Legion and Tino depend on her finishing
`models.py` and `seed.py` first before they can test their own code.

### How the tables connect

```
users ──────────< orders >──────────< order_items >────────── menu_items
                     │
                     ├──────────── promotions (nullable FK)
                     │
                     └──────────── loyalty_points
```

---

### `models.py` — What Ammara builds

Six SQLAlchemy model classes. Each maps to one DB table.

---

#### Class: `User`
Table: `users`

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | Auto-increment |
| student_number | String | e.g. STU2024001 — nullable for staff/admin |
| name | String | Full name |
| email | String UNIQUE | Login email |
| password_hash | String | Never plain text — Legion calls `set_password()` |
| role | String | `'student'` · `'staff'` · `'admin'` |
| is_active | Boolean | Default True. Soft-disable without deleting |
| created_at | DateTime | Auto-set to `datetime.utcnow` |

**Relationships to define:**
- `orders` → one User has many Orders (`db.relationship('Order', backref='student')`)
- `loyalty` → one User has many LoyaltyPoints records

**Methods Ammara must add:**
```python
def set_password(self, password):
    # Legion calls this on register — hashes and stores password
    self.password_hash = generate_password_hash(password)

def check_password(self, password):
    # Legion calls this on login — returns True/False
    return check_password_hash(self.password_hash, password)

@property
def loyalty_balance(self):
    # Returns the student's current points total
    # Get the most recent LoyaltyPoints row for this user
    # Return points_balance, or 0 if no rows exist
```

---

#### Class: `MenuItem`
Table: `menu_items`

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | Auto-increment |
| name | String | e.g. "Beef Bunny Chow" |
| description | String | Short text shown on menu card |
| price | Float | In Rands e.g. 38.0 |
| category | String | `'mains'` · `'snacks'` · `'drinks'` · `'breakfast'` |
| emoji | String | Single emoji e.g. 🍞 |
| dietary | String | `'none'` · `'vegetarian'` · `'halal'` · `'vegan'` |
| is_available | Boolean | Default True. Staff toggles this to mark sold out |
| created_at | DateTime | Auto-set |

**Relationships to define:**
- `order_items` → one MenuItem appears in many OrderItems

**Method Ammara must add:**
```python
def to_dict(self):
    # Legion passes this to Tino's templates as JSON
    # Must return: id, name, description, price, category, emoji, dietary, is_available
```

---

#### Class: `Promotion`
Table: `promotions`

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | Auto-increment |
| name | String | e.g. "Bunny Chow Friday Special" |
| type | String | `'flat'` (R10 off) · `'percent'` (15% off) · `'loyalty'` (free item) |
| discount_value | Float | The amount or percentage |
| is_active | Boolean | Admin toggles this on/off |
| valid_from | Date | Nullable — optional start date |
| valid_until | Date | Nullable — optional end date |

**Relationships to define:**
- `orders` → one Promotion used in many Orders

---

#### Class: `Order`
Table: `orders`

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | Auto-increment |
| user_id | Integer FK → users.id | Who placed the order |
| promo_id | Integer FK → promotions.id | Nullable — only if promo applied |
| status | String | `'new'` → `'preparing'` → `'ready'` → `'collected'` |
| pickup_slot | String | e.g. "12:15" |
| subtotal | Float | Sum of all OrderItem line totals |
| service_fee | Float | Default 2.0 (R2) |
| total | Float | subtotal + service_fee − any discount |
| pickup_code | String UNIQUE | 5-char code shown to student e.g. "AB7K2" |
| created_at | DateTime | Auto-set |

**Relationships to define:**
- `items` → one Order has many OrderItems (cascade delete)
- `loyalty_record` → one Order generates one LoyaltyPoints row

**Method Ammara must add:**
```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    if not self.pickup_code:
        self.pickup_code = self._generate_code()

@staticmethod
def _generate_code():
    # Return a random 5-character uppercase alphanumeric string
    # Use random.choices(string.ascii_uppercase + string.digits, k=5)
    # Legion uses this code to display to the student on track.html

def to_dict(self):
    # Legion passes this to Tino's track.html and the JSON status endpoint
    # Must return: id, status, pickup_slot, subtotal, service_fee,
    #              total, pickup_code, created_at, items (list of OrderItem.to_dict())
```

---

#### Class: `OrderItem`
Table: `order_items`

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | Auto-increment |
| order_id | Integer FK → orders.id | Which order this line belongs to |
| menu_item_id | Integer FK → menu_items.id | Which menu item |
| quantity | Integer | How many of this item |
| unit_price | Float | ⚠️ Snapshot of price at time of order — copy from MenuItem.price |

> ⚠️ **Critical:** `unit_price` must be set from `menu_item.price` at the moment the order is created.
> If the canteen later changes a price, old order history stays correct.

**Method Ammara must add:**
```python
def to_dict(self):
    # Used inside Order.to_dict() to list each item in an order
    # Must return: menu_item_id, name, emoji, quantity, unit_price, line_total
    # line_total = unit_price * quantity (rounded to 2 decimal places)
```

---

#### Class: `LoyaltyPoints`
Table: `loyalty_points`

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | Auto-increment |
| user_id | Integer FK → users.id | Which student earned the points |
| order_id | Integer FK → orders.id | Which order triggered this |
| points_earned | Integer | Usually 1 per order |
| points_balance | Integer | Running total at the time of this record |
| awarded_at | DateTime | Auto-set |

> 💡 When Legion's staff route marks an order as `'collected'`, it calls a helper
> that creates a new `LoyaltyPoints` row. Ammara does NOT write that logic — Legion does.
> Ammara just defines the model so Legion can import and use it.

---

### `seed.py` — What Ammara builds

Populate the database with sample data so Tino and Legion can test without entering data manually.

**Ammara must seed:**

```
Users (at least one of each role):
  - student: legion@campus.ac.za / password123 / STU2024001
  - staff:   staff@campus.ac.za  / password123
  - admin:   admin@campus.ac.za  / password123

Menu items (at least 10 across all categories):
  Mains:     Beef Bunny Chow (R38), Grilled Chicken Wrap (R42),
             Veggie Burger (R35), Pap & Chakalaka (R28)
  Snacks:    Boerewors Roll (R30), Samoosa x2 (R15), Fruit Cup (R22)
             Cheese Toastie (R20) — set is_available=False
  Drinks:    Rooibos Tea (R12), Coke 330ml (R14)
  Breakfast: Jungle Oats (R18), Egg & Bacon Roll (R25)

Promotions (at least 2):
  - "Daily Special: Bunny Chow + Coke" — type='flat', discount_value=9.0, is_active=True
  - "10th Meal Free" — type='loyalty', discount_value=30.0, is_active=True

Sample orders (at least 3, with different statuses):
  - One order with status='new'
  - One with status='preparing'
  - One with status='collected' (also needs a LoyaltyPoints row)
```

---

## ⚙️ LEGION — Backend Routes

Legion imports models from Ammara's `models.py` but never edits it.
If Legion needs a new model method, he asks Ammara to add it.

---

### `app.py`

```python
# What Legion builds here:
# 1. Create Flask app instance
# 2. app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campuseats.db'
# 3. app.config['SECRET_KEY'] = 'dev-secret-change-in-production'
# 4. db.init_app(app)  ← db imported from models.py
# 5. Register blueprints: auth, student, staff, admin
# 6. with app.app_context(): db.create_all()  ← creates tables on first run
```

---

### Decorators Legion must write (put in a `utils.py`)

```python
def login_required(f):
    # Check session['user_id'] exists
    # If not → redirect to /login
    # If yes → call the route function normally

def role_required(*roles):
    # Check session['role'] is in the allowed roles list
    # If not → abort(403)
    # Example usage: @role_required('admin') or @role_required('staff', 'admin')
```

---

### `routes/auth.py`

| Route | Method | Action |
|-------|--------|--------|
| `/login` | GET | Render `auth/login.html` |
| `/login` | POST | Validate credentials → set session → redirect by role |
| `/register` | GET | Render `auth/register.html` |
| `/register` | POST | Create User → redirect to `/login` |
| `/logout` | GET | Clear session → redirect to `/login` |

**`login()` logic:**
```
1. Get email + password from form
2. Query: User.query.filter_by(email=email).first()
3. If no user or user.check_password(password) is False → flash error, re-render login
4. Set session['user_id'] = user.id
5. Set session['role'] = user.role
6. Redirect: student → /menu | staff → /staff | admin → /admin
```

**`register()` logic:**
```
1. Get name, email, student_number, password from form
2. Check email not already in DB
3. Create User(name=..., email=..., student_number=..., role='student')
4. Call user.set_password(password)  ← Ammara's method
5. db.session.add(user), db.session.commit()
6. flash('Account created. Please log in.')
7. Redirect to /login
```

---

### `routes/student.py`

| Route | Method | Action |
|-------|--------|--------|
| `/menu` | GET | Query available menu items → render student/menu.html |
| `/order` | POST | Receive cart JSON → create Order + OrderItems → return order id |
| `/order/<int:id>/track` | GET | Query Order → render student/track.html |
| `/order/<int:id>/status` | GET | Return `{"status": "..."}` JSON — Tino polls this |

**`menu()` logic:**
```
1. Query: MenuItem.query.filter_by(is_available=True).all()
2. Pass items as list of dicts using item.to_dict()  ← Ammara's method
3. Render menu.html with items
```

**`place_order()` logic:**
```
1. Parse JSON from request: {cart: [{menu_item_id, quantity}], pickup_slot}
2. For each cart item:
   a. Query MenuItem by id
   b. If not found or is_available=False → return error JSON
3. Calculate subtotal = sum(item.price * quantity for each cart item)
4. Create Order(user_id=session['user_id'], subtotal=..., service_fee=2.0,
                total=subtotal+2.0, pickup_slot=...)
   ← pickup_code auto-generated by Ammara's __init__
5. db.session.add(order), db.session.flush()  ← get order.id before commit
6. For each cart item:
   Create OrderItem(order_id=order.id, menu_item_id=...,
                    quantity=..., unit_price=menu_item.price)
   db.session.add(order_item)
7. db.session.commit()
8. Return JSON: {"order_id": order.id}
```

**`track_order()` logic:**
```
1. Query Order by id
2. Check order.user_id == session['user_id'] (security — students can't see others' orders)
3. Render track.html with order.to_dict()  ← Ammara's method
```

---

### `routes/staff.py`

| Route | Method | Action |
|-------|--------|--------|
| `/staff` | GET | Query active orders → render staff/dashboard.html |
| `/staff/order/<int:id>/status` | POST | Update order status |
| `/staff/menu/<int:id>/toggle` | POST | Flip MenuItem.is_available |
| `/staff/orders/live` | GET | Return all active orders as JSON (Tino polls this) |

**`update_status()` logic:**
```
1. Get new_status from form data
2. Validate new_status is one of: 'preparing', 'ready', 'collected'
3. Query Order by id, update order.status
4. If new_status == 'collected': call award_loyalty_point(order)
5. db.session.commit()
6. Redirect back to /staff
```

**`award_loyalty_point(order)` helper:**
```
1. Get the student's most recent LoyaltyPoints row to find their current balance
2. current_balance = last_record.points_balance if last_record else 0
3. Create LoyaltyPoints(user_id=order.user_id, order_id=order.id,
                         points_earned=1, points_balance=current_balance+1)
4. db.session.add(lp), db.session.commit()
```

**`toggle_availability()` logic:**
```
1. Query MenuItem by id
2. item.is_available = not item.is_available
3. db.session.commit()
4. Redirect back to /staff
```

---

### `routes/admin.py`

| Route | Method | Action |
|-------|--------|--------|
| `/admin` | GET | Aggregate stats + recent orders → render admin/dashboard.html |
| `/admin/stats` | GET | JSON for Tino's charts |
| `/admin/menu` | GET | All menu items → render admin/menu.html |
| `/admin/menu/add` | POST | Create new MenuItem |
| `/admin/menu/<int:id>/edit` | POST | Update existing MenuItem |
| `/admin/menu/<int:id>/delete` | POST | Delete MenuItem |
| `/admin/orders` | GET | All orders (filterable) → render admin/orders.html |
| `/admin/students` | GET | All students → render admin/students.html |

**`dashboard()` stats to calculate:**
```python
from datetime import date
today = date.today()

total_orders_today  = Order.query.filter(db.func.date(Order.created_at) == today).count()
revenue_today       = db.session.query(db.func.sum(Order.total))\
                        .filter(db.func.date(Order.created_at) == today).scalar() or 0
active_students     = User.query.filter_by(role='student', is_active=True).count()
recent_orders       = Order.query.order_by(Order.created_at.desc()).limit(5).all()
```

**`get_stats()` JSON response for charts:**
```python
# Hourly breakdown — count orders grouped by hour for today
# Top items — count OrderItems grouped by menu_item_id, get top 5
# Return: {"hourly": [{"hour": "08:00", "count": 3}, ...],
#          "top_items": [{"name": "Bunny Chow", "count": 42}, ...]}
```

**`add_menu_item()` logic:**
```
1. Get all fields from form: name, description, price, category, emoji, dietary
2. Create MenuItem(...), db.session.add(), db.session.commit()
3. flash('Item added.'), redirect to /admin/menu
```

**`delete_menu_item()` logic:**
```
1. Query MenuItem by id
2. Check no active Order (status != 'collected') contains this item
   If yes → flash error, redirect (can't delete item with live orders)
3. db.session.delete(item), db.session.commit()
4. Redirect to /admin/menu
```

---

## 🎨 TINO — Frontend

Tino can start building templates as soon as Ammara has finished `seed.py` and the DB is seeded,
and as soon as Legion has the routes returning data.

---

### Design rules
- **Student + Admin:** Light warm background `#F7F4EF`, surface `#FFFFFF`, border `#E2DDD6`
- **Staff dashboard:** Dark background `#111210`, surface `#1C1D1A`, border `#2E2F2B`
- **Accent orange:** `#E85D24` — buttons, highlights, active states
- **Accent navy:** `#2E4057` — admin sidebar, secondary elements
- **Fonts:** `DM Sans` body + `Syne` headings (Google Fonts CDN)
- **No box-shadow or glow** — use `border: 0.5px solid` for card outlines only
- **Hover states:** Change `border-color` only, never add shadow
- **Border radius:** `10px–12px` on cards, `20px` on pills/chips, `7px–8px` on inputs

---

### `templates/base.html`

```html
<!-- What Tino builds: -->
<!-- 1. <head>: Google Fonts, /static/css/style.css, viewport meta -->
<!-- 2. <nav> — role-aware links using session['role'] passed by Legion: -->
<!--    student → Menu, My Orders -->
<!--    staff   → Order Queue -->
<!--    admin   → Dashboard, Menu Manager, Orders, Students -->
<!-- 3. Flash message block (Legion flashes messages on actions) -->
<!-- 4. {% block content %}{% endblock %} -->
<!-- 5. <script> tags at bottom -->

<!-- Jinja variables Legion always passes to every template: -->
<!-- current_user_name (string), current_role (string) -->
```

---

### `templates/student/menu.html`

**Layout:** Left = scrollable menu grid. Right = sticky cart panel (300px wide).

**Menu grid (left):**
- Search bar at top
- Category filter tabs: All / Mains / Snacks / Drinks / Breakfast / 🌿 Veg
- 2-column card grid — each card has: emoji, dietary badge (if veg/halal), name, description, price, add button
- Sold-out cards show "Sold out" badge, grey out content, no add button

**Cart panel (right):**
- Pickup slot `<select>` — slots every 15 min from 11:30 to 13:30
- Empty state message when no items added
- Cart item rows: emoji, name, qty controls (−/+), line total
- Subtotal + R2 service fee + Total
- "Place order" button — disabled when cart empty

**Jinja variables Legion passes:**
```python
render_template('student/menu.html', items=[item.to_dict() for item in menu_items])
```

**`static/js/menu.js` — what Tino writes:**
```javascript
// Cart state object: { menu_item_id: {name, emoji, price, quantity} }
// addItem(id, name, emoji, price) — add to cart or increment qty
// removeItem(id) — decrement qty, remove if 0
// renderCart() — update cart panel DOM
// placeOrder() — on button click:
//   POST to /order with JSON: { cart: [...], pickup_slot: "12:15" }
//   On success: window.location = '/order/' + data.order_id + '/track'
```

---

### `templates/student/track.html`

**Layout:** Centered card, max-width 480px.

**What Tino builds:**
- Large pickup code display (e.g. `AB7K2`) in monospace font, big and bold
- 4-step progress bar: Placed → Preparing → Ready → Collected
  - Active step highlighted in accent orange
- Order summary: list of items with quantities
- Pickup slot reminder
- Auto-refresh status every 5 seconds

**Jinja variables Legion passes:**
```python
render_template('student/track.html', order=order.to_dict())
```

**JS Tino writes inline in this template:**
```javascript
const orderId = {{ order.id }};
let currentStatus = "{{ order.status }}";

setInterval(async () => {
  const res = await fetch(`/order/${orderId}/status`);
  const data = await res.json();
  if (data.status !== currentStatus) {
    currentStatus = data.status;
    updateProgressBar(currentStatus); // Tino writes this
  }
}, 5000);
```

---

### `templates/staff/dashboard.html`

**Layout:** Dark theme. Full viewport height. Three columns side by side.

**Top bar:** Logo + "Staff View" label + live clock (JS `setInterval`)

**Stats row under topbar:** New orders count / Preparing count / Completed today / Avg wait

**Three columns:**
- **New Orders** — red left border on cards, "Start cooking" button
- **Preparing** — amber left border, "Mark ready" button
- **Ready for Pickup** — green left border, "Collected" button

**Each order card shows:** Order ID (monospace), student name, pickup slot, item list with quantities

**Bottom of Ready column:** Sold-out toggle chips for each menu item

**Jinja variables Legion passes:**
```python
render_template('staff/dashboard.html',
  new_orders=[o.to_dict() for o in new_orders],
  preparing_orders=[o.to_dict() for o in preparing_orders],
  ready_orders=[o.to_dict() for o in ready_orders],
  menu_items=[item.to_dict() for item in all_items])
```

**`static/js/staff.js` — what Tino writes:**
```javascript
// moveOrder(orderId, newStatus):
//   POST to /staff/order/{orderId}/status with body: new_status=preparing
//   On success: move card DOM element to correct column

// Auto-refresh every 10 seconds:
//   GET /staff/orders/live → re-render all three columns from JSON

// toggleSoldOut(itemId):
//   POST to /staff/menu/{itemId}/toggle
//   Toggle chip styling on/off
```

---

### `templates/admin/dashboard.html`

**Layout:** Light theme. Sidebar (200px) + main content area.

**Sidebar** (same across all admin pages — put in a partial `_sidebar.html`):
- Logo + "Admin Panel" role label
- Nav links: Dashboard, All Orders, Menu Manager, Promotions, Students, Settings
- Active link highlighted

**Stats row:** Orders today / Revenue today (R) / Avg wait time / Active students

**Charts section:**
- Bar chart — orders per hour (use Chart.js from CDN)
- Horizontal bar — top 5 selling items

**Recent orders table** (last 5): Order ID, Student, Items, Total, Status pill, Time

**`static/js/admin.js` — what Tino writes:**
```javascript
// On page load, fetch /admin/stats then:
// renderHourlyChart(data.hourly) — Chart.js bar chart
// renderTopItems(data.top_items) — horizontal bars (can be plain CSS divs, no chart library needed)
```

---

### `templates/admin/menu.html`

**What Tino builds:**
- Category filter tabs (filter table rows by JS, no page reload)
- Table: Item (emoji + name), Category, Price, Dietary badge, Available toggle, Edit / Delete buttons
- "Add item" button → opens modal form
- Modal form fields: Name, Emoji, Price, Category (select), Description, Dietary (select)

**How actions connect to Legion:**
```html
<!-- Available toggle — plain form, no JS needed -->
<form method="POST" action="/admin/menu/{{ item.id }}/toggle">
  <button type="submit">Toggle</button>
</form>

<!-- Add item modal submits to -->
<form method="POST" action="/admin/menu/add"> ... </form>

<!-- Delete button -->
<form method="POST" action="/admin/menu/{{ item.id }}/delete">
  <button type="submit" onclick="return confirm('Delete this item?')">Delete</button>
</form>
```

---

## 🔗 End-to-end flow: Student places an order

```
1. Tino's menu.html loads
   └── Legion's GET /menu queries MenuItem (Ammara's model), passes to template

2. Student adds items → Tino's menu.js updates cart object in memory

3. Student clicks "Place Order"
   └── Tino's menu.js POSTs to /order with JSON cart

4. Legion's place_order() route:
   └── Validates each item is available (queries Ammara's MenuItem)
   └── Creates Order row (Ammara's model — pickup_code auto-generated)
   └── Creates OrderItem rows (copies unit_price from MenuItem.price)
   └── Commits all to DB
   └── Returns {"order_id": 42}

5. Tino's JS redirects browser to /order/42/track

6. Legion's track_order() queries Order, passes order.to_dict() to track.html

7. Tino's track.html renders pickup code + progress bar
   └── JS polls GET /order/42/status every 5 seconds

8. Staff sees new order card on Tino's staff dashboard
   └── Clicks "Start cooking" → Tino's staff.js POSTs to /staff/order/42/status
   └── Legion updates Order.status = 'preparing' (Ammara's model)

9. Tino's polling picks up status change → moves progress bar forward

10. Staff clicks "Mark ready" → status = 'ready'
    └── Student's progress bar shows "Ready — go collect!"

11. Staff clicks "Collected" → status = 'collected'
    └── Legion also calls award_loyalty_point() helper
    └── Ammara's LoyaltyPoints model gets a new row
```

---

## ✅ Task Checklists

### Ammara — Database
- [ ] `models.py` — `User` class with `set_password`, `check_password`, `loyalty_balance`
- [ ] `models.py` — `MenuItem` class with `to_dict`
- [ ] `models.py` — `Promotion` class
- [ ] `models.py` — `Order` class with `__init__` (auto pickup_code), `to_dict`
- [ ] `models.py` — `OrderItem` class with `to_dict`
- [ ] `models.py` — `LoyaltyPoints` class
- [ ] `models.py` — All relationships defined with `db.relationship`
- [ ] `seed.py` — 3 users (student/staff/admin), 12 menu items, 2 promos, 3 sample orders

### Legion — Backend
- [ ] `app.py` — Flask setup, DB config, blueprint registration
- [ ] `utils.py` — `login_required` and `role_required` decorators
- [ ] `routes/auth.py` — login, register, logout
- [ ] `routes/student.py` — menu GET, place_order POST, track_order GET, order_status JSON
- [ ] `routes/staff.py` — dashboard, update_status, toggle_availability, live orders JSON
- [ ] `routes/admin.py` — dashboard, stats JSON, menu CRUD, orders list, students list
- [ ] `requirements.txt`

### Tino — Frontend
- [ ] `templates/base.html` — layout, nav, flash messages
- [ ] `templates/auth/login.html`
- [ ] `templates/auth/register.html`
- [ ] `templates/student/menu.html` — grid + cart sidebar
- [ ] `templates/student/track.html` — pickup code + progress bar + polling JS
- [ ] `templates/staff/dashboard.html` — 3-column Kanban dark UI
- [ ] `templates/admin/dashboard.html` — stats + charts
- [ ] `templates/admin/menu.html` — table + add modal
- [ ] `templates/admin/orders.html` — orders table
- [ ] `templates/admin/students.html` — student accounts table
- [ ] `static/css/style.css` — all global styles
- [ ] `static/js/menu.js` — cart logic + order fetch
- [ ] `static/js/staff.js` — order movement + auto-refresh
- [ ] `static/js/admin.js` — chart rendering

---

## 📌 Rules for everyone

1. **Ammara never edits routes. Legion never edits models. Tino never hardcodes URLs.**
2. **Tino always uses `{{ url_for('blueprint.function_name') }}`** — never `/admin/menu` directly
3. **Legion always imports from `models.py`** — `from models import User, MenuItem, Order, OrderItem, LoyaltyPoints, db`
4. **unit_price must be snapshotted** — Legion copies `menu_item.price` into `OrderItem.unit_price` at order creation. Never reference `menu_item.price` for historical orders.
5. **Passwords are never stored plain** — Legion calls `user.set_password()` always
6. **Check `is_available` before accepting an order** — Legion validates every item in the cart
7. **Legion flashes messages, Tino displays them** — `flash('Order placed!')` in routes, `{{ get_flashed_messages() }}` in `base.html`

---

## 📦 Dependencies

**`requirements.txt` (Legion creates this)**
```
flask
flask-sqlalchemy
werkzeug
```

```bash
pip install -r requirements.txt
```

## 🚀 Running the project

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Seed the database (Ammara runs this first)
python seed.py

# 3. Start the server (Legion runs this)
python app.py

# 4. Open in browser
http://localhost:5000

# Test logins:
# Student → legion@campus.ac.za / password123
# Staff   → staff@campus.ac.za  / password123
# Admin   → admin@campus.ac.za  / password123
```