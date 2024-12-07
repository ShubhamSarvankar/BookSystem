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
    
@app.route('/book/<int:book_id>', methods=['GET', 'POST'])
def book_details(book_id):
    try:
        cur = mysql.connection.cursor()

        # Fetch book details
        cur.execute("SELECT * FROM Book WHERE book_id = %s", (book_id,))
        book = cur.fetchone()

        # Fetch reviews for the book
        cur.execute("""
            SELECT r.review_text, r.ranking, c.customer_name 
            FROM Review r 
            JOIN Customer c ON r.customer_id = c.customer_id 
            WHERE r.book_id = %s
        """, (book_id,))
        reviews = cur.fetchall()

        if request.method == 'POST':
            if 'user_id' not in session:
                flash("Please log in to add items to your cart.", "warning")
                return redirect(url_for('login'))

            quantity = int(request.form.get('quantity', 1))
            user_id = session['user_id']

            # Add to cart
            cur.execute("""
                INSERT INTO Cart (customer_id, book_id, quantity)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
            """, (user_id, book_id, quantity))
            mysql.connection.commit()
            flash("Book successfully added to cart!", "success")  # Add flash message

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
            reviews_data = [
                {"review_text": r[0], "ranking": r[1], "customer_name": r[2]}
                for r in reviews
            ]
            return render_template('book.html', book=book_data, reviews=reviews_data)
        else:
            return "Book not found", 404
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)})

# User Registration Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # Hash the password
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
            cur.execute(customer_query, (name, email, hashed_password, customer_type))
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
            return redirect('/register')  # Stay on the register page with a success message
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
                flash("Logged in successfully!", "success")
                return redirect(url_for('home'))
            else:
                flash("Invalid email or password.", "danger")
                return redirect('/login')
        except Exception as e:
            print("Login Error:", e)
            flash("An error occurred. Please try again.", "danger")
            return redirect('/login')
    return render_template('login.html')

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        user_id = session['user_id']
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT b.book_id, b.title, c.quantity, b.price, (c.quantity * b.price) AS subtotal
            FROM Cart c
            JOIN Book b ON c.book_id = b.book_id
            WHERE c.customer_id = %s
        """, (user_id,))
        cart_items = cur.fetchall()
        cur.close()

        total = sum(item[4] for item in cart_items)  # Updated to match new index
        formatted_items = [
            {
                "book_id": item[0],  # Include book_id
                "title": item[1],
                "quantity": item[2],
                "price": item[3],
                "subtotal": item[4]
            }
            for item in cart_items
        ]

        return render_template('cart.html', cart_items=formatted_items, total=total)
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)})

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        user_id = session['user_id']
        book_id = request.form.get('book_id')

        # Ensure book_id is valid
        if not book_id:
            flash("Invalid book selected. Please try again.", "danger")
            return redirect(url_for('cart'))

        cur = mysql.connection.cursor()
        cur.execute("""
            DELETE FROM Cart
            WHERE customer_id = %s AND book_id = %s
        """, (user_id, book_id))
        mysql.connection.commit()
        cur.close()

        flash("Item removed from your cart.", "success")
    except Exception as e:
        flash("Error while removing item. Please try again.", "danger")
        print("Error:", e)
    return redirect(url_for('cart'))

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
        cart_items = [
            {
                "title": item[0],
                "quantity": item[1],
                "price": item[2],
                "subtotal": item[3]
            }
            for item in cur.fetchall()
        ]

        if not cart_items:
            cur.close()
            return render_template('checkout.html', error="Your cart is empty!")

        # Calculate total price
        total = sum(item['subtotal'] for item in cart_items)

        # Fetch addresses for the logged-in user
        cur.execute("""
            SELECT address_id, street, city, state, zip
            FROM Address
            WHERE customer_id = %s
        """, (user_id,))
        addresses = [
            {
                "address_id": address[0],
                "street": address[1],
                "city": address[2],
                "state": address[3],
                "zip": address[4]
            }
            for address in cur.fetchall()
        ]

        cur.close()

        return render_template('checkout.html', cart_items=cart_items, total=total, addresses=addresses)
    except Exception as e:
        print("Error in checkout:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/complete_checkout', methods=['POST'])
def complete_checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        user_id = session['user_id']
        address_id = request.form.get('address_id')
        card_details = request.form.get('card_details')

        # Retrieve cart items
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT c.book_id, c.quantity, b.price
            FROM Cart c
            JOIN Book b ON c.book_id = b.book_id
            WHERE c.customer_id = %s
        """, (user_id,))
        # Ensure fetchall() is called as a method
        cart_items = cur.fetchall()

        if not cart_items:
            flash("Your cart is empty. Please add items to proceed.", "warning")
            return redirect(url_for('checkout'))

        # Calculate total amount
        total_amount = sum(item[1] * item[2] for item in cart_items)

        # Insert order into Orders table
        cur.execute("""
            INSERT INTO Orderss (customer_id, order_date, order_status, total_amount)
            VALUES (%s, NOW(), 'Completed', %s)
        """, (user_id, total_amount))
        order_id = cur.lastrowid

        # Insert items into Order_Item table
        for book_id, quantity, price in cart_items:
            cur.execute("""
                INSERT INTO Order_Item (order_id, book_id, quantity, unit_price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, book_id, quantity, price))

        # Insert payment details
        cur.execute("""
            INSERT INTO Payment (order_id, payment_method, payment_date, amount)
            VALUES (%s, 'Credit Card', NOW(), %s)
        """, (order_id, total_amount))

        # Insert shipment details
        cur.execute("""
            INSERT INTO Shipment (order_id, shipment_date, delivery_status, address_id)
            VALUES (%s, NOW(), 'Pending', %s)
        """, (order_id, address_id))

        # Clear the cart
        cur.execute("DELETE FROM Cart WHERE customer_id = %s", (user_id,))
        mysql.connection.commit()
        cur.close()

        flash("Your purchase was successful!", "success")
        return redirect(url_for('order_confirmation', order_id=order_id))
    except Exception as e:
        flash("An error occurred during checkout. Please try again.", "danger")
        print("Error in complete_checkout:", e)
        return redirect(url_for('checkout'))

@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        print(f"Processing order confirmation for order_id: {order_id}")

        # Simple order confirmation message
        confirmation_data = {
            "order_id": order_id,
            "message": "Your order has been successfully confirmed!"
        }

        print(f"Confirmation data: {confirmation_data}")

        # Pass the confirmation message to the template
        return render_template('order_confirmation.html', order=confirmation_data)

    except Exception as e:
        # Log the error for debugging
        print(f"Error in order_confirmation: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

@app.route('/order_history')
def order_history():
    if 'user_id' not in session:
        flash("Please log in to view your order history.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    try:
        cur = mysql.connection.cursor()

        # Fetch order history for the logged-in user
        query = """
            SELECT o.order_id, o.order_date, o.order_status, o.total_amount, 
                   GROUP_CONCAT(CONCAT(oi.quantity, ' x ', b.title) SEPARATOR '<br>') AS items
            FROM Orderss o
            JOIN Order_Item oi ON o.order_id = oi.order_id
            JOIN Book b ON oi.book_id = b.book_id
            WHERE o.customer_id = %s
            GROUP BY o.order_id
            ORDER BY o.order_date DESC
        """
        cur.execute(query, (user_id,))
        orders = cur.fetchall()
        cur.close()

        # Transform orders for rendering
        order_data = [
            {
                "order_id": order[0],
                "order_date": order[1].strftime('%Y-%m-%d'),
                "order_status": order[2],
                "total_amount": order[3],
                "items": order[4]
            }
            for order in orders
        ]

        return render_template('order_history.html', orders=order_data)
    except Exception as e:
        print("Error fetching order history:", e)
        flash("An error occurred while fetching your order history.", "danger")
        return redirect(url_for('home'))


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin':
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid credentials, try again.", "danger")
    return render_template('admin_login.html')

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))

    try:
        cur = mysql.connection.cursor()

        # Aggregate Earnings for a Date Range
        total_profit = 0
        if request.method == 'POST':
            from_date = request.form.get('from_date')
            to_date = request.form.get('to_date')
            if from_date and to_date:
                cur.execute("""
                    SELECT SUM(o.total_amount)
                    FROM Orderss o
                    WHERE o.order_status = 'Completed'
                    AND o.order_date BETWEEN %s AND %s
                """, (from_date, to_date))
                total_profit = cur.fetchone()[0] or 0

        # Best Selling Genre
        cur.execute("""
            SELECT b.genre, SUM(oi.quantity * oi.unit_price) AS genre_profit
            FROM Order_Item oi
            JOIN Orderss o ON oi.order_id = o.order_id
            JOIN Book b ON oi.book_id = b.book_id
            WHERE o.order_status = 'Completed'
            GROUP BY b.genre
            ORDER BY genre_profit DESC
            LIMIT 1
        """)
        best_selling_genre = cur.fetchone()
        best_selling_genre_name = best_selling_genre[0] if best_selling_genre else 'N/A'
        best_selling_genre_profit = best_selling_genre[1] if best_selling_genre else 0

        # Most Valued Customer
        cur.execute("""
            SELECT c.customer_name, SUM(o.total_amount) AS total_spent
            FROM Orderss o
            JOIN Customer c ON o.customer_id = c.customer_id
            WHERE o.order_status = 'Completed'
            GROUP BY c.customer_name
            ORDER BY total_spent DESC
            LIMIT 1
        """)
        most_valued_customer = cur.fetchone()
        most_valued_customer_name = most_valued_customer[0] if most_valued_customer else 'N/A'
        most_valued_customer_spent = most_valued_customer[1] if most_valued_customer else 0

        cur.close()

        return render_template(
            'admin_dashboard.html',
            total_profit=total_profit,
            best_selling_genre_name=best_selling_genre_name,
            best_selling_genre_profit=best_selling_genre_profit,
            most_valued_customer_name=most_valued_customer_name,
            most_valued_customer_spent=most_valued_customer_spent
        )
    except Exception as e:
        print(f"Error in admin_dashboard: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

@app.route('/customer_analytics')
def customer_analytics():
    if not session.get('is_admin'):
        flash("Admin access required.", "danger")
        return redirect(url_for('admin_login'))

    try:
        cur = mysql.connection.cursor()

        # Total profits by customer type
        query1 = """
            SELECT c.customer_type, SUM(o.total_amount) AS total_profits
            FROM Customer c
            JOIN Orderss o ON c.customer_id = o.customer_id
            WHERE o.order_status = 'Completed'
            GROUP BY c.customer_type
        """
        cur.execute(query1)
        profits = {row[0]: row[1] for row in cur.fetchall()}

        # Number of customers by type
        query2 = """
            SELECT customer_type, COUNT(*) AS num_customers
            FROM Customer
            GROUP BY customer_type
        """
        cur.execute(query2)
        customer_counts = {row[0]: row[1] for row in cur.fetchall()}

        # Popular books for each type
        query3 = """
            SELECT c.customer_type, b.title, COUNT(oi.book_id) AS total_sales
            FROM Customer c
            JOIN Orderss o ON c.customer_id = o.customer_id
            JOIN Order_Item oi ON o.order_id = oi.order_id
            JOIN Book b ON oi.book_id = b.book_id
            WHERE o.order_status = 'Completed'
            GROUP BY c.customer_type, b.title
            ORDER BY total_sales DESC
            LIMIT 2
        """
        cur.execute(query3)
        popular_books = cur.fetchall()

        # Popular genres for each type
        query4 = """
            SELECT c.customer_type, b.genre, COUNT(oi.book_id) AS total_sales
            FROM Customer c
            JOIN Orderss o ON c.customer_id = o.customer_id
            JOIN Order_Item oi ON o.order_id = oi.order_id
            JOIN Book b ON oi.book_id = b.book_id
            WHERE o.order_status = 'Completed'
            GROUP BY c.customer_type, b.genre
            ORDER BY total_sales DESC
            LIMIT 2
        """
        cur.execute(query4)
        popular_genres = cur.fetchall()

        # Average spending per order for each type
        query5 = """
            SELECT c.customer_type, AVG(o.total_amount) AS avg_spending
            FROM Customer c
            JOIN Orderss o ON c.customer_id = o.customer_id
            WHERE o.order_status = 'Completed'
            GROUP BY c.customer_type
        """
        cur.execute(query5)
        avg_spending = {row[0]: row[1] for row in cur.fetchall()}

        cur.close()

        # Combine the data for rendering
        analytics = {
            "profits": profits,
            "customer_counts": customer_counts,
            "popular_books": popular_books,
            "popular_genres": popular_genres,
            "avg_spending": avg_spending,
        }
        return render_template('customer_analytics.html', analytics=analytics)
    except Exception as e:
        print("Error fetching customer analytics:", e)
        flash("Error fetching analytics. Please try again later.", "danger")
        return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

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
            CREATE TABLE IF NOT EXISTS Orderss (
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
                FOREIGN KEY (order_id) REFERENCES Orderss(order_id),
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
                FOREIGN KEY (order_id) REFERENCES Orderss(order_id)
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
                FOREIGN KEY (order_id) REFERENCES Orderss(order_id),
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

if __name__ == '__main__':
    app.run(debug=True)
