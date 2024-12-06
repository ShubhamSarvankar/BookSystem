import mysql.connector

# Connect to the Database
db = mysql.connector.connect(
    host="sql5.freemysqlhosting.net",  # Update with your database host
    user="sql5749107",                # Update with your database user
    password="e1Hs4PCSR6",            # Update with your database password
    database="sql5749107"             # Update with your database name
)
cursor = db.cursor()

# --- Populate Address Table ---
def populate_address_table():
    addresses = [
        ("123 Maple Street", "Springfield", "IL", "62704", "USA", "Home"),
        ("456 Oak Avenue", "Madison", "WI", "53703", "USA", "Home"),
        ("789 Pine Lane", "Austin", "TX", "73301", "USA", "Business"),
        ("101 Birch Boulevard", "Seattle", "WA", "98101", "USA", "Home"),
        ("555 Elm Drive", "Boston", "MA", "02108", "USA", "Business"),
        ("789 Cedar Road", "New York", "NY", "10001", "USA", "Home"),
        ("321 Willow Street", "Chicago", "IL", "60614", "USA", "Home"),
        ("888 Redwood Avenue", "San Francisco", "CA", "94102", "USA", "Business"),
        ("222 Aspen Drive", "Denver", "CO", "80202", "USA", "Home"),
        ("678 Magnolia Court", "Portland", "OR", "97204", "USA", "Business")
    ]
    for address in addresses:
        cursor.execute("""
            INSERT INTO Address (street, city, state, zip, country, address_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, address)
    db.commit()

# --- Populate Customer Table ---
def populate_customer_table():
    customers = [
        ("John Doe", "john@example.com", "password123", "Individual", 1),
        ("Jane Smith", "jane@example.com", "password456", "Individual", 2),
        ("Tech Solutions Inc.", "contact@techsolutions.com", "password789", "Business", 3),
        ("Emily White", "emily@example.com", "password101", "Individual", 4),
        ("Global Corp.", "info@globalcorp.com", "password102", "Business", 5),
        ("Michael Brown", "michael@example.com", "password103", "Individual", 6),
        ("Jennifer Davis", "jennifer@example.com", "password104", "Individual", 7),
        ("Bright Ideas LLC", "ideas@bright.com", "password105", "Business", 8),
        ("Sophia Wilson", "sophia@example.com", "password106", "Individual", 9),
        ("Innovate Tech", "support@innovate.com", "password107", "Business", 10)
    ]
    for customer in customers:
        cursor.execute("""
            INSERT INTO Customer (customer_name, email, password, customer_type, address_id)
            VALUES (%s, %s, %s, %s, %s)
        """, customer)
    db.commit()

# --- Populate Individual Customer Table ---
def populate_individual_customer_table():
    individuals = [
        (1, 30, "Single", "Male", 55000),
        (2, 25, "Married", "Female", 62000),
        (4, 28, "Single", "Female", 48000),
        (6, 35, "Married", "Male", 72000),
        (7, 40, "Single", "Female", 54000),
        (9, 32, "Married", "Female", 60000)
    ]
    for individual in individuals:
        cursor.execute("""
            INSERT INTO Individual_Customer (customer_id, age, marital_status, gender, income)
            VALUES (%s, %s, %s, %s, %s)
        """, individual)
    db.commit()

# --- Populate Business Customer Table ---
def populate_business_customer_table():
    businesses = [
        (3, "Technology", 1200000),
        (5, "Retail", 900000),
        (8, "Consulting", 750000),
        (10, "Software", 1300000)
    ]
    for business in businesses:
        cursor.execute("""
            INSERT INTO Business_Customer (customer_id, business_category, gross_income)
            VALUES (%s, %s, %s)
        """, business)
    db.commit()

# --- Populate Publisher Table ---
def populate_publisher_table():
    publishers = [
        ("Penguin Random House", "contact@penguin.com", "123-456-7890", 1),
        ("HarperCollins", "info@harpercollins.com", "987-654-3210", 2),
        ("Simon & Schuster", "support@simon.com", "555-123-4567", 3),
        ("Macmillan", "sales@macmillan.com", "111-222-3333", 4)
    ]
    for publisher in publishers:
        cursor.execute("""
            INSERT INTO Publisher (publisher_name, email, phone, address_id)
            VALUES (%s, %s, %s, %s)
        """, publisher)
    db.commit()

# --- Populate Book Table ---
def populate_book_table():
    books = [
        ("The Great Gatsby", "F. Scott Fitzgerald", "Fiction", 10.99, 50, 1, "Hardcover"),
        ("1984", "George Orwell", "Dystopian", 8.99, 40, 1, "Softcover"),
        ("To Kill a Mockingbird", "Harper Lee", "Fiction", 12.99, 30, 2, "First Edition"),
        ("The Catcher in the Rye", "J.D. Salinger", "Classic", 9.99, 20, 3, "Softcover"),
        ("Moby Dick", "Herman Melville", "Adventure", 15.99, 15, 4, "Hardcover"),
        ("Pride and Prejudice", "Jane Austen", "Romance", 11.99, 25, 2, "Softcover"),
        ("War and Peace", "Leo Tolstoy", "Historical", 19.99, 10, 3, "Hardcover"),
        ("The Hobbit", "J.R.R. Tolkien", "Fantasy", 13.99, 35, 1, "First Edition"),
        ("Crime and Punishment", "Fyodor Dostoevsky", "Classic", 14.99, 20, 2, "Softcover"),
        ("The Odyssey", "Homer", "Epic", 18.99, 5, 4, "Hardcover")
    ]
    for book in books:
        cursor.execute("""
            INSERT INTO Book (title, author, genre, price, inventory, publisher_id, cover_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, book)
    db.commit()

# --- Populate Order Table ---
def populate_order_table():
    orders = [
        (1, "2024-12-01", "Completed", 25.98),
        (2, "2024-12-02", "Pending", 8.99),
        (4, "2024-12-03", "Cancelled", 15.99),
        (6, "2024-12-04", "Completed", 45.97),
        (7, "2024-12-05", "Completed", 13.99),
        (9, "2024-12-06", "Pending", 18.99),
        (3, "2024-12-07", "Completed", 30.98),
        (5, "2024-12-08", "Cancelled", 11.99),
        (8, "2024-12-09", "Pending", 60.95),
        (10, "2024-12-10", "Completed", 50.97)
    ]
    for order in orders:
        cursor.execute("""
            INSERT INTO `Order` (customer_id, order_date, order_status, total_amount)
            VALUES (%s, %s, %s, %s)
        """, order)
    db.commit()

# --- Populate Order_Item Table ---
def populate_order_item_table():
    order_items = [
        (1, 1, 2, 1, 8.99),
        (1, 2, 3, 1, 12.99),
        (2, 4, 5, 1, 15.99),
        (3, 6, 7, 1, 19.99),
        (4, 8, 8, 1, 13.99),
        (5, 9, 9, 1, 18.99),
        (6, 10, 10, 1, 18.99),
        (7, 1, 1, 1, 10.99),
        (8, 2, 2, 1, 12.99),
        (9, 3, 4, 1, 15.99)
    ]
    for order_item in order_items:
        cursor.execute("""
            INSERT INTO Order_Item (order_id, book_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
        """, order_item)
    db.commit()

# --- Populate Payment Table ---
def populate_payment_table():
    payments = [
        (1, "Credit Card", "2024-12-01", 25.98),
        (2, "PayPal", "2024-12-02", 8.99),
        (4, "Credit Card", "2024-12-03", 15.99),
        (6, "Bank Transfer", "2024-12-04", 45.97),
        (7, "Credit Card", "2024-12-05", 13.99),
        (9, "PayPal", "2024-12-06", 18.99),
        (3, "Credit Card", "2024-12-07", 30.98),
        (5, "Bank Transfer", "2024-12-08", 11.99),
        (8, "PayPal", "2024-12-09", 60.95),
        (10, "Credit Card", "2024-12-10", 50.97)
    ]
    for payment in payments:
        cursor.execute("""
            INSERT INTO Payment (order_id, payment_method, payment_date, amount)
            VALUES (%s, %s, %s, %s)
        """, payment)
    db.commit()

# --- Populate Shipment Table ---
def populate_shipment_table():
    shipments = [
        (1, "2024-12-02", "Shipped", 1),
        (2, "2024-12-03", "Pending", 2),
        (4, "2024-12-05", "Delivered", 3),
        (6, "2024-12-06", "Shipped", 4),
        (7, "2024-12-07", "Delivered", 5),
        (9, "2024-12-08", "Pending", 6),
        (3, "2024-12-09", "Shipped", 7),
        (5, "2024-12-10", "Cancelled", 8),
        (8, "2024-12-11", "Delivered", 9),
        (10, "2024-12-12", "Shipped", 10)
    ]
    for shipment in shipments:
        cursor.execute("""
            INSERT INTO Shipment (order_id, shipment_date, delivery_status, address_id)
            VALUES (%s, %s, %s, %s)
        """, shipment)
    db.commit()

# --- Populate Cart Table ---
def populate_cart_table():
    carts = [
        (1, 1, 2),
        (2, 4, 1),
        (4, 6, 3),
        (6, 7, 2),
        (7, 8, 1),
        (9, 10, 1),
        (3, 2, 1),
        (5, 3, 1),
        (8, 5, 1),
        (10, 9, 2)
    ]
    for cart in carts:
        cursor.execute("""
            INSERT INTO Cart (customer_id, book_id, quantity)
            VALUES (%s, %s, %s)
        """, cart)
    db.commit()

# --- Populate Review Table ---
def populate_review_table():
    reviews = [
        (1, 1, 5, "An amazing book!", "2024-12-01"),
        (2, 2, 4, "Interesting read.", "2024-12-02"),
        (4, 3, 5, "Loved it!", "2024-12-03"),
        (6, 4, 3, "It was okay.", "2024-12-04"),
        (7, 5, 5, "Highly recommend!", "2024-12-05"),
        (9, 6, 2, "Not great.", "2024-12-06"),
        (3, 7, 4, "Good book.", "2024-12-07"),
        (5, 8, 5, "Fantastic!", "2024-12-08"),
        (8, 9, 3, "Decent read.", "2024-12-09"),
        (10, 10, 4, "Enjoyed it.", "2024-12-10")
    ]
    for review in reviews:
        cursor.execute("""
            INSERT INTO Review (book_id, customer_id, ranking, review_text, review_date)
            VALUES (%s, %s, %s, %s, %s)
        """, review)
    db.commit()

# --- Execute All Population Functions ---
populate_address_table()
populate_customer_table()
populate_individual_customer_table()
populate_business_customer_table()
populate_publisher_table()
populate_book_table()
populate_order_table()
populate_order_item_table()
populate_payment_table()
populate_shipment_table()
populate_cart_table()
populate_review_table()

print("All data populated successfully!")

# Close the Database Connection
cursor.close()
db.close()