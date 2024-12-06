from flask import Flask, request, flash, jsonify, render_template, redirect, url_for
from flask_mysqldb import MySQL
import re
import os
from flask import session
from flask_bcrypt import Bcrypt
from flask_session import Session

app = Flask(__name__)

# Database configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

bcrypt = Bcrypt(app)

mysql = MySQL(app)

# Helper function to validate email
def is_valid_email(email):
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email)

# Helper function to validate phone number
def is_valid_phone(phone):
    return phone.isdigit() and len(phone) == 10

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'An unexpected error occurred on the server'}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'The requested resource was not found'}), 404

# Homepage
@app.route('/')
def home():
    try:
        cur = mysql.connection.cursor()
        query = """
            SELECT b.book_id, b.title, b.author, b.price, b.inventory, b.cover_type, COUNT(oi.book_id) AS order_count
            FROM Book b
            JOIN Order_Item oi ON b.book_id = oi.book_id
            GROUP BY b.book_id
            ORDER BY order_count DESC
            LIMIT 3
        """
        cur.execute(query)
        books = cur.fetchall()
        cur.close()
        
        # Debugging: Print the fetched books
        print("Books fetched:", books)

        # Transform data for rendering
        books_data = [
            {
                "id": book[0],
                "title": book[1],
                "author": book[2],
                "price": book[3],
                "inventory": book[4],
                "cover_type": book[5],
                "order_count": book[6]
            }
            for book in books
        ]

        # Debugging: Print the data being sent to the template
        print("Books Data Sent to Template:", books_data)

        return render_template('index.html', books=books_data)
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": str(e)})

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    if query:
        try:
            cur = mysql.connection.cursor()
            search_query = """
                SELECT book_id, title, author, genre, price 
                FROM Book 
                WHERE title LIKE %s OR author LIKE %s
            """
            like_query = f"%{query}%"
            cur.execute(search_query, (like_query, like_query))
            books = cur.fetchall()  # Fetch matching books
            cur.close()

            # Pass books and query to the template
            return render_template('products.html', books=books, query=query)
        except Exception as e:
            print("Search Error:", e)
            return jsonify({"error": str(e)}), 500
    else:
        # If no query, return an empty result
        return render_template('products.html', books=[], query=query)

# Book Catalog
@app.route('/catalog')
def catalog():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT book_id, title, author, price FROM Book")
        books = cur.fetchall()
        cur.close()
        books_data = [
            {"book_id": book[0], "title": book[1], "author": book[2], "price": book[3]}
            for book in books
        ]
        return render_template('catalog.html', books=books_data)
    except Exception as e:
        return jsonify({"error": str(e)})
    
@app.route('/book/<int:book_id>')
def book_details(book_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Book WHERE book_id = %s", (book_id,))
        book = cur.fetchone()
        cur.close()
        if book:
            book_data = {
                "book_id": book[0],
                "title": book[1],
                "author": book[2],
                "genre": book[3],
                "price": book[4],
                "inventory": book[5],
                "cover_type": book[6],
            }
            return render_template('book.html', book=book_data)
        else:
            return "Book not found", 404
    except Exception as e:
        return jsonify({"error": str(e)})

# User Registration Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        customer_type = 'Individual'  # Assuming individual registration here
        address_details = {
            'street': request.form.get('street'),
            'city': request.form.get('city'),
            'state': request.form.get('state'),
            'zip': request.form.get('zip'),
            'country': request.form.get('country'),
            'address_type': 'Home',  # Defaulting to Home
        }

        try:
            # Insert customer details
            cur = mysql.connection.cursor()
            customer_query = """
                INSERT INTO Customer (customer_name, email, password, customer_type)
                VALUES (%s, %s, %s, %s)
            """
            cur.execute(customer_query, (name, email, password, customer_type))
            customer_id = cur.lastrowid  # Get the generated customer_id

            # Insert address details
            address_query = """
                INSERT INTO Address (customer_id, street, city, state, zip, country, address_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(address_query, (
                customer_id,
                address_details['street'],
                address_details['city'],
                address_details['state'],
                address_details['zip'],
                address_details['country'],
                address_details['address_type']
            ))

            mysql.connection.commit()
            cur.close()

            flash("Registration successful! Please log in.", "success")
            return redirect('/login')
        except Exception as e:
            print("Registration Error:", e)
            flash("An error occurred during registration. Please try again.", "danger")
            return redirect('/register')
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM Customer WHERE email = %s", (email,))
            user = cur.fetchone()
            cur.close()

            if user and bcrypt.check_password_hash(user[3], password):  # Assuming password is at index 3
                session['user_id'] = user[0]  # Assuming customer_id is at index 0
                session['user_name'] = user[1]  # Assuming customer_name is at index 1
                return redirect(url_for('home'))
            else:
                return "Invalid credentials", 401
        except Exception as e:
            return jsonify({"error": str(e)})
    return render_template('login.html')

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        user_id = session['user_id']
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT b.title, c.quantity, b.price, (c.quantity * b.price) AS subtotal
            FROM Cart c
            JOIN Book b ON c.book_id = b.book_id
            WHERE c.customer_id = %s
        """, (user_id,))
        cart_items = cur.fetchall()
        cur.close()

        total = sum(item[3] for item in cart_items)  # Calculate total price
        formatted_items = [
            {
                "title": item[0],
                "quantity": item[1],
                "price": item[2],
                "subtotal": item[3]
            }
            for item in cart_items
        ]

        return render_template('cart.html', cart_items=formatted_items, total=total)
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)})

@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        user_id = session['user_id']
        cur = mysql.connection.cursor()

        # Fetch cart items for the logged-in user
        cur.execute("""
            SELECT b.title, c.quantity, b.price, (c.quantity * b.price) AS subtotal
            FROM Cart c
            JOIN Book b ON c.book_id = b.book_id
            WHERE c.customer_id = %s
        """, (user_id,))
        cart_items = cur.fetchall()

        if not cart_items:
            cur.close()
            return render_template('checkout.html', error="Your cart is empty!")

        # Calculate total price
        total = sum(item[3] for item in cart_items)
        formatted_items = [
            {
                "title": item[0],
                "quantity": item[1],
                "price": item[2],
                "subtotal": item[3]
            }
            for item in cart_items
        ]

        # Fetch addresses for the logged-in user
        cur.execute("""
            SELECT address_id, street, city, state, zip
            FROM Address
            WHERE customer_id = %s
        """, (user_id,))
        addresses = cur.fetchall()

        formatted_addresses = [
            {
                "address_id": address[0],
                "street": address[1],
                "city": address[2],
                "state": address[3],
                "zip": address[4]
            }
            for address in addresses
        ]

        cur.close()

        return render_template('checkout.html', cart_items=formatted_items, total=total, addresses=formatted_addresses)
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))
@app.route('/complete_checkout', methods=['POST'])
def complete_checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        user_id = session['user_id']

        # Fetch cart items and calculate total
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT b.book_id, c.quantity, b.price, (c.quantity * b.price) AS subtotal
            FROM Cart c
            JOIN Book b ON c.book_id = b.book_id
            WHERE c.customer_id = %s
        """, (user_id,))
        cart_items = cur.fetchall()
        total = sum(item[3] for item in cart_items)
        
        # Insert the order
        cur.execute("""
            INSERT INTO `Order` (customer_id, order_date, order_status, total_amount)
            VALUES (%s, NOW(), 'Completed', %s)
        """, (user_id, total))
        order_id = cur.lastrowid

        # Insert order items
        for item in cart_items:
            cur.execute("""
                INSERT INTO Order_Item (order_id, book_id, quantity, unit_price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, item[0], item[1], item[2]))

        # Save payment info
        card_name = request.form['card_name']
        card_number = request.form['card_number']
        expiry_date = request.form['expiry_date']
        cvv = request.form['cvv']
        cur.execute("""
            INSERT INTO Payment (order_id, payment_method, payment_date, amount)
            VALUES (%s, 'Credit Card', NOW(), %s)
        """, (order_id, total))
        
        # Clear cart
        cur.execute("DELETE FROM Cart WHERE customer_id = %s", (user_id,))
        
        mysql.connection.commit()
        cur.close()

        # Redirect to order confirmation page
        return redirect(url_for('order_confirmation', order_id=order_id))

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

# Order Confirmation Page
@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT o.order_id, o.order_date, o.total_amount, oi.book_id, b.title, oi.quantity, oi.unit_price
            FROM `Order` o
            JOIN Order_Item oi ON o.order_id = oi.order_id
            JOIN Book b ON oi.book_id = b.book_id
            WHERE o.order_id = %s
        """, (order_id,))
        order_details = cur.fetchall()
        cur.close()

        if not order_details:
            return "Order not found", 404

        formatted_details = {
            "order_id": order_details[0][0],
            "order_date": order_details[0][1],
            "total_amount": order_details[0][2],
            "items": [
                {"book_id": item[3], "title": item[4], "quantity": item[5], "unit_price": item[6]}
                for item in order_details
            ]
        }

        return render_template('order_confirmation.html', order=formatted_details)

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

# Admin Dashboard (Optional)
@app.route('/admin')
def admin_dashboard():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Orders")  # Fetch all orders for admin view
        orders = cur.fetchall()
        cur.close()
        return render_template('admin_dashboard.html', orders=orders)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/init_db', methods=['GET'])
def init_db():
    try:
        cur = mysql.connection.cursor()

        # Address Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Address (
                address_id INT AUTO_INCREMENT PRIMARY KEY,
                street VARCHAR(100),
                city VARCHAR(50),
                state VARCHAR(50),
                zip VARCHAR(10),
                country VARCHAR(50),
                address_type ENUM('Home', 'Business')
            )
        """)

        # Customer Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Customer (
                customer_id INT AUTO_INCREMENT PRIMARY KEY,
                customer_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,  -- Hashed password
                customer_type ENUM('Individual', 'Business') NOT NULL,
                address_id INT,
                FOREIGN KEY (address_id) REFERENCES Address(address_id)
            )
        """)

        # Individual Customer Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Individual_Customer (
                individual_id INT AUTO_INCREMENT PRIMARY KEY,
                customer_id INT,
                age INT,
                marital_status ENUM('Single', 'Married'),
                gender ENUM('Male', 'Female'),
                income DECIMAL(10, 2),
                FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
            )
        """)

        # Business Customer Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Business_Customer (
                business_id INT AUTO_INCREMENT PRIMARY KEY,
                customer_id INT,
                business_category VARCHAR(50),
                gross_income DECIMAL(10, 2),
                FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
            )
        """)

        # Publisher Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Publisher (
                publisher_id INT AUTO_INCREMENT PRIMARY KEY,
                publisher_name VARCHAR(100),
                email VARCHAR(100),
                phone VARCHAR(15),
                address_id INT,
                FOREIGN KEY (address_id) REFERENCES Address(address_id)
            )
        """)

        # Book Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Book (
                book_id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                author VARCHAR(100),
                genre VARCHAR(50),
                price DECIMAL(10, 2) NOT NULL,
                inventory INT NOT NULL,
                publisher_id INT,
                cover_type ENUM('Hardcover', 'Softcover', 'First Edition'),
                FOREIGN KEY (publisher_id) REFERENCES Publisher(publisher_id)
            )
        """)

        # Order Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS `Order` (
                order_id INT AUTO_INCREMENT PRIMARY KEY,
                customer_id INT,
                order_date DATE NOT NULL,
                order_status ENUM('Pending', 'Completed', 'Cancelled'),
                total_amount DECIMAL(10, 2),
                FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
            )
        """)

        # Order Item Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Order_Item (
                order_item_id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT,
                book_id INT,
                quantity INT NOT NULL,
                unit_price DECIMAL(10, 2),
                FOREIGN KEY (order_id) REFERENCES `Order`(order_id),
                FOREIGN KEY (book_id) REFERENCES Book(book_id)
            )
        """)

        # Payment Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Payment (
                payment_id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT,
                payment_method ENUM('Credit Card', 'PayPal', 'Bank Transfer'),
                payment_date DATE NOT NULL,
                amount DECIMAL(10, 2),
                FOREIGN KEY (order_id) REFERENCES `Order`(order_id)
            )
        """)

        # Shipment Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Shipment (
                shipment_id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT,
                shipment_date DATE,
                delivery_status ENUM('Pending', 'Shipped', 'Delivered', 'Cancelled'),
                address_id INT,
                FOREIGN KEY (order_id) REFERENCES `Order`(order_id),
                FOREIGN KEY (address_id) REFERENCES Address(address_id)
            )
        """)

        # Cart Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Cart (
                cart_id INT AUTO_INCREMENT PRIMARY KEY,
                customer_id INT,
                book_id INT,
                quantity INT,
                FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
                FOREIGN KEY (book_id) REFERENCES Book(book_id)
            )
        """)

        # Review Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Review (
                review_id INT AUTO_INCREMENT PRIMARY KEY,
                book_id INT,
                customer_id INT,
                ranking INT CHECK(ranking BETWEEN 1 AND 5),
                review_text TEXT,
                review_date DATE,
                FOREIGN KEY (book_id) REFERENCES Book(book_id),
                FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
            )
        """)

        mysql.connection.commit()
        cur.close()
        return "Database initialized successfully with all 12 tables!"
    except Exception as e:
        return jsonify({"error": str(e)})

# Create Customer
@app.route('/customers', methods=['POST'])
def add_customer():
    data = request.json
    email = data['email']
    phone = data['phone']

    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email format'}), 400

    if not is_valid_phone(phone):
        return jsonify({'error': 'Phone number must be 10 digits'}), 400

    # Proceed with adding customer
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM Customers WHERE email = %s", (email,))
    if cursor.fetchone():
        return jsonify({'error': 'Email already exists'}), 400

    query = """
        INSERT INTO Customers (customer_name, email, phone, address)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (
        data['customer_name'], 
        email, 
        phone, 
        data['address']
    ))
    mysql.connection.commit()
    return jsonify({'message': 'Customer added successfully!'}), 201

# Retrieve All Customers
@app.route('/customers', methods=['GET'])
def get_customers():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM Customers")
    customers = cursor.fetchall()
    return jsonify(customers), 200

# Retrieve Single Customer by ID
@app.route('/customers/<int:id>', methods=['GET'])
def get_customer(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM Customers WHERE customer_id = %s", (id,))
    customer = cursor.fetchone()
    if customer:
        return jsonify(customer), 200
    else:
        return jsonify({'message': 'Customer not found'}), 404

# Update Customer
@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    data = request.json
    name = data.get('customer_name')
    email = data.get('email')
    phone = data.get('phone')
    address = data.get('address')

    cursor = mysql.connection.cursor()
    query = """
        UPDATE Customers 
        SET customer_name = %s, email = %s, phone = %s, address = %s
        WHERE customer_id = %s
    """
    cursor.execute(query, (name, email, phone, address, id))
    mysql.connection.commit()
    if cursor.rowcount > 0:
        return jsonify({'message': 'Customer updated successfully!'}), 200
    else:
        return jsonify({'message': 'Customer not found'}), 404

# Delete Customer
@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM Orders WHERE customer_id = %s", (id,))
    orders = cursor.fetchall()
    if orders:
        return jsonify({'error': 'Cannot delete customer with existing orders.'}), 400
    
    cursor.execute("DELETE FROM Customers WHERE customer_id = %s", (id,))
    mysql.connection.commit()
    return jsonify({'message': 'Customer deleted successfully!'}), 200

# Create Order
@app.route('/orders', methods=['POST'])
def add_order():
    data = request.json
    customer_id = data['customer_id']
    order_date = data.get('order_date')  # Default to today if not provided
    total_amount = data['total_amount']

    cursor = mysql.connection.cursor()
    query = """
        INSERT INTO Orders (customer_id, order_date, total_amount)
        VALUES (%s, %s, %s)
    """
    cursor.execute(query, (customer_id, order_date, total_amount))
    mysql.connection.commit()
    return jsonify({'message': 'Order created successfully!'}), 201

# Retrieve All Orders
@app.route('/orders', methods=['GET'])
def get_orders():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT o.order_id, o.order_date, o.total_amount, 
               c.customer_name, c.email 
        FROM Orders o
        JOIN Customers c ON o.customer_id = c.customer_id
    """)
    orders = cursor.fetchall()
    return jsonify(orders), 200

# Retrieve Single Order by ID
@app.route('/orders/<int:id>', methods=['GET'])
def get_order(id):
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT o.order_id, o.order_date, o.total_amount, 
               c.customer_name, c.email 
        FROM Orders o
        JOIN Customers c ON o.customer_id = c.customer_id
        WHERE o.order_id = %s
    """, (id,))
    order = cursor.fetchone()
    if order:
        return jsonify(order), 200
    else:
        return jsonify({'message': 'Order not found'}), 404

# Update Order
@app.route('/orders/<int:id>', methods=['PUT'])
def update_order(id):
    data = request.json
    total_amount = data.get('total_amount')
    order_date = data.get('order_date')

    cursor = mysql.connection.cursor()
    query = """
        UPDATE Orders
        SET total_amount = %s, order_date = %s
        WHERE order_id = %s
    """
    cursor.execute(query, (total_amount, order_date, id))
    mysql.connection.commit()
    if cursor.rowcount > 0:
        return jsonify({'message': 'Order updated successfully!'}), 200
    else:
        return jsonify({'message': 'Order not found'}), 404

# Delete Order
@app.route('/orders/<int:id>', methods=['DELETE'])
def delete_order(id):
    cursor = mysql.connection.cursor()
    # Delete related transactions first
    cursor.execute("DELETE FROM Transactions WHERE order_id = %s", (id,))
    # Then delete the order
    cursor.execute("DELETE FROM Orders WHERE order_id = %s", (id,))
    mysql.connection.commit()
    if cursor.rowcount > 0:
        return jsonify({'message': 'Order deleted successfully!'}), 200
    else:
        return jsonify({'message': 'Order not found'}), 404

# Create Transaction
@app.route('/transactions', methods=['POST'])
def add_transaction():
    data = request.json
    order_id = data['order_id']
    payment_method = data['payment_method']
    payment_total_amount = data['payment_total_amount']

    cursor = mysql.connection.cursor()
    query = """
        INSERT INTO Transactions (order_id, payment_method, payment_total_amount)
        VALUES (%s, %s, %s)
    """
    cursor.execute(query, (order_id, payment_method, payment_total_amount))
    mysql.connection.commit()
    return jsonify({'message': 'Transaction recorded successfully!'}), 201

# Retrieve All Transactions
@app.route('/transactions', methods=['GET'])
def get_transactions():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT t.transaction_id, t.payment_method, t.payment_total_amount, 
               t.transaction_date, o.order_id, c.customer_name
        FROM Transactions t
        JOIN Orders o ON t.order_id = o.order_id
        JOIN Customers c ON o.customer_id = c.customer_id
    """)
    transactions = cursor.fetchall()
    return jsonify(transactions), 200

# Retrieve Single Transaction by ID
@app.route('/transactions/<int:id>', methods=['GET'])
def get_transaction(id):
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT t.transaction_id, t.payment_method, t.payment_total_amount, 
               t.transaction_date, o.order_id, c.customer_name
        FROM Transactions t
        JOIN Orders o ON t.order_id = o.order_id
        JOIN Customers c ON o.customer_id = c.customer_id
        WHERE t.transaction_id = %s
    """, (id,))
    transaction = cursor.fetchone()
    if transaction:
        return jsonify(transaction), 200
    else:
        return jsonify({'message': 'Transaction not found'}), 404

# Delete Transaction
@app.route('/transactions/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM Transactions WHERE transaction_id = %s", (id,))
    mysql.connection.commit()
    if cursor.rowcount > 0:
        return jsonify({'message': 'Transaction deleted successfully!'}), 200
    else:
        return jsonify({'message': 'Transaction not found'}), 404

# Fetch all products
@app.route('/products', methods=['GET'])
def get_products():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Products")
        rows = cur.fetchall()
        cur.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)})

# Add a new product
@app.route('/products', methods=['POST'])
def add_product():
    data = request.get_json()
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO Products (product_name, price, inventory, category)
            VALUES (%s, %s, %s, %s)
        """, (data['product_name'], data['price'], data['inventory'], data['category']))
        mysql.connection.commit()
        cur.close()
        return jsonify({"message": "Product added successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)})

# Update a product
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE Products
            SET product_name = %s, price = %s, inventory = %s, category = %s
            WHERE product_id = %s
        """, (data['product_name'], data['price'], data['inventory'], data['category'], product_id))
        mysql.connection.commit()
        cur.close()
        return jsonify({"message": "Product updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)})

# Delete a product
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM Products WHERE product_id = %s", (product_id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({"message": "Product deleted successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
