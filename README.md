# 🚀 Umang Sutarsandhiya – Portfolio Backend

## Tech Stack
- **Backend**: Python + Flask
- **Database**: SQLite (portfolio.db — auto-created on first run)
- **Frontend**: HTML/CSS/JS (served from `/public/index.html`)

## Quick Start

```bash
# 1. Install Flask (if not installed)
pip install flask

# 2. Start the server
python3 app.py
# OR
./start.sh

# 3. Open browser
open http://localhost:5000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server health check |
| POST | `/api/contact` | Submit contact form |
| GET | `/api/messages` | Get all contact messages |
| POST | `/api/food/order` | Place food order |
| GET | `/api/food/orders` | Get all food orders |
| POST | `/api/ride/book` | Book a ride |
| GET | `/api/ride/bookings` | Get all ride bookings |
| GET | `/api/salon/slots` | Get available slots |
| POST | `/api/salon/book` | Book salon appointment |
| GET | `/api/salon/bookings` | Get all salon bookings |
| GET | `/api/shop/products` | Get product catalog |
| POST | `/api/shop/order` | Place e-commerce order |
| GET | `/api/shop/orders` | Get all shop orders |
| GET | `/api/stats` | Portfolio-wide stats |
| GET | `/api/admin/dashboard` | Full admin overview |
| POST | `/api/visit` | Track page visit |

## Project Structure

```
portfolio-backend/
├── app.py            ← Flask API server
├── portfolio.db      ← SQLite database (auto-created)
├── start.sh          ← Quick start script
├── README.md
└── public/
    └── index.html    ← Frontend (served by Flask)
```

## Database Tables
- `contact_messages` — Contact form submissions
- `food_orders` — FoodieExpress orders
- `ride_bookings` — SwiftRide bookings
- `salon_bookings` — GlowSalon appointments
- `shop_orders` — ShopEase orders
- `page_visits` — Visitor tracking

## Deployment (Production)

```bash
# Using gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Using render.com / Railway / Fly.io
# Set start command to: python3 app.py
```
