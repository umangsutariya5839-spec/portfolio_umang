"""
Portfolio Backend - Flask + SQLite
Umang Sutarsandhiya - Portfolio API Server

Endpoints:
  POST /api/contact          - Send contact message
  GET  /api/messages         - Get all messages (admin)
  POST /api/food/order       - Place food order
  GET  /api/food/orders      - Get food orders
  POST /api/ride/book        - Book a ride
  GET  /api/ride/bookings    - Get ride bookings
  POST /api/salon/book       - Book salon appointment
  GET  /api/salon/bookings   - Get salon bookings
  GET  /api/salon/slots      - Get available slots
  POST /api/shop/order       - Place ecommerce order
  GET  /api/shop/orders      - Get shop orders
  GET  /api/shop/products    - Get products
  GET  /api/stats            - Portfolio stats
  GET  /health               - Health check
"""

from flask import Flask, request, jsonify, send_from_directory
import sqlite3, json, hashlib, time, uuid, re, os
from functools import wraps
from datetime import datetime

app = Flask(__name__, static_folder='public')

DB_PATH = os.path.join(os.path.dirname(__file__), 'portfolio.db')

# ─── CORS MIDDLEWARE ────────────────────────────────────────────────────────
@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response

@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return jsonify({}), 200

# ─── DATABASE INIT ──────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS contact_messages (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        subject TEXT,
        message TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        read INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS food_orders (
        id TEXT PRIMARY KEY,
        customer_name TEXT,
        restaurant TEXT NOT NULL,
        items TEXT NOT NULL,
        total REAL NOT NULL,
        status TEXT DEFAULT 'confirmed',
        address TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS ride_bookings (
        id TEXT PRIMARY KEY,
        customer_name TEXT,
        phone TEXT,
        pickup TEXT NOT NULL,
        dropoff TEXT NOT NULL,
        ride_type TEXT NOT NULL,
        fare REAL NOT NULL,
        driver_name TEXT,
        driver_rating TEXT,
        status TEXT DEFAULT 'searching',
        created_at TEXT DEFAULT (datetime('now'))
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS salon_bookings (
        id TEXT PRIMARY KEY,
        customer_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        service TEXT NOT NULL,
        service_price REAL NOT NULL,
        booking_date TEXT NOT NULL,
        time_slot TEXT NOT NULL,
        status TEXT DEFAULT 'confirmed',
        created_at TEXT DEFAULT (datetime('now'))
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS shop_orders (
        id TEXT PRIMARY KEY,
        customer_name TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        items TEXT NOT NULL,
        subtotal REAL NOT NULL,
        delivery REAL DEFAULT 0,
        total REAL NOT NULL,
        payment_method TEXT DEFAULT 'COD',
        status TEXT DEFAULT 'confirmed',
        created_at TEXT DEFAULT (datetime('now'))
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS page_visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page TEXT,
        ip TEXT,
        visited_at TEXT DEFAULT (datetime('now'))
    )''')

    conn.commit()
    conn.close()
    print("✅ Database initialized:", DB_PATH)

# ─── HELPERS ────────────────────────────────────────────────────────────────
def gen_id(prefix=''):
    return prefix + str(uuid.uuid4())[:8].upper()

def row_to_dict(row):
    return dict(row) if row else None

def rows_to_list(rows):
    return [dict(r) for r in rows]

def validate_email(email):
    return re.match(r'^[^@]+@[^@]+\.[^@]+$', email)

# ─── HEALTH CHECK ────────────────────────────────────────────────────────────
@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'Portfolio API is running!', 'timestamp': datetime.now().isoformat(), 'version': '1.0.0'})

# ─── STATS ──────────────────────────────────────────────────────────────────
@app.route('/api/stats')
def get_stats():
    conn = get_db()
    c = conn.cursor()
    stats = {
        'contact_messages': c.execute('SELECT COUNT(*) FROM contact_messages').fetchone()[0],
        'food_orders': c.execute('SELECT COUNT(*) FROM food_orders').fetchone()[0],
        'ride_bookings': c.execute('SELECT COUNT(*) FROM ride_bookings').fetchone()[0],
        'salon_bookings': c.execute('SELECT COUNT(*) FROM salon_bookings').fetchone()[0],
        'shop_orders': c.execute('SELECT COUNT(*) FROM shop_orders').fetchone()[0],
        'page_visits': c.execute('SELECT COUNT(*) FROM page_visits').fetchone()[0],
    }
    conn.close()
    return jsonify({'success': True, 'stats': stats})

# ─── CONTACT ────────────────────────────────────────────────────────────────
@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json()
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    subject = (data.get('subject') or 'Portfolio Inquiry').strip()
    message = (data.get('message') or '').strip()

    if not name: return jsonify({'success': False, 'error': 'Name is required'}), 400
    if not email or not validate_email(email): return jsonify({'success': False, 'error': 'Valid email is required'}), 400
    if not message: return jsonify({'success': False, 'error': 'Message is required'}), 400

    msg_id = gen_id('MSG-')
    conn = get_db()
    conn.execute('INSERT INTO contact_messages (id,name,email,subject,message) VALUES (?,?,?,?,?)',
                 (msg_id, name, email, subject, message))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': f"Thanks {name}! Your message has been received. Umang will get back to you soon.", 'id': msg_id})

@app.route('/api/messages')
def get_messages():
    conn = get_db()
    rows = conn.execute('SELECT * FROM contact_messages ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify({'success': True, 'messages': rows_to_list(rows), 'total': len(rows)})

# ─── FOOD ORDERS ─────────────────────────────────────────────────────────────
@app.route('/api/food/order', methods=['POST'])
def food_order():
    data = request.get_json()
    restaurant = (data.get('restaurant') or '').strip()
    items = data.get('items', [])
    total = data.get('total', 0)
    customer_name = (data.get('customer_name') or 'Guest').strip()
    address = (data.get('address') or 'Default Address').strip()

    if not restaurant: return jsonify({'success': False, 'error': 'Restaurant name required'}), 400
    if not items: return jsonify({'success': False, 'error': 'No items in order'}), 400
    if total <= 0: return jsonify({'success': False, 'error': 'Invalid total amount'}), 400

    order_id = gen_id('FOOD-')
    conn = get_db()
    conn.execute('INSERT INTO food_orders (id,customer_name,restaurant,items,total,address) VALUES (?,?,?,?,?,?)',
                 (order_id, customer_name, restaurant, json.dumps(items), total, address))
    conn.commit()
    conn.close()

    eta = "30-40 minutes"
    return jsonify({'success': True, 'order_id': order_id, 'message': f'Order placed at {restaurant}!', 'eta': eta, 'total': total, 'status': 'confirmed'})

@app.route('/api/food/orders')
def get_food_orders():
    conn = get_db()
    rows = conn.execute('SELECT * FROM food_orders ORDER BY created_at DESC LIMIT 50').fetchall()
    conn.close()
    orders = []
    for r in rows:
        d = dict(r)
        try: d['items'] = json.loads(d['items'])
        except: pass
        orders.append(d)
    return jsonify({'success': True, 'orders': orders, 'total': len(orders)})

# ─── RIDE BOOKINGS ───────────────────────────────────────────────────────────
DRIVERS = [
    {'name': 'Ramesh K.', 'rating': '4.8', 'trips': 1240, 'vehicle': 'Honda Activa', 'plate': 'GJ 01 AB 2345'},
    {'name': 'Suresh P.', 'rating': '4.7', 'trips': 890, 'vehicle': 'TVS Jupiter', 'plate': 'GJ 05 CD 6789'},
    {'name': 'Mahesh V.', 'rating': '4.9', 'trips': 2100, 'vehicle': 'Honda Dio', 'plate': 'GJ 01 EF 1122'},
]

@app.route('/api/ride/book', methods=['POST'])
def book_ride():
    data = request.get_json()
    pickup = (data.get('pickup') or '').strip()
    dropoff = (data.get('dropoff') or '').strip()
    ride_type = (data.get('ride_type') or 'bike').strip()
    fare = data.get('fare', 0)
    customer_name = (data.get('customer_name') or 'Rider').strip()
    phone = (data.get('phone') or '').strip()

    if not pickup: return jsonify({'success': False, 'error': 'Pickup location required'}), 400
    if not dropoff: return jsonify({'success': False, 'error': 'Drop location required'}), 400

    import random
    driver = random.choice(DRIVERS)
    booking_id = gen_id('RIDE-')
    eta_minutes = random.randint(2, 6)

    conn = get_db()
    conn.execute('INSERT INTO ride_bookings (id,customer_name,phone,pickup,dropoff,ride_type,fare,driver_name,driver_rating,status) VALUES (?,?,?,?,?,?,?,?,?,?)',
                 (booking_id, customer_name, phone, pickup, dropoff, ride_type, fare, driver['name'], driver['rating'], 'driver_assigned'))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'booking_id': booking_id, 'message': 'Driver assigned!', 'driver': driver, 'eta_minutes': eta_minutes, 'fare': fare, 'status': 'driver_assigned'})

@app.route('/api/ride/bookings')
def get_ride_bookings():
    conn = get_db()
    rows = conn.execute('SELECT * FROM ride_bookings ORDER BY created_at DESC LIMIT 50').fetchall()
    conn.close()
    return jsonify({'success': True, 'bookings': rows_to_list(rows), 'total': len(rows)})

# ─── SALON BOOKINGS ──────────────────────────────────────────────────────────
BUSY_SLOTS_BASE = ['10:00 AM', '2:45 PM', '4:15 PM']

@app.route('/api/salon/slots')
def get_salon_slots():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    conn = get_db()
    booked = conn.execute('SELECT time_slot FROM salon_bookings WHERE booking_date=? AND status!=?', (date, 'cancelled')).fetchall()
    conn.close()
    booked_slots = [r['time_slot'] for r in booked] + BUSY_SLOTS_BASE
    all_slots = ['10:00 AM','10:45 AM','11:30 AM','12:15 PM','2:00 PM','2:45 PM','3:30 PM','4:15 PM','5:00 PM']
    return jsonify({'success': True, 'date': date, 'slots': [{'time': s, 'available': s not in booked_slots} for s in all_slots]})

@app.route('/api/salon/book', methods=['POST'])
def book_salon():
    data = request.get_json()
    customer_name = (data.get('customer_name') or '').strip()
    phone = (data.get('phone') or '').strip()
    service = (data.get('service') or '').strip()
    service_price = data.get('service_price', 0)
    booking_date = (data.get('booking_date') or '').strip()
    time_slot = (data.get('time_slot') or '').strip()

    if not customer_name: return jsonify({'success': False, 'error': 'Name required'}), 400
    if not phone: return jsonify({'success': False, 'error': 'Phone required'}), 400
    if not service: return jsonify({'success': False, 'error': 'Service required'}), 400
    if not booking_date: return jsonify({'success': False, 'error': 'Date required'}), 400
    if not time_slot: return jsonify({'success': False, 'error': 'Time slot required'}), 400

    conn = get_db()
    existing = conn.execute('SELECT id FROM salon_bookings WHERE booking_date=? AND time_slot=? AND status!=?', (booking_date, time_slot, 'cancelled')).fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'error': 'This slot is already booked. Please choose another.'}), 409

    booking_id = gen_id('SALON-')
    conn.execute('INSERT INTO salon_bookings (id,customer_name,phone,service,service_price,booking_date,time_slot) VALUES (?,?,?,?,?,?,?)',
                 (booking_id, customer_name, phone, service, service_price, booking_date, time_slot))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'booking_id': booking_id, 'message': f'Appointment confirmed for {customer_name}!', 'details': {'service': service, 'date': booking_date, 'time': time_slot, 'price': service_price}})

@app.route('/api/salon/bookings')
def get_salon_bookings():
    conn = get_db()
    rows = conn.execute('SELECT * FROM salon_bookings ORDER BY created_at DESC LIMIT 50').fetchall()
    conn.close()
    return jsonify({'success': True, 'bookings': rows_to_list(rows), 'total': len(rows)})

# ─── SHOP / ECOMMERCE ────────────────────────────────────────────────────────
PRODUCTS_DB = [
    {'id':1,'name':'Wireless Earbuds','emoji':'🎧','category':'electronics','price':1299,'original_price':2499,'rating':4.7,'badge':'52% OFF','stock':50},
    {'id':2,'name':'Smart Watch','emoji':'⌚','category':'electronics','price':2999,'original_price':5999,'rating':4.5,'badge':'50% OFF','stock':30},
    {'id':3,'name':'Men\'s Jacket','emoji':'🧥','category':'fashion','price':899,'original_price':1799,'rating':4.3,'badge':'50% OFF','stock':40},
    {'id':4,'name':'Sneakers','emoji':'👟','category':'fashion','price':1499,'original_price':2999,'rating':4.6,'badge':'NEW','stock':25},
    {'id':5,'name':'Coffee Maker','emoji':'☕','category':'home','price':1799,'original_price':3499,'rating':4.8,'badge':'Top Pick','stock':15},
    {'id':6,'name':'LED Desk Lamp','emoji':'💡','category':'home','price':599,'original_price':999,'rating':4.4,'badge':'HOT','stock':60},
    {'id':7,'name':'Face Serum','emoji':'🧴','category':'beauty','price':499,'original_price':899,'rating':4.7,'badge':'NEW','stock':80},
    {'id':8,'name':'Yoga Mat','emoji':'🧘','category':'sports','price':799,'original_price':1299,'rating':4.5,'badge':'Popular','stock':35},
    {'id':9,'name':'Bluetooth Speaker','emoji':'🔊','category':'electronics','price':1999,'original_price':3999,'rating':4.6,'badge':'47% OFF','stock':20},
    {'id':10,'name':'Sunglasses','emoji':'🕶','category':'fashion','price':699,'original_price':1299,'rating':4.2,'badge':'NEW','stock':45},
    {'id':11,'name':'Air Purifier','emoji':'🌬','category':'home','price':3499,'original_price':5999,'rating':4.8,'badge':'Best Seller','stock':12},
    {'id':12,'name':'Lip Gloss Set','emoji':'💄','category':'beauty','price':349,'original_price':599,'rating':4.5,'badge':'Sale','stock':70},
]

@app.route('/api/shop/products')
def get_products():
    category = request.args.get('category', 'all')
    products = PRODUCTS_DB if category == 'all' else [p for p in PRODUCTS_DB if p['category'] == category]
    return jsonify({'success': True, 'products': products, 'total': len(products)})

@app.route('/api/shop/order', methods=['POST'])
def shop_order():
    data = request.get_json()
    items = data.get('items', [])
    subtotal = data.get('subtotal', 0)
    customer_name = (data.get('customer_name') or 'Customer').strip()
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip()
    address = (data.get('address') or '').strip()
    payment_method = (data.get('payment_method') or 'COD').strip()

    if not items: return jsonify({'success': False, 'error': 'No items in order'}), 400
    if subtotal <= 0: return jsonify({'success': False, 'error': 'Invalid order total'}), 400

    delivery = 0 if subtotal >= 499 else 49
    total = subtotal + delivery
    order_id = gen_id('ORD-')

    conn = get_db()
    conn.execute('INSERT INTO shop_orders (id,customer_name,email,phone,address,items,subtotal,delivery,total,payment_method) VALUES (?,?,?,?,?,?,?,?,?,?)',
                 (order_id, customer_name, email, phone, address, json.dumps(items), subtotal, delivery, total, payment_method))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'order_id': order_id, 'message': f'Order confirmed! Delivering to {address or "your address"}', 'total': total, 'delivery': delivery, 'delivery_days': '3-5 business days', 'status': 'confirmed'})

@app.route('/api/shop/orders')
def get_shop_orders():
    conn = get_db()
    rows = conn.execute('SELECT * FROM shop_orders ORDER BY created_at DESC LIMIT 50').fetchall()
    conn.close()
    orders = []
    for r in rows:
        d = dict(r)
        try: d['items'] = json.loads(d['items'])
        except: pass
        orders.append(d)
    return jsonify({'success': True, 'orders': orders, 'total': len(orders)})

# ─── PAGE VISIT TRACKER ──────────────────────────────────────────────────────
@app.route('/api/visit', methods=['POST'])
def track_visit():
    data = request.get_json() or {}
    page = data.get('page', 'home')
    ip = request.remote_addr
    conn = get_db()
    conn.execute('INSERT INTO page_visits (page,ip) VALUES (?,?)', (page, ip))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ─── ADMIN DASHBOARD DATA ────────────────────────────────────────────────────
@app.route('/api/admin/dashboard')
def admin_dashboard():
    conn = get_db()
    c = conn.cursor()
    stats = {
        'total_messages': c.execute('SELECT COUNT(*) FROM contact_messages').fetchone()[0],
        'unread_messages': c.execute('SELECT COUNT(*) FROM contact_messages WHERE read=0').fetchone()[0],
        'total_food_orders': c.execute('SELECT COUNT(*) FROM food_orders').fetchone()[0],
        'food_revenue': c.execute('SELECT COALESCE(SUM(total),0) FROM food_orders').fetchone()[0],
        'total_rides': c.execute('SELECT COUNT(*) FROM ride_bookings').fetchone()[0],
        'ride_revenue': c.execute('SELECT COALESCE(SUM(fare),0) FROM ride_bookings').fetchone()[0],
        'total_salon_bookings': c.execute('SELECT COUNT(*) FROM salon_bookings').fetchone()[0],
        'salon_revenue': c.execute('SELECT COALESCE(SUM(service_price),0) FROM salon_bookings').fetchone()[0],
        'total_shop_orders': c.execute('SELECT COUNT(*) FROM shop_orders').fetchone()[0],
        'shop_revenue': c.execute('SELECT COALESCE(SUM(total),0) FROM shop_orders').fetchone()[0],
        'page_visits': c.execute('SELECT COUNT(*) FROM page_visits').fetchone()[0],
    }
    recent_messages = rows_to_list(c.execute('SELECT * FROM contact_messages ORDER BY created_at DESC LIMIT 5').fetchall())
    recent_orders = rows_to_list(c.execute('SELECT * FROM shop_orders ORDER BY created_at DESC LIMIT 5').fetchall())
    conn.close()
    return jsonify({'success': True, 'stats': stats, 'recent_messages': recent_messages, 'recent_orders': recent_orders})

# ─── STATIC FRONTEND ────────────────────────────────────────────────────────
@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory(app.static_folder, path)
    except:
        return send_from_directory(app.static_folder, 'index.html')

# ─── ERROR HANDLERS ──────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# ─── RUN ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    print("🚀 Portfolio Backend running on http://localhost:5000")
    print("📡 API Endpoints:")
    print("   POST /api/contact        - Contact form")
    print("   POST /api/food/order     - Food order")
    print("   POST /api/ride/book      - Ride booking")
    print("   POST /api/salon/book     - Salon booking")
    print("   GET  /api/salon/slots    - Available slots")
    print("   POST /api/shop/order     - E-commerce order")
    print("   GET  /api/shop/products  - Products list")
    print("   GET  /api/stats          - Portfolio stats")
    print("   GET  /api/admin/dashboard - Admin overview")
    app.run(debug=True, port=5000, host='0.0.0.0')
