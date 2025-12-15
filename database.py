import mysql.connector
from mysql.connector import Error
import hashlib
from datetime import datetime
import uuid
import logging
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# DATABASE CONFIGURATION
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'root',
    'database': 'cafeteria_db'  
}

# DATABASE CONNECTION
def get_connection():
    """Create and return a database connection."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        return None

# PASSWORD HASHING
def hash_password(password):
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

# DATABASE INITIALIZATION
def initialize_database():
    """Create database and tables if they don't exist."""
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = connection.cursor()

        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('Customer', 'Admin') NOT NULL,
                email VARCHAR(100),
                phone VARCHAR(15),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_username (username)
            )
        """)

        # Create menu table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_name VARCHAR(100) NOT NULL,
                category VARCHAR(50) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                stock INT NOT NULL DEFAULT 0,
                is_available BOOLEAN DEFAULT TRUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_category (category),
                INDEX idx_availability (is_available)
            )
        """)

        # Create orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_reference VARCHAR(50) UNIQUE NOT NULL,
                username VARCHAR(50) NOT NULL,
                total_amount DECIMAL(10, 2) NOT NULL,
                payment_mode VARCHAR(20) NOT NULL,
                status ENUM('Pending', 'Preparing', 'Ready', 'Completed', 'Cancelled') DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username) ON UPDATE CASCADE,
                INDEX idx_username (username),
                INDEX idx_status (status),
                INDEX idx_created_at (created_at),
                INDEX idx_order_ref (order_reference)
            )
        """)

        # Create order_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                item_name VARCHAR(100) NOT NULL,
                quantity INT NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                total DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                INDEX idx_order_id (order_id)
            )
        """)

        # Create order_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                status VARCHAR(20) NOT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
            )
        """)

        # Favorites table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                item_name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_favorite (username, item_name),
                FOREIGN KEY (username) REFERENCES users(username) ON UPDATE CASCADE
            )
        """)

        # Ratings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_ratings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_reference VARCHAR(50) UNIQUE NOT NULL,
                rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_reference) REFERENCES orders(order_reference)
            )
        """)

        connection.commit()

        # Insert default admin if not exists
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            admin_password = hash_password("Admin@123")
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                ('admin', admin_password, 'Admin')
            )
            connection.commit()
            logger.info("Default admin user created successfully")

        # Insert sample menu items if table is empty
        cursor.execute("SELECT COUNT(*) FROM menu")
        if cursor.fetchone()[0] == 0:
            sample_menu = [
                ('Dal Chawal', 'Food', 50.0, 10, 'Traditional dal and rice combo'),
                ('Thali', 'Food', 80.0, 5, 'Complete meal with variety'),
                ('Half Thali', 'Food', 40.0, 20, 'Half portion thali'),
                ('Gulab Jamun', 'Dessert', 15.0, 15, 'Sweet dessert'),
                ('Samosa', 'Snack', 20.0, 25, 'Crispy fried snack'),
                ('Chai', 'Beverage', 10.0, 50, 'Hot tea'),
                ('Coffee', 'Beverage', 15.0, 30, 'Hot coffee'),
                ('Sandwich', 'Snack', 30.0, 12, 'Vegetable sandwich'),
            ]
            cursor.executemany(
                "INSERT INTO menu (item_name, category, price, stock, description) VALUES (%s, %s, %s, %s, %s)",
                sample_menu
            )
            connection.commit()
            logger.info("Sample menu items added successfully")

        cursor.close()
        connection.close()
        logger.info("✓ Database initialized successfully!")
        return True

    except Error as e:
        logger.error(f"✗ Error initializing database: {e}")
        return False

# USER MANAGEMENT FUNCTIONS
def add_user(username, password, role='Customer', email=None, phone=None):
    """Add a new user to the database."""
    connection = get_connection()
    if not connection:
        logger.error("Database connection failed while adding user")
        return False, "Database connection failed"

    try:
        cursor = connection.cursor()
        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password, role, email, phone) VALUES (%s, %s, %s, %s, %s)",
            (username, hashed_password, role, email, phone)
        )
        connection.commit()
        cursor.close()
        connection.close()
        logger.info(f"User '{username}' added successfully with role '{role}'")
        return True, "User added successfully"
    except Error as e:
        logger.error(f"Error adding user '{username}': {e}")
        if "Duplicate entry" in str(e):
            return False, "Username already exists"
        return False, "Failed to create user account"

def validate_user(username, password):
    """Validate user credentials and return role."""
    connection = get_connection()
    if not connection:
        logger.error("Database connection failed during user validation")
        return None

    try:
        cursor = connection.cursor()
        hashed_password = hash_password(password)
        cursor.execute(
            "SELECT role FROM users WHERE username = %s AND password = %s",
            (username, hashed_password)
        )
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if result:
            logger.info(f"User '{username}' validated successfully as '{result[0]}'")
            return result[0]
        logger.warning(f"Failed login attempt for username: '{username}'")
        return None
    except Error as e:
        logger.error(f"Error validating user '{username}': {e}")
        return None

def user_exists(username):
    """Check if username already exists."""
    connection = get_connection()
    if not connection:
        logger.error("Database connection failed while checking user existence")
        return False

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        exists = result is not None
        logger.info(f"User existence check for '{username}': {exists}")
        return exists
    except Error as e:
        logger.error(f"Error checking if user '{username}' exists: {e}")
        return False

# MENU MANAGEMENT FUNCTIONS
def get_menu(available_only=False):
    """Fetch all menu items."""
    connection = get_connection()
    if not connection:
        logger.error("Database connection failed while fetching menu")
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM menu"
        if available_only:
            query += " WHERE is_available = TRUE AND stock > 0"
        query += " ORDER BY category, item_name"
       
        cursor.execute(query)
        items = cursor.fetchall()
       
        # Convert Decimal to float for all price fields
        for item in items:
            if 'price' in item:
                item['price'] = float(item['price'])
       
        cursor.close()
        connection.close()
        logger.info(f"Fetched {len(items)} menu items (available_only={available_only})")
        return items
    except Error as e:
        logger.error(f"Error fetching menu: {e}")
        return []

def get_menu_df():
    """Get menu as pandas DataFrame for Streamlit."""
    menu_items = get_menu(available_only=True)
   
    if not menu_items:
        logger.warning("No menu items found, returning default menu")
        return pd.DataFrame({
            "Items": ["Dal Chawal", "Thali", "Half Thali", "Gulab Jamun", "Samosa", "Chai", "Coffee", "Sandwich"],
            "Category": ["Food", "Food", "Food", "Dessert", "Snack", "Beverage", "Beverage", "Snack"],
            "Price (₹)": [50.0, 80.0, 40.0, 15.0, 20.0, 10.0, 15.0, 30.0],
            "Stock": [10, 5, 20, 15, 25, 50, 30, 12],
        })
   
    df = pd.DataFrame(menu_items)
    df = df.rename(columns={
        'item_name': 'Items',
        'category': 'Category',
        'price': 'Price (₹)',
        'stock': 'Stock'
    })
    return df[['Items', 'Category', 'Price (₹)', 'Stock']]

def add_menu_item(item_name, category, price, stock, description=None):
    """Add a new menu item."""
    connection = get_connection()
    if not connection:
        logger.error("Database connection failed while adding menu item")
        return False, "Database connection failed"

    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO menu (item_name, category, price, stock, description) VALUES (%s, %s, %s, %s, %s)",
            (item_name, category, price, stock, description)
        )
        connection.commit()
        cursor.close()
        connection.close()
        logger.info(f"Menu item '{item_name}' added successfully")
        return True, "Menu item added successfully"
    except Error as e:
        logger.error(f"Error adding menu item '{item_name}': {e}")
        return False, "Failed to add menu item"

def update_menu_item(item_id, item_name, category, price, stock, is_available=True, description=None):
    """Update an existing menu item."""
    connection = get_connection()
    if not connection:
        logger.error("Database connection failed while updating menu item")
        return False, "Database connection failed"

    try:
        cursor = connection.cursor()
        cursor.execute(
            """UPDATE menu SET item_name = %s, category = %s, price = %s,
               stock = %s, is_available = %s, description = %s WHERE id = %s""",
            (item_name, category, price, stock, is_available, description, item_id)
        )
        connection.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        connection.close()
       
        if affected_rows > 0:
            logger.info(f"Menu item ID {item_id} updated successfully")
            return True, "Menu item updated successfully"
        else:
            logger.warning(f"No menu item found with ID {item_id}")
            return False, "Menu item not found"
    except Error as e:
        logger.error(f"Error updating menu item ID {item_id}: {e}")
        return False, "Failed to update menu item"

def delete_menu_item(item_id):
    """Delete a menu item."""
    connection = get_connection()
    if not connection:
        logger.error("Database connection failed while deleting menu item")
        return False, "Database connection failed"

    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM menu WHERE id = %s", (item_id,))
        connection.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        connection.close()
       
        if affected_rows > 0:
            logger.info(f"Menu item ID {item_id} deleted successfully")
            return True, "Menu item deleted successfully"
        else:
            logger.warning(f"No menu item found with ID {item_id}")
            return False, "Menu item not found"
    except Error as e:
        logger.error(f"Error deleting menu item ID {item_id}: {e}")
        return False, "Failed to delete menu item"

def check_stock_availability(item_name, quantity):
    """Check if sufficient stock is available for an item."""
    connection = get_connection()
    if not connection:
        logger.error(f"Database connection failed while checking stock for '{item_name}'")
        return False, "Database connection failed"

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT stock, is_available FROM menu WHERE item_name = %s",
            (item_name,)
        )
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if not result:
            logger.warning(f"Item '{item_name}' not found in menu")
            return False, f"Item '{item_name}' not found"
       
        if not result['is_available']:
            logger.warning(f"Item '{item_name}' is not available")
            return False, f"Item '{item_name}' is not available"
       
        if result['stock'] < quantity:
            logger.warning(f"Insufficient stock for '{item_name}': Available={result['stock']}, Required={quantity}")
            return False, f"Insufficient stock. Available: {result['stock']}, Required: {quantity}"
       
        logger.info(f"Stock available for '{item_name}': {result['stock']} >= {quantity}")
        return True, "Stock available"
    except Error as e:
        logger.error(f"Error checking stock for '{item_name}': {e}")
        return False, "Failed to check stock availability"

def get_low_stock_items(threshold=5):
    """Get items with low stock."""
    connection = get_connection()
    if not connection:
        logger.error("Database connection failed while fetching low stock items")
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM menu WHERE stock <= %s ORDER BY stock ASC",
            (threshold,)
        )
        items = cursor.fetchall()
       
        # Convert Decimal to float
        for item in items:
            if 'price' in item:
                item['price'] = float(item['price'])
       
        cursor.close()
        connection.close()
        logger.info(f"Found {len(items)} items with stock <= {threshold}")
        return items
    except Error as e:
        logger.error(f"Error fetching low stock items: {e}")
        return []

# ORDER MANAGEMENT FUNCTIONS
def generate_order_reference():
    """Generate a unique order reference."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8].upper()
    order_ref = f"ORD-{timestamp}-{unique_id}"
    logger.info(f"Generated order reference: {order_ref}")
    return order_ref

def create_order(username, cart_items, payment_mode, order_reference=None):
    """Create a new order with items using transaction."""
    if not order_reference:
        order_reference = generate_order_reference()
   
    connection = get_connection()
    if not connection:
        logger.error(f"Database connection failed while creating order for user '{username}'")
        return False, "Database connection failed", None

    try:
        cursor = connection.cursor()
        connection.start_transaction()
        logger.info(f"Starting order creation for user '{username}' with reference '{order_reference}'")

        # Validate stock for all items first
        for item in cart_items:
            success, message = check_stock_availability(item['name'], item['quantity'])
            if not success:
                connection.rollback()
                logger.warning(f"Order creation failed for '{username}': {message}")
                return False, message, None

        # Calculate total amount
        total_amount = sum(item['total'] for item in cart_items)
        logger.info(f"Order total amount: ₹{total_amount}")

        # Insert order
        cursor.execute(
            """INSERT INTO orders (order_reference, username, total_amount, payment_mode, status)
               VALUES (%s, %s, %s, %s, %s)""",
            (order_reference, username, total_amount, payment_mode, 'Completed')
        )
        order_id = cursor.lastrowid
        logger.info(f"Order inserted with ID: {order_id}")

        # Insert order items and update stock
        for item in cart_items:
            cursor.execute(
                """INSERT INTO order_items (order_id, item_name, quantity, price, total)
                   VALUES (%s, %s, %s, %s, %s)""",
                (order_id, item['name'], item['quantity'], item['price'], item['total'])
            )
            logger.info(f"Added item '{item['name']}' x{item['quantity']} to order")

            cursor.execute(
                "UPDATE menu SET stock = stock - %s WHERE item_name = %s",
                (item['quantity'], item['name'])
            )
            logger.info(f"Updated stock for '{item['name']}': reduced by {item['quantity']}")

        # Add to order history
        cursor.execute(
            "INSERT INTO order_history (order_id, status) VALUES (%s, %s)",
            (order_id, 'Completed')
        )

        connection.commit()
        cursor.close()
        connection.close()
       
        logger.info(f"✓ Order '{order_reference}' created successfully for user '{username}'")
        return True, "Order created successfully", order_reference
       
    except Error as e:
        if connection:
            connection.rollback()
            logger.error(f"Transaction rolled back for order '{order_reference}'")
        logger.error(f"✗ Error creating order for user '{username}': {e}")
        return False, "Order creation failed. Please try again.", None

def get_user_orders(username):
    """Fetch all orders for a specific user."""
    connection = get_connection()
    if not connection:
        logger.error(f"Database connection failed while fetching orders for user '{username}'")
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM orders WHERE username = %s ORDER BY created_at DESC",
            (username,)
        )
        orders = cursor.fetchall()

        # Get items for each order and convert data types
        for order in orders:
            # Convert Decimal to float
            if 'total_amount' in order:
                order['total_amount'] = float(order['total_amount'])
           
            # Fetch order items
            cursor.execute(
                "SELECT * FROM order_items WHERE order_id = %s",
                (order['id'],)
            )
            items = cursor.fetchall()
           
            # Convert Decimal to float for items
            for item in items:
                if 'price' in item:
                    item['price'] = float(item['price'])
                if 'total' in item:
                    item['total'] = float(item['total'])
           
            order['items'] = items

        cursor.close()
        connection.close()
        logger.info(f"Retrieved {len(orders)} orders for user '{username}'")
        return orders
    except Error as e:
        logger.error(f"Error fetching orders for user '{username}': {e}")
        return []

def get_all_orders(limit=50):
    """Fetch all orders (for admin)."""
    connection = get_connection()
    if not connection:
        logger.error("Database connection failed while fetching all orders")
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM orders ORDER BY created_at DESC LIMIT %s",
            (limit,)
        )
        orders = cursor.fetchall()

        # Get items for each order and convert data types
        for order in orders:
            # Convert Decimal to float
            if 'total_amount' in order:
                order['total_amount'] = float(order['total_amount'])
           
            # Fetch order items
            cursor.execute(
                "SELECT * FROM order_items WHERE order_id = %s",
                (order['id'],)
            )
            items = cursor.fetchall()
           
            # Convert Decimal to float for items
            for item in items:
                if 'price' in item:
                    item['price'] = float(item['price'])
                if 'total' in item:
                    item['total'] = float(item['total'])
           
            order['items'] = items

        cursor.close()
        connection.close()
        logger.info(f"Retrieved {len(orders)} orders (admin view, limit={limit})")
        return orders
    except Error as e:
        logger.error(f"Error fetching all orders: {e}")
        return []

def get_order_by_reference(order_reference):
    """Get order details by order reference."""
    connection = get_connection()
    if not connection:
        logger.error(f"Database connection failed while fetching order '{order_reference}'")
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM orders WHERE order_reference = %s",
            (order_reference,)
        )
        order = cursor.fetchone()
       
        if order:
            # Convert Decimal to float
            if 'total_amount' in order:
                order['total_amount'] = float(order['total_amount'])
           
            # Fetch order items
            cursor.execute(
                "SELECT * FROM order_items WHERE order_id = %s",
                (order['id'],)
            )
            items = cursor.fetchall()
           
            # Convert Decimal to float for items
            for item in items:
                if 'price' in item:
                    item['price'] = float(item['price'])
                if 'total' in item:
                    item['total'] = float(item['total'])
           
            order['items'] = items
            logger.info(f"Retrieved order '{order_reference}' successfully")
        else:
            logger.warning(f"Order '{order_reference}' not found")

        cursor.close()
        connection.close()
        return order
    except Error as e:
        logger.error(f"Error fetching order by reference '{order_reference}': {e}")
        return None

def update_order_status(order_id, status):
    """Update order status."""
    connection = get_connection()
    if not connection:
        logger.error(f"Database connection failed while updating order ID {order_id}")
        return False, "Database connection failed"

    try:
        cursor = connection.cursor()
       
        # Update order status
        cursor.execute(
            "UPDATE orders SET status = %s WHERE id = %s",
            (status, order_id)
        )
        affected_rows = cursor.rowcount
       
        if affected_rows > 0:
            # Add to history
            cursor.execute(
                "INSERT INTO order_history (order_id, status) VALUES (%s, %s)",
                (order_id, status)
            )
            connection.commit()
            logger.info(f"Order ID {order_id} status updated to '{status}'")
            cursor.close()
            connection.close()
            return True, "Order status updated successfully"
        else:
            logger.warning(f"No order found with ID {order_id}")
            cursor.close()
            connection.close()
            return False, "Order not found"
           
    except Error as e:
        logger.error(f"Error updating order status for ID {order_id}: {e}")
        return False, "Failed to update order status"

# ADMIN STATISTICS
def get_dashboard_stats():
    """Get statistics for admin dashboard."""
    connection = get_connection()
    if not connection:
        logger.error("Database connection failed while fetching dashboard stats")
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        stats = {}

        # Today's orders count
        cursor.execute(
            "SELECT COUNT(*) as count FROM orders WHERE DATE(created_at) = CURDATE()"
        )
        stats['today_orders'] = cursor.fetchone()['count']

        # Today's revenue (with NULL safety)
        cursor.execute(
            "SELECT COALESCE(SUM(total_amount), 0) as revenue FROM orders WHERE DATE(created_at) = CURDATE()"
        )
        stats['today_revenue'] = float(cursor.fetchone()['revenue'])

        # Total menu items
        cursor.execute("SELECT COUNT(*) as count FROM menu")
        stats['menu_items'] = cursor.fetchone()['count']

        # Low stock items (stock <= 5)
        cursor.execute("SELECT COUNT(*) as count FROM menu WHERE stock <= 5")
        stats['low_stock_items'] = cursor.fetchone()['count']

        # Total customers
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'Customer'")
        stats['total_customers'] = cursor.fetchone()['count']

        # Total orders
        cursor.execute("SELECT COUNT(*) as count FROM orders")
        stats['total_orders'] = cursor.fetchone()['count']

        cursor.close()
        connection.close()
        logger.info("Dashboard statistics retrieved successfully")
        return stats
    except Error as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        return None

# FAVORITES MANAGEMENT
def get_user_favorites(username):
    """Get user's favorite items."""
    connection = get_connection()
    if not connection:
        logger.error(f"Database connection failed while fetching favorites for '{username}'")
        return []

    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT item_name FROM favorites WHERE username = %s",
            (username,)
        )
        favorites = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        logger.info(f"Retrieved {len(favorites)} favorites for user '{username}'")
        return favorites
    except Error as e:
        logger.error(f"Error fetching favorites for user '{username}': {e}")
        return []

def add_favorite(username, item_name):
    """Add item to user's favorites."""
    connection = get_connection()
    if not connection:
        logger.error(f"Database connection failed while adding favorite for '{username}'")
        return False

    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT IGNORE INTO favorites (username, item_name) VALUES (%s, %s)",
            (username, item_name)
        )
        connection.commit()
        cursor.close()
        connection.close()
        logger.info(f"Added '{item_name}' to favorites for user '{username}'")
        return True
    except Error as e:
        logger.error(f"Error adding favorite for user '{username}': {e}")
        return False

def remove_favorite(username, item_name):
    """Remove item from user's favorites."""
    connection = get_connection()
    if not connection:
        logger.error(f"Database connection failed while removing favorite for '{username}'")
        return False

    try:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM favorites WHERE username = %s AND item_name = %s",
            (username, item_name)
        )
        connection.commit()
        cursor.close()
        connection.close()
        logger.info(f"Removed '{item_name}' from favorites for user '{username}'")
        return True
    except Error as e:
        logger.error(f"Error removing favorite for user '{username}': {e}")
        return False

# RATINGS MANAGEMENT
def add_order_rating(order_reference, rating, feedback=None):
    """Add rating for an order."""
    connection = get_connection()
    if not connection:
        logger.error(f"Database connection failed while adding rating for order '{order_reference}'")
        return False

    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO order_ratings (order_reference, rating, feedback) VALUES (%s, %s, %s)",
            (order_reference, rating, feedback)
        )
        connection.commit()
        cursor.close()
        connection.close()
        logger.info(f"Rating {rating}/5 added for order '{order_reference}'")
        return True
    except Error as e:
        logger.error(f"Error adding rating for order '{order_reference}': {e}")
        return False

def get_order_rating(order_reference):
    """Get rating for an order."""
    connection = get_connection()
    if not connection:
        logger.error(f"Database connection failed while fetching rating for order '{order_reference}'")
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM order_ratings WHERE order_reference = %s",
            (order_reference,)
        )
        rating = cursor.fetchone()
        cursor.close()
        connection.close()
        if rating:
            logger.info(f"Retrieved rating for order '{order_reference}'")
        return rating
    except Error as e:
        logger.error(f"Error fetching rating for order '{order_reference}': {e}")
        return None

# SALES DATA FOR REPORTS
def get_sales_data(start_date=None, end_date=None):
    """Get sales data for reports."""
    connection = get_connection()
    if not connection:
        logger.error("Database connection failed while fetching sales data")
        return []

    try:
        cursor = connection.cursor(dictionary=True)
       
        query = """
            SELECT
                DATE(created_at) as date,
                COUNT(*) as orders,
                SUM(total_amount) as revenue
            FROM orders
        """
       
        if start_date and end_date:
            query += " WHERE DATE(created_at) BETWEEN %s AND %s"
            params = (start_date, end_date)
            logger.info(f"Fetching sales data from {start_date} to {end_date}")
        else:
            query += " WHERE DATE(created_at) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
            params = ()
            logger.info("Fetching sales data for last 7 days")
       
        query += " GROUP BY DATE(created_at) ORDER BY date DESC"
       
        cursor.execute(query, params)
        sales_data = cursor.fetchall()
       
        # Convert Decimal to float
        for row in sales_data:
            if 'revenue' in row:
                row['revenue'] = float(row['revenue'])
       
        cursor.close()
        connection.close()
        logger.info(f"Retrieved {len(sales_data)} sales records")
        return sales_data
    except Error as e:
        logger.error(f"Error fetching sales data: {e}")
        return []

# INITIALIZE DATABASE ON IMPORT
if __name__ == "__main__":
    initialize_database()
else:
    initialize_database()