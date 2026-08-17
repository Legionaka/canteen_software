# CampusEats

College canteen ordering system — Flask + SQLAlchemy + HTML/CSS/JS.

## Team

| Developer | Role | Owns |
|-----------|------|------|
| Ammara | Database | `models.py`, `seed.py` |
| Legion | Backend | `app.py`, `utils.py`, `routes/` |
| Tino | Frontend | `templates/`, `static/css/`, `static/js/` |

## Quick start

1. Create a `.env` file in the project root:

```bash
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db
```

For production with Supabase, use:

```bash
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres:password@db.project-ref.supabase.co:5432/postgres
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Seed the database:

```bash
python seed.py
```

4. Run the app:

```bash
python app.py
```

The app will be available at `http://127.0.0.1:5000`.

## Test logins

| Email | Password | Role |
|-------|----------|------|
| `legion@campus.ac.za` | `password123` | Student |
| `staff@campus.ac.za` | `password123` | Staff |
| `admin@campus.ac.za` | `password123` | Admin |

## Routes

### Auth
- `GET /login` — login page
- `POST /login` — authenticate
- `GET /register` — student registration
- `POST /register` — create student account
- `GET /logout` — clear session

### Student
- `GET /menu` — browse menu and place orders
- `POST /order` — create order from cart JSON
- `GET /order/<id>/track` — track an order
- `GET /order/<id>/status` — JSON order status

### Staff
- `GET /staff` — kitchen board
- `POST /staff/order/<id>/status` — advance order status
- `POST /staff/menu/<id>/toggle` — toggle item availability
- `GET /staff/orders/live` — JSON active orders for auto-refresh

### Admin
- `GET /admin` — dashboard with stats and charts
- `GET /admin/stats` — JSON hourly + top items
- `GET /admin/menu` — menu management
- `POST /admin/menu/add` — add menu item
- `POST /admin/menu/<id>/edit` — edit menu item
- `POST /admin/menu/<id>/delete` — delete menu item
- `GET /admin/orders` — all orders
- `GET /admin/students` — all students

## Frontend notes

- Design tokens: no box-shadow, border-color hover states only.
- Student/admin use light theme; staff dashboard uses dark theme.
- Fonts: Syne (headings) and DM Sans (body) from Google Fonts.
- `base.html` injects `current_user_name` and `current_role` for the nav bar.
