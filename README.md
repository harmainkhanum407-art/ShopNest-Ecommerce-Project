# E-Commerce Web Application

A beginner-friendly full-stack e-commerce project created for the Thiranex task.

## Features

- Product catalog with search and category filtering
- Add-to-cart and cart quantity management
- Checkout and order creation
- User registration and login
- Role-based access: Admin and User
- Admin product creation
- Admin order status management
- Order tracking page
- SQLite database
- JSON APIs for products and orders
- Responsive interface

## Technologies

- Python
- Flask
- SQLite
- HTML5
- CSS3
- JavaScript
- Jinja2 templates

## Project Structure

```text
ecommerce_web_application/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── ecommerce.db              # created automatically on first run
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── cart.html
│   ├── checkout.html
│   ├── orders.html
│   └── admin.html
└── static/
    ├── style.css
    └── script.js
```

## How to Run

1. Install Python 3.10 or newer.
2. Open the project folder in VS Code.
3. Create a virtual environment:

```powershell
python -m venv venv
```

4. Activate it:

```powershell
venv\Scripts\activate
```

5. Install dependencies:

```powershell
pip install -r requirements.txt
```

6. Run the application:

```powershell
python app.py
```

7. Open this address in your browser:

```text
http://127.0.0.1:5000
```

## Demo Login Details

### Admin

- Email: `admin@example.com`
- Password: `admin123`

### User

- Email: `user@example.com`
- Password: `user123`

## Important Notes

- The database is created automatically when the application starts.
- This is an educational project. For real deployment, use environment variables for secrets, stronger validation, CSRF protection, secure cookies, and a production WSGI server.
- Change the Flask secret key before deploying.
