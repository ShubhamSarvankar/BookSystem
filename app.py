from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
import re

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'shubham'  # Replace with your MySQL username
app.config['MYSQL_PASSWORD'] = 'shubhamsarvankar13'  # Replace with your MySQL password
app.config['MYSQL_DB'] = 'ecommerce'  # Replace with your database name
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

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

# Test Route
@app.route('/')
def home():
    return "Flask app is working! Go to /customers to test CRUD operations."

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

if __name__ == '__main__':
    app.run(debug=True)