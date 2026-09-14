from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DB_PATH = Path(__file__).with_name("ecommerce.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL,
        category TEXT NOT NULL,
        emoji TEXT NOT NULL,
        stock INTEGER NOT NULL DEFAULT 10
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        address TEXT NOT NULL,
        total REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Placed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    );
    """)

    admin = conn.execute("SELECT id FROM users WHERE email = ?", ("admin@example.com",)).fetchone()
    if not admin:
        conn.execute(
            "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
            ("Admin User", "admin@example.com", generate_password_hash("admin123"), "admin")
        )

    user = conn.execute("SELECT id FROM users WHERE email = ?", ("user@example.com",)).fetchone()
    if not user:
        conn.execute(
            "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
            ("Demo User", "user@example.com", generate_password_hash("user123"), "user")
        )

    count = conn.execute("SELECT COUNT(*) AS total FROM products").fetchone()["total"]
    if count == 0:
        products = [
            ("Classic Sneakers", "Comfortable everyday sneakers for casual outings.", 1499, "Fashion", "👟", 25),
            ("Smart Watch", "Track time, steps and daily activity with a modern design.", 2499, "Electronics", "⌚", 18),
            ("Wireless Headphones", "Enjoy clear sound with comfortable wireless headphones.", 1999, "Electronics", "🎧", 30),
            ("Travel Backpack", "Durable backpack with multiple compartments for travel.", 1199, "Accessories", "🎒", 20),
            ("Cotton Hoodie", "Soft cotton hoodie suitable for cool evenings.", 999, "Fashion", "🧥", 22),
            ("Desk Lamp", "Minimal LED desk lamp for study and work spaces.", 799, "Home", "💡", 15),
            ("Coffee Mug", "Reusable ceramic mug with a simple premium finish.", 399, "Home", "☕", 40),
            ("Fitness Bottle", "Leak-resistant water bottle for daily workouts.", 599, "Fitness", "🥤", 35)
        ]
        conn.executemany(
            "INSERT INTO products(name,description,price,category,emoji,stock) VALUES(?,?,?,?,?,?)",
            products
        )
    conn.commit()
    conn.close()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access is required.", "danger")
            return redirect(url_for("home"))
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_globals():
    cart = session.get("cart", {})
    return {"cart_count": sum(cart.values()), "current_user": session.get("user_name")}

@app.route("/")
def home():
    conn = get_db()
    category = request.args.get("category", "")
    search = request.args.get("search", "").strip()
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY id DESC"
    products = conn.execute(query, params).fetchall()
    categories = conn.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()
    conn.close()
    return render_template("index.html", products=products, categories=categories, selected_category=category, search=search)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if not name or not email or len(password) < 6:
            flash("Enter valid details. Password must contain at least 6 characters.", "danger")
            return redirect(url_for("register"))
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users(name,email,password) VALUES(?,?,?)",
                (name, email, generate_password_hash(password))
            )
            conn.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("An account with this email already exists.", "danger")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]
            flash("Welcome back!", "success")
            return redirect(url_for("home"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

@app.route("/cart")
def cart():
    cart_data = session.get("cart", {})
    conn = get_db()
    items, total = [], 0
    for product_id, quantity in cart_data.items():
        product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if product:
            subtotal = product["price"] * quantity
            total += subtotal
            items.append({"product": product, "quantity": quantity, "subtotal": subtotal})
    conn.close()
    return render_template("cart.html", items=items, total=total)

@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("home"))
    cart_data = session.get("cart", {})
    key = str(product_id)
    cart_data[key] = min(cart_data.get(key, 0) + 1, product["stock"])
    session["cart"] = cart_data
    flash(f"{product['name']} added to cart.", "success")
    return redirect(request.referrer or url_for("home"))

@app.route("/cart/update", methods=["POST"])
def update_cart():
    cart_data = session.get("cart", {})
    for product_id in list(cart_data.keys()):
        value = request.form.get(f"quantity_{product_id}", "0")
        try:
            quantity = max(0, int(value))
        except ValueError:
            quantity = 0
        if quantity == 0:
            cart_data.pop(product_id, None)
        else:
            cart_data[product_id] = quantity
    session["cart"] = cart_data
    flash("Cart updated.", "success")
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_data = session.get("cart", {})
    if not cart_data:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("home"))

    conn = get_db()
    items, total = [], 0
    for product_id, quantity in cart_data.items():
        product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if product:
            quantity = min(quantity, product["stock"])
            subtotal = product["price"] * quantity
            total += subtotal
            items.append((product, quantity, subtotal))

    if request.method == "POST":
        customer_name = request.form["customer_name"].strip()
        address = request.form["address"].strip()
        if not customer_name or not address:
            flash("Please enter your name and delivery address.", "danger")
            conn.close()
            return redirect(url_for("checkout"))

        cur = conn.execute(
            "INSERT INTO orders(user_id,customer_name,address,total,status) VALUES(?,?,?,?,?)",
            (session["user_id"], customer_name, address, total, "Placed")
        )
        order_id = cur.lastrowid
        for product, quantity, subtotal in items:
            conn.execute(
                "INSERT INTO order_items(order_id,product_id,quantity,price) VALUES(?,?,?,?)",
                (order_id, product["id"], quantity, product["price"])
            )
            conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product["id"]))
        conn.commit()
        conn.close()
        session["cart"] = {}
        flash("Order placed successfully.", "success")
        return redirect(url_for("orders"))

    conn.close()
    return render_template("checkout.html", items=items, total=total)

@app.route("/orders")
@login_required
def orders():
    conn = get_db()
    orders_data = conn.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return render_template("orders.html", orders=orders_data)

@app.route("/admin")
@login_required
@admin_required
def admin():
    conn = get_db()
    products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    orders_data = conn.execute("""
        SELECT orders.*, users.email
        FROM orders JOIN users ON users.id = orders.user_id
        ORDER BY orders.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("admin.html", products=products, orders=orders_data)

@app.route("/admin/product/add", methods=["POST"])
@login_required
@admin_required
def add_product():
    data = request.form
    conn = get_db()
    conn.execute(
        "INSERT INTO products(name,description,price,category,emoji,stock) VALUES(?,?,?,?,?,?)",
        (data["name"], data["description"], float(data["price"]), data["category"], data.get("emoji", "🛍️"), int(data["stock"]))
    )
    conn.commit()
    conn.close()
    flash("Product added.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/order/<int:order_id>/status", methods=["POST"])
@login_required
@admin_required
def update_order_status(order_id):
    status = request.form["status"]
    allowed = {"Placed", "Packed", "Shipped", "Delivered", "Cancelled"}
    if status not in allowed:
        flash("Invalid status.", "danger")
        return redirect(url_for("admin"))
    conn = get_db()
    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()
    flash("Order status updated.", "success")
    return redirect(url_for("admin"))

@app.route("/api/products")
def api_products():
    conn = get_db()
    products = [dict(row) for row in conn.execute("SELECT * FROM products ORDER BY id").fetchall()]
    conn.close()
    return jsonify(products)

@app.route("/api/orders")
@login_required
def api_orders():
    conn = get_db()
    orders_data = [dict(row) for row in conn.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],)
    ).fetchall()]
    conn.close()
    return jsonify(orders_data)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
