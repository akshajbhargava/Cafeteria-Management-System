# Cafeteria-Management-System
Streamlit-based Cafeteria Management System with MySQL backend. Supports customer signup/login, menu browsing, cart, discount codes, secure checkout, order history, favorites, and order tracking. Admin dashboard includes real-time stats, menu CRUD, inventory and low-stock alerts, and sales reports.

# 🍽️ Cafeteria Management System

A modern, full-stack cafeteria management system built with Streamlit and MySQL. Designed for workplace dining with a sleek, Uber Eats-inspired interface.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

### 👤 Customer Portal
- **User Authentication** - Secure signup/login with email and phone validation
- **Menu Browser** - Search and filter items by category with real-time stock display
- **Shopping Cart** - Dynamic cart management with quantity controls and live total
- **Discount Codes** - Apply promo codes (WELCOME10, STUDENT20, SAVE15, FREESHIP)
- **Multiple Payment Options** - UPI, Card, and Cash payment modes with simulated checkout
- **Order History** - View complete order history with detailed item breakdowns
- **Favorites** - Save favorite items for quick reordering with heart icon
- **Order Tracking** - Track orders by unique reference number
- **Rating System** - Rate and review completed orders with feedback

### 🔐 Admin Portal
- **Dashboard Analytics** - Real-time statistics for today's orders, revenue, customers, and total orders
- **Menu Management** - Full CRUD operations for menu items with price and stock updates
- **Inventory Tracking** - Stock monitoring with color-coded alerts (red for critical, orange for low)
- **Low Stock Alerts** - Automatic warnings for items with stock ≤ 10
- **Order Management** - View all customer orders with complete details
- **Sales Reports** - Generate and export sales data by custom date range to CSV

## 🛠️ Tech Stack

- **Frontend:** Streamlit (Python web framework)
- **Backend:** Python 3.10+
- **Database:** MySQL 8.0+
- **Libraries:** 
  - `streamlit` - Web application framework
  - `mysql-connector-python` - MySQL database connectivity
  - `pandas` - Data manipulation and analysis
  - `hashlib` - SHA-256 password encryption
  - `uuid` - Unique order reference generation
  - `re` - Regular expressions for validation
  - `datetime` - Date and time handling

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.10 or higher
- MySQL Server 8.0 or higher
- pip (Python package manager)
- Git (for cloning the repository)

## 🚀 Installation & Setup

### Step 1: Clone the Repository

### Step 2: Install Python Dependencies

### Step 3: Configure MySQL

**Start MySQL Server:**

**Windows:**

**Mac:**

**Linux:**

**Update Database Configuration (if needed):**

Edit `database.py` and modify the credentials if your MySQL setup is different:

DB_CONFIG = {
'host': '127.0.0.1', # Change if using remote MySQL
'user': 'root', # Your MySQL username
'password': 'root', # Your MySQL password
'database': 'cafeteria_db' # Database name (auto-created)
}

text

### Step 4: Run the Application
streamlit run app.py

text

The application will automatically:
- ✅ Create the `cafeteria_db` database
- ✅ Create all 7 required tables
- ✅ Insert default admin user
- ✅ Add 8 sample menu items

Open your browser and navigate to: [**http://localhost:8501**](http://localhost:8501)


