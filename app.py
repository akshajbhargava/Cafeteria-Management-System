import streamlit as st
import pandas as pd
import re
import time
from datetime import datetime

# Import all database functions
from database import (
    add_user, validate_user, user_exists, get_menu, add_menu_item,
    update_menu_item, delete_menu_item, create_order, get_user_orders,
    get_all_orders, get_dashboard_stats, get_low_stock_items,
    get_order_by_reference, update_order_status, generate_order_reference,
    check_stock_availability, get_user_favorites, add_favorite, remove_favorite,
    add_order_rating, get_order_rating
)

# Page configuration
st.set_page_config(
    page_title="Cafeteria Management System",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS Styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

:root {
  --green: #06C167;
  --green-dark: #059457;
  --black: #000000;
  --card: #111111;
  --border: #2A2A2A;
  --white: #FFFFFF;
  --gray: #9E9E9E;
}

.stApp {
  background: #000000;
  font-family: 'Inter', sans-serif;
  color: var(--white);
}

.main .block-container {
  background: radial-gradient(circle at top, #111111 0, #000000 100%);
  padding: 2.5rem 3rem;
  border-radius: 24px;
  max-width: 1180px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.nav-bar {
  background: rgba(0, 0, 0, 0.98);
  padding: 1rem 1.75rem;
  border-radius: 18px;
  margin-bottom: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.04);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-logo {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: radial-gradient(circle at 20% 0%, #06C167 0, #059457 40%, #000000 100%);
}

.nav-title {
  font-family: 'Poppins', sans-serif;
  font-size: 1.55rem;
  font-weight: 600;
  color: #FFFFFF;
}

.nav-subtitle {
  font-size: 0.85rem;
  color: var(--gray);
}

.stButton > button {
  background: linear-gradient(135deg, var(--green), var(--green-dark));
  color: #FFFFFF;
  border: none;
  border-radius: 999px;
  padding: 0.55rem 1.6rem;
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.18s ease-out;
}

.stButton > button:hover {
  filter: brightness(1.08);
}

.stTabs [data-baseweb="tab"] {
  background-color: #111111;
  border-radius: 999px;
  padding: 0.55rem 1.4rem;
  color: var(--gray);
  border: 1px solid transparent;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
  background: rgba(6, 193, 103, 0.16);
  border-color: rgba(6, 193, 103, 0.65);
  color: #FFFFFF;
}

[data-testid="stMetricValue"] {
  font-size: 1.8rem;
  color: var(--green);
  font-weight: 700;
}

[data-testid="stMetricLabel"] {
  font-size: 0.85rem;
  color: var(--gray);
  text-transform: uppercase;
}

.stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
  border-radius: 12px;
  border: 1px solid var(--border);
  background: #050505;
  color: #FFFFFF;
}

.price-badge {
  background: rgba(6, 193, 103, 0.12);
  color: var(--green);
  padding: 0.1rem 0.6rem;
  border-radius: 999px;
  font-weight: 600;
}

.welcome-header {
  background: linear-gradient(135deg, #151515 0%, #050505 55%, #000000 100%);
  border-radius: 18px;
  padding: 1.6rem 1.8rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 1.6rem;
}

.welcome-header h1 {
  color: #FFFFFF;
  font-size: 2rem;
  margin: 0;
}

.welcome-header p {
  color: var(--gray);
  font-size: 0.95rem;
  margin: 0;
}

.cart-badge {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #06C167;
  color: white;
  border-radius: 50%;
  width: 35px;
  height: 35px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1rem;
  box-shadow: 0 4px 12px rgba(6, 193, 103, 0.4);
  z-index: 999;
}

.stException, div[data-testid="stException"] {
  display: none !important;
}
</style>
""", unsafe_allow_html=True)

# Constants
DISCOUNT_CODES = {
    "WELCOME10": 10,
    "STUDENT20": 20,
    "FREESHIP": 5,
    "SAVE15": 15
}

ORDER_STATUSES = ["Preparing", "Ready", "Completed"]

# Session state initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"
if "cart" not in st.session_state:
    st.session_state.cart = []
if "cart_total" not in st.session_state:
    st.session_state.cart_total = 0
if "payment_mode" not in st.session_state:
    st.session_state.payment_mode = None
if "payment_reference" not in st.session_state:
    st.session_state.payment_reference = None
if "page_history" not in st.session_state:
    st.session_state.page_history = []
if "pending_payment_data" not in st.session_state:
    st.session_state.pending_payment_data = {}
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "final_payment_amount" not in st.session_state:
    st.session_state.final_payment_amount = None
if "discount_applied" not in st.session_state:
    st.session_state.discount_applied = 0

# Navigation functions
def go_to(page_name):
    current = st.session_state.current_page
    if current != page_name:
        st.session_state.page_history.append(current)
    st.session_state.current_page = page_name
    st.rerun()

def go_back(default_page="Home"):
    if st.session_state.page_history:
        prev = st.session_state.page_history.pop()
        st.session_state.current_page = prev
    else:
        st.session_state.current_page = default_page
    st.rerun()

def show_back_button(label="← Back"):
    if st.button(label, key=f"back_{st.session_state.current_page}"):
        go_back()

# Helper functions
def format_currency(amount):
    """Format amount as currency"""
    return f"₹{amount:,.2f}"

def get_cart_count():
    """Get total items in cart"""
    total = 0
    for item in st.session_state.cart:
        total += item.get("quantity", 0)
    return total

def show_cart_badge():
    """Display cart item count badge"""
    if st.session_state.logged_in and st.session_state.role == "Customer":
        count = get_cart_count()
        if count > 0:
            st.markdown(f"""
                <div class='cart-badge'>{count}</div>
            """, unsafe_allow_html=True)

# Navigation bar
def show_navigation_bar():
    st.markdown("""
        <div class='nav-bar'>
          <div class='nav-logo'></div>
          <div>
            <div class='nav-title'>Cafeteria Hub</div>
            <div class='nav-subtitle'>Workplace dining · Fast & predictable</div>
          </div>
        </div>
    """, unsafe_allow_html=True)
   
    show_cart_badge()
   
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1, 1, 1.2, 1, 3])
   
    with nav_col1:
        if st.button("Home", key="nav_home", use_container_width=True):
            go_to("Home")
   
    with nav_col2:
        if st.button("About", key="nav_about", use_container_width=True):
            go_to("About")
   
    with nav_col3:
        if st.button("Contact", key="nav_contact", use_container_width=True):
            go_to("Contact")
   
    with nav_col4:
        if st.session_state.logged_in:
            if st.button("Logout", key="nav_logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.session_state.role = ""
                st.session_state.cart = []
                st.session_state.cart_total = 0
                st.session_state.favorites = []
                go_to("Home")
        else:
            if st.button("Login", key="nav_login", use_container_width=True):
                go_to("CustomerLogin")
   
    st.markdown("---")

def get_menu_df():
    """Get menu from database and convert to DataFrame"""
    try:
        with st.spinner("Loading menu..."):
            menu_items = get_menu(available_only=True)
       
        if not menu_items:
            st.warning("No menu items available at the moment.")
            return pd.DataFrame()
       
        menu_data = {
            "ID": [item['id'] for item in menu_items],
            "Items": [item['item_name'] for item in menu_items],
            "Category": [item['category'] for item in menu_items],
            "Price (₹)": [float(item['price']) for item in menu_items],
            "Stock": [item['stock'] for item in menu_items],
            "Description": [item.get('description', '') for item in menu_items]
        }
        return pd.DataFrame(menu_data)
    except Exception as e:
        st.error(f"Error loading menu: {e}")
        return pd.DataFrame()

# Home page
def home_page():
    show_navigation_bar()
   
    st.markdown("<h1 style='text-align: center;'>Welcome to Cafeteria Hub</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px; color: #BBBBBB;'>Curated meals with a seamless ordering experience.</p>", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns(2)
   
    with col1:
        st.header("What We Offer")
        st.write("""
For Customers:
- Browse a curated, digital menu
- Manage your cart with a modern, responsive interface
- Choose convenient payment options (UPI, card, or cash)
- Track orders from placement to completion

For Administrators:
- Real-time overview of core metrics
- Simple inventory visibility
- Snapshot of sales performance
- Intuitive menu configuration
""")
       
        st.subheader("Key Highlights")
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("Menu Items", "20+", "Fresh Daily")
        with col_stat2:
            st.metric("Active Customers", "50+", "Growing")
        with col_stat3:
            st.metric("Orders Served", "1,000+", "And Counting")
   
    with col2:
        st.header("Get Started")
       
        st.markdown("### Customer Access")
        if st.button("Customer Login", use_container_width=True, key="customer_login"):
            go_to("CustomerLogin")
        if st.button("New Customer? Sign Up", use_container_width=True, key="customer_signup"):
            go_to("SignUp")

        st.markdown("---")
       
        st.markdown("### Administrator Access")
        st.info("Administrator access is restricted to authorized personnel.")
        if st.button("Administrator Login", use_container_width=True, key="admin_login"):
            go_to("AdminLogin")

        st.markdown("---")
       
        st.markdown("### Browse Menu Without Login")
        if st.button("Preview Menu", use_container_width=True):
            go_to("GuestPreview")

    st.markdown("---")
    st.markdown("<p class='footer-text'>Cafeteria Management System · Designed for a modern food ordering experience.</p>", unsafe_allow_html=True)

# About page
def about_page():
    show_navigation_bar()
    show_back_button()
   
    st.markdown("<h1 style='text-align: center;'>About Cafeteria Hub</h1>", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([2, 1])
   
    with col1:
        st.header("Our Story")
        st.write("Cafeteria Hub combines reliable food service with a frictionless digital ordering experience for workplaces. The platform provides a consistent way to browse, order, and manage meals in a technology-driven environment.")
       
        st.header("Why Cafeteria Hub")
        st.write("""
- Quality ingredients and predictable menus
- Hygienic preparation supported by clear processes
- Digital-first service for reduced waiting time
- Transparent and predictable pricing
- Focused on a straightforward, user-centric experience
""")
   
    with col2:
        st.header("At a Glance")
        st.metric("Years of Service", "5+")
        st.metric("Daily Orders", "100+")
        st.metric("Menu Variety", "20+")
        st.metric("Team Size", "15+")
       
        st.header("Core Principles")
        st.write("""
- Product quality and reliability
- Operational integrity
- Continuous improvement
- Practical customer focus
- Responsible sourcing
""")
   
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #9E9E9E;'>Thank you for choosing Cafeteria Hub.</p>", unsafe_allow_html=True)

# Contact page
def contact_page():
    show_navigation_bar()
    show_back_button()
   
    st.markdown("<h1 style='text-align: center;'>Contact Us</h1>", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns(2)
   
    with col1:
        st.header("Get in Touch")
        st.write("For questions, feedback, or support, submit your details and the team will respond promptly.")
       
        st.subheader("Send a Message")
        with st.form("contact_form", clear_on_submit=True):
            name = st.text_input("Name", placeholder="Enter your name")
            email = st.text_input("Email Address", placeholder="your.email@example.com")
            subject = st.selectbox("Subject", ["General Inquiry", "Feedback", "Complaint", "Suggestion", "Technical Support", "Other"])
            message = st.text_area("Message", placeholder="Write your message here...", height=150)
           
            submitted = st.form_submit_button("Send Message", use_container_width=True)
            if submitted:
                if name and email and message:
                    st.success("Message sent successfully. You will receive a response shortly.")
                else:
                    st.warning("Please complete all required fields before submitting.")
   
    with col2:
        st.header("Contact Details")
       
        st.subheader("Address")
        st.write("Cafeteria Hub\nMain Campus Building, Ground Floor\nYash Technologies Super Corridor\nIndore, Madhya Pradesh - 452006")
       
        st.subheader("Phone")
        st.write("Main: +91 98765 43210")
        st.write("Support: +91 98765 43211")
       
        st.subheader("Email")
        st.write("General: info@cafeteriahub.com")
        st.write("Support: support@cafeteriahub.com")
       
        st.subheader("Operating Hours")
        st.write("Monday – Friday: 9:00 AM – 7:00 PM\nSaturday: 9:00 AM – 6:00 PM\nSunday: Closed")
       
        st.subheader("Social")
        st.write("Facebook: @CafeteriaHub")
        st.write("Instagram: @cafeteria_hub")
        st.write("Twitter: @CafeteriaHub")

# Guest preview
def guest_preview():
    show_navigation_bar()
    show_back_button()
   
    st.title("Menu Preview")
    st.info("To place an order, create an account or log in.")
   
    menu_df = get_menu_df()
    if not menu_df.empty:
        st.subheader("Current Menu")
        display_df = menu_df[['Items', 'Category', 'Price (₹)', 'Stock']]
        st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("No menu items available.")

# Customer login
def customer_login_page():
    show_navigation_bar()
    show_back_button()
   
    st.title("Customer Login")
    st.write("Sign in to manage your orders and profile.")

    with st.form("customer_login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Login", use_container_width=True)
       
        if submitted:
            if username and password:
                with st.spinner("Logging in..."):
                    time.sleep(0.5)
                    role = validate_user(username, password)
               
                if role == "Customer":
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = role
                   
                    # Load user favorites
                    try:
                        st.session_state.favorites = get_user_favorites(username)
                    except:
                        st.session_state.favorites = []
                   
                    st.success(f"Welcome back, {username}!")
                    time.sleep(0.3)
                    go_to("Portal")
                elif role == "Admin":
                    st.error("Administrators cannot log in from the customer portal.")
                else:
                    st.error("Invalid username or password.")
            else:
                st.warning("Please provide both username and password.")

# Admin login
def admin_login_page():
    show_navigation_bar()
    show_back_button()
   
    st.title("Administrator Login")
    st.warning("Restricted section. Use only if you have administrator access.")

    with st.form("admin_login_form", clear_on_submit=False):
        username = st.text_input("Admin Username", placeholder="Enter admin username")
        password = st.text_input("Admin Password", type="password", placeholder="Enter admin password")
        submitted = st.form_submit_button("Login as Administrator", use_container_width=True)
       
        if submitted:
            if username and password:
                with st.spinner("Verifying credentials..."):
                    time.sleep(0.5)
                    role = validate_user(username, password)
               
                if role == "Admin":
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = role
                    st.success(f"Welcome, {username}!")
                    time.sleep(0.3)
                    go_to("Portal")
                elif role == "Customer":
                    st.error("Use the customer login for non-administrator accounts.")
                else:
                    st.error("Invalid administrator credentials.")
            else:
                st.warning("Please complete both fields before logging in.")

# Signup page
def signup_page():
    show_navigation_bar()
    show_back_button()
   
    st.title("Create Account")
    st.write("Create a customer account to place and manage orders.")

    col_left, col_right = st.columns([1.5, 1])
   
    with col_left:
        username = st.text_input("Choose Username", placeholder="3–20 characters, unique", key="su_username")
        email = st.text_input("Email Address", placeholder="your.email@example.com", key="su_email")
        phone = st.text_input("Phone Number", placeholder="+91 9876543210", key="su_phone")
        password = st.text_input("Create Password", type="password", placeholder="Enter a strong password", key="su_password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password", key="su_confirm_password")

        if password:
            has_lower = bool(re.search(r"[a-z]", password))
            has_upper = bool(re.search(r"[A-Z]", password))
            has_digit = bool(re.search(r"\d", password))
            has_special = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))
            has_length = len(password) >= 8
           
            strength_score = sum([has_lower, has_upper, has_digit, has_special, has_length])
           
            if strength_score <= 2:
                st.markdown("Password strength: Weak")
            elif strength_score <= 3:
                st.markdown("Password strength: Medium")
            else:
                st.markdown("Password strength: Strong")
           
            st.progress(strength_score / 5)

        if password and confirm_password:
            if password == confirm_password:
                st.success("Passwords match.")
            else:
                st.error("Passwords do not match.")

        st.info("This registration flow creates a customer account.")
   
    with col_right:
        st.markdown("### Password Requirements")
       
        if password:
            requirements = [
                ("At least 8 characters", len(password) >= 8),
                ("Lowercase letter (a–z)", bool(re.search(r"[a-z]", password))),
                ("Uppercase letter (A–Z)", bool(re.search(r"[A-Z]", password))),
                ("Number (0–9)", bool(re.search(r"\d", password))),
                ("Special character (!@#$...)", bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))),
            ]
           
            for req, met in requirements:
                if met:
                    st.markdown(f"- [x] {req}")
                else:
                    st.markdown(f"- [ ] {req}")
        else:
            st.markdown("- [ ] At least 8 characters")
            st.markdown("- [ ] Lowercase letter (a–z)")
            st.markdown("- [ ] Uppercase letter (A–Z)")
            st.markdown("- [ ] Number (0–9)")
            st.markdown("- [ ] Special character (!@#$...)")

        st.markdown("---")
        st.markdown("### Suggestions")
        st.write("- Combine letters, numbers, and symbols\n- Avoid dictionary words and simple patterns\n- Do not use personal information such as birthdays\n- Use a passphrase you can remember but others cannot guess")

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Create Account", use_container_width=True):
            u = st.session_state.get("su_username", "").strip()
            e = st.session_state.get("su_email", "").strip()
            ph = st.session_state.get("su_phone", "").strip()
            p = st.session_state.get("su_password", "")
            cp = st.session_state.get("su_confirm_password", "")

            if not u:
                st.error("Enter a username to continue.")
            elif len(u) < 3:
                st.error("Username must be at least 3 characters long.")
            elif not e:
                st.error("Enter an email address to continue.")
            elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', e):
                st.error("Please enter a valid email address.")
            elif ph and not re.match(r'^\+?1?\d{9,15}$', ph):
                st.error("Please enter a valid phone number (9-15 digits).")
            elif not p:
                st.error("Enter a password to continue.")
            elif not cp:
                st.error("Confirm your password to continue.")
            elif p != cp:
                st.error("Passwords do not match.")
            elif user_exists(u):
                st.error("Username already exists. Choose a different username.")
            else:
                has_lower = bool(re.search(r"[a-z]", p))
                has_upper = bool(re.search(r"[A-Z]", p))
                has_digit = bool(re.search(r"\d", p))
                has_special = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", p))
                has_length = len(p) >= 8
               
                if not has_length:
                    st.error("Password must be at least 8 characters long.")
                elif not has_lower:
                    st.error("Password must include at least one lowercase letter.")
                elif not has_upper:
                    st.error("Password must include at least one uppercase letter.")
                elif not has_digit:
                    st.error("Password must include at least one number.")
                elif not has_special:
                    st.error("Password must include at least one special character (!@#$%^&*...).")
                else:
                    role = "Customer"
                    with st.spinner("Creating your account..."):
                        time.sleep(0.5)
                        success, message = add_user(u, p, role, e, ph)
                   
                    if success:
                        st.success(f"Account created successfully. Welcome, {u}!")
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.session_state.role = role
                        st.session_state.favorites = []
                        time.sleep(0.5)
                        go_to("Portal")
                    else:
                        st.error(f"Account creation failed: {message}")

    st.markdown("---")
   
    col_link1, col_link2, col_link3 = st.columns([1, 2, 1])
    with col_link2:
        st.markdown("<p style='text-align: center;'>Already have an account?</p>", unsafe_allow_html=True)
        if st.button("Go to Login", use_container_width=True):
            go_to("CustomerLogin")

# Portal router
def portal_page():
    show_navigation_bar()
   
    with st.sidebar:
        st.markdown("### User")
        st.write(f"Name: {st.session_state.username}")
        st.write(f"Role: {st.session_state.role}")

    if st.session_state.role == "Customer":
        customer_portal()
    elif st.session_state.role == "Admin":
        admin_portal()

# Customer portal with database integration
def customer_portal():
    st.markdown(
        f"<div class='welcome-header'><h1>Customer Portal</h1><p>Welcome back, {st.session_state.username}.</p></div>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Browse Menu", "My Cart", "Order History", "Favorites", "Track Order"])

    # TAB 1: Browse Menu with Search
    with tab1:
        st.header("Menu")
       
        search_query = st.text_input("🔍 Search for items...", placeholder="Type item name (e.g., Chai, Samosa)")
       
        menu_df = get_menu_df()
       
        if not menu_df.empty:
            if search_query:
                filtered_menu = menu_df[menu_df["Items"].str.contains(search_query, case=False, na=False)]
                if filtered_menu.empty:
                    st.info(f"No items found for '{search_query}'. Try a different search term.")
            else:
                categories = ["All"] + list(menu_df["Category"].unique())
                selected_category = st.selectbox("Filter by Category", categories)
               
                if selected_category != "All":
                    filtered_menu = menu_df[menu_df["Category"] == selected_category]
                else:
                    filtered_menu = menu_df
           
            st.divider()

            if not filtered_menu.empty:
                for idx, row in filtered_menu.iterrows():
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
                       
                        with col1:
                            col_name, col_fav = st.columns([5, 1])
                            with col_name:
                                st.markdown(
                                    f"<div style='display:flex;flex-direction:column;'>"
                                    f"<span style='font-weight:600;'>{row['Items']}</span>"
                                    f"<span style='font-size:0.85rem;color:#9E9E9E;'>{row['Category']}</span>"
                                    f"</div>",
                                    unsafe_allow_html=True,
                                )
                            with col_fav:
                                is_favorite = row['Items'] in st.session_state.favorites
                                if st.button("❤️" if is_favorite else "🤍", key=f"fav_{idx}"):
                                    try:
                                        if is_favorite:
                                            remove_favorite(st.session_state.username, row['Items'])
                                            st.session_state.favorites.remove(row['Items'])
                                        else:
                                            add_favorite(st.session_state.username, row['Items'])
                                            st.session_state.favorites.append(row['Items'])
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error updating favorites: {e}")
                       
                        with col2:
                            st.markdown(f"<span class='price-badge'>₹{row['Price (₹)']}</span>", unsafe_allow_html=True)
                       
                        with col3:
                            stock_text = f"Stock: {row['Stock']}"
                            if row['Stock'] < 10:
                                st.markdown(f"<span style='color:orange;font-size:0.85rem;'>⚠️ {stock_text}</span>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<span style='color:#9E9E9E;font-size:0.85rem;'>✓ {stock_text}</span>", unsafe_allow_html=True)
                       
                        with col4:
                            quantity = st.number_input(
                                "Qty",
                                min_value=0,
                                max_value=row["Stock"],
                                key=f"qty_{idx}",
                                value=0,
                                label_visibility="visible",
                                help="Select quantity to add to cart",
                            )
                           
                            if quantity > 0:
                                existing_item_index = None
                                for i, cart_item in enumerate(st.session_state.cart):
                                    if cart_item["name"] == row["Items"]:
                                        existing_item_index = i
                                        break
                               
                                if existing_item_index is not None:
                                    old_total = st.session_state.cart[existing_item_index]["total"]
                                    st.session_state.cart_total -= old_total
                                    st.session_state.cart[existing_item_index]["quantity"] = quantity
                                    st.session_state.cart[existing_item_index]["total"] = row["Price (₹)"] * quantity
                                    st.session_state.cart_total += st.session_state.cart[existing_item_index]["total"]
                                else:
                                    item = {
                                        "name": row["Items"],
                                        "price": row["Price (₹)"],
                                        "quantity": quantity,
                                        "total": row["Price (₹)"] * quantity,
                                    }
                                    st.session_state.cart.append(item)
                                    st.session_state.cart_total += item["total"]
                           
                            elif quantity == 0:
                                for i, cart_item in enumerate(st.session_state.cart):
                                    if cart_item["name"] == row["Items"]:
                                        st.session_state.cart_total -= cart_item["total"]
                                        st.session_state.cart.pop(i)
                                        break
        else:
            st.warning("No menu items available.")

    # TAB 2: Cart with Stock Validation
    with tab2:
        st.header("Shopping Cart")
       
        if st.session_state.cart:
            for i, item in enumerate(st.session_state.cart):
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
               
                with col1:
                    st.write(item["name"])
                with col2:
                    st.write(f"₹{item['price']}")
                with col3:
                    st.write(f"Qty: {item['quantity']}")
                with col4:
                    st.write(f"₹{item['total']}")
                with col5:
                    if st.button("Remove", key=f"remove_{i}"):
                        st.session_state.cart_total -= item["total"]
                        st.session_state.cart.pop(i)
                        st.rerun()

            st.divider()
           
            st.subheader("Have a promo code?")
            discount_code = st.text_input("Enter discount code", placeholder="e.g., WELCOME10")
           
            discount_percentage = 0
            if discount_code:
                code_upper = discount_code.upper()
                if code_upper in DISCOUNT_CODES:
                    discount_percentage = DISCOUNT_CODES[code_upper]
                    st.success(f"🎉 {discount_percentage}% discount applied!")
                else:
                    st.error("Invalid discount code. Try: WELCOME10, STUDENT20, FREESHIP, SAVE15")
           
            subtotal = st.session_state.cart_total
            discount_amount = subtotal * (discount_percentage / 100)
            final_total = subtotal - discount_amount
           
            if discount_percentage > 0:
                st.write(f"**Subtotal:** ₹{subtotal}")
                st.write(f"**Discount ({discount_percentage}%):** -₹{discount_amount:.2f}")
                st.markdown(f"### Total: {format_currency(final_total)}")
            else:
                st.markdown(f"### Total: {format_currency(subtotal)}")

            st.subheader("Checkout")
            payment_method = st.selectbox("Select Payment Method", ["UPI", "Card", "Cash"], key="checkout_method")

            if st.button("Proceed to Payment", use_container_width=True):
                # Validate stock for all items
                stock_valid = True
                error_messages = []
               
                with st.spinner("Validating stock availability..."):
                    for item in st.session_state.cart:
                        success, message = check_stock_availability(item['name'], item['quantity'])
                        if not success:
                            stock_valid = False
                            error_messages.append(message)
               
                if not stock_valid:
                    st.error("Stock validation failed:")
                    for msg in error_messages:
                        st.error(f"• {msg}")
                    st.info("Please update your cart and try again.")
                else:
                    # All validation passed, proceed to payment
                    st.session_state.final_payment_amount = final_total
                    st.session_state.discount_applied = discount_percentage
                    st.session_state.payment_mode = payment_method
                    st.session_state.payment_reference = generate_order_reference()
                   
                    if payment_method == "Card":
                        go_to("CardDetails")
                    else:
                        go_to("Payment")
        else:
            st.info("Your cart is currently empty. Add items from the menu.")

    # TAB 3: Order History from Database
    with tab3:
        st.header("Order History")
       
        try:
            with st.spinner("Loading your orders..."):
                orders = get_user_orders(st.session_state.username)
           
            if orders:
                for order in orders:
                    order_ref = order['order_reference']
                    status = order.get('status', 'Completed')
                   
                    status_colors = {
                        "Preparing": "#FFA500",
                        "Ready": "#06C167",
                        "Completed": "#9E9E9E",
                        "Pending": "#FFD700",
                        "Cancelled": "#FF4444"
                    }
                    status_color = status_colors.get(status, "#9E9E9E")
                   
                    with st.container():
                        st.markdown(
                            f"""
<div style="background:#111111;border-radius:14px;padding:1.2rem;margin-bottom:1rem;border:1px solid #2A2A2A;">
<h4 style="margin:0 0 0.5rem 0;">Order #{order_ref}
<span style="color:{status_color};font-size:0.9rem;">● {status}</span></h4>
<p style="margin:0.3rem 0;color:#9E9E9E;">Date: {order['created_at']}</p>
<p style="margin:0.3rem 0;color:#9E9E9E;">Payment: {order['payment_mode']}</p>
<p style="margin:0.3rem 0;"><strong>Total: ₹{order['total_amount']:.2f}</strong></p>
<hr style="border-top:1px solid #2A2A2A;margin:0.6rem 0;">
<p style="margin:0.3rem 0;font-weight:500;">Items:</p>
""",
                            unsafe_allow_html=True,
                        )
                        for item in order["items"]:
                            st.markdown(f"- {item['item_name']} x{item['quantity']} (₹{item['total']:.2f})")
                       
                        # Check if order has been rated
                        try:
                            rating_data = get_order_rating(order_ref)
                            if rating_data:
                                stars = "⭐" * rating_data['rating']
                                st.markdown(f"<p style='color:#06C167;'>Your rating: {stars}</p>", unsafe_allow_html=True)
                                if rating_data.get('feedback'):
                                    st.markdown(f"<p style='color:#9E9E9E;font-size:0.85rem;'>Your feedback: {rating_data['feedback']}</p>", unsafe_allow_html=True)
                            else:
                                # Show rating form
                                if st.button(f"⭐ Rate this order", key=f"rate_btn_{order_ref}"):
                                    with st.form(f"rating_{order_ref}"):
                                        st.write("How was your experience?")
                                        rating = st.slider("Rating", 1, 5, 5, key=f"rating_slider_{order_ref}")
                                        feedback = st.text_area("Feedback (optional)", key=f"feedback_{order_ref}")
                                       
                                        if st.form_submit_button("Submit Rating"):
                                            try:
                                                if add_order_rating(order_ref, rating, feedback):
                                                    st.success("Thank you for your feedback! 🙏")
                                                    time.sleep(0.5)
                                                    st.rerun()
                                                else:
                                                    st.error("Failed to save rating. Please try again.")
                                            except Exception as e:
                                                st.error(f"Error saving rating: {e}")
                        except Exception as e:
                            pass
                       
                        st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No orders recorded yet. Place an order to see history here.")
        except Exception as e:
            st.error(f"Error loading order history: {e}")

    # TAB 4: Favorites
    with tab4:
        st.header("Your Favorites ❤️")
       
        if st.session_state.favorites:
            st.write(f"You have {len(st.session_state.favorites)} favorite items")
           
            menu_df = get_menu_df()
            if not menu_df.empty:
                fav_items = menu_df[menu_df["Items"].isin(st.session_state.favorites)]
               
                for idx, row in fav_items.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                   
                    with col1:
                        st.markdown(f"**{row['Items']}** - {row['Category']}")
                    with col2:
                        st.markdown(f"<span class='price-badge'>₹{row['Price (₹)']}</span>", unsafe_allow_html=True)
                    with col3:
                        if st.button("Remove ❌", key=f"remove_fav_{idx}"):
                            try:
                                remove_favorite(st.session_state.username, row['Items'])
                                st.session_state.favorites.remove(row['Items'])
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error removing favorite: {e}")
        else:
            st.info("You haven't added any favorites yet. Click the ❤️ icon on menu items to add them here!")

    # TAB 5: Track Order
    with tab5:
        st.header("Track Your Order")
       
        order_ref_input = st.text_input("Enter Order Reference", placeholder="e.g., ORD-20241215...")
       
        if st.button("Search Order"):
            if order_ref_input:
                try:
                    with st.spinner("Searching for order..."):
                        order = get_order_by_reference(order_ref_input)
                   
                    if order:
                        st.success(f"Order found: {order_ref_input}")
                       
                        status = order.get('status', 'Completed')
                        status_colors = {
                            "Preparing": "#FFA500",
                            "Ready": "#06C167",
                            "Completed": "#9E9E9E",
                            "Pending": "#FFD700",
                            "Cancelled": "#FF4444"
                        }
                        status_color = status_colors.get(status, "#9E9E9E")
                       
                        st.markdown(
                            f"""
<div style="background:#111111;border-radius:14px;padding:1.5rem;border:1px solid #2A2A2A;">
<h3>Order #{order['order_reference']}</h3>
<p style="font-size:1.2rem;"><span style="color:{status_color};">● {status}</span></p>
<hr style="border-top:1px solid #2A2A2A;margin:1rem 0;">
<p><strong>Date:</strong> {order['created_at']}</p>
<p><strong>Payment:</strong> {order['payment_mode']}</p>
<p><strong>Total:</strong> ₹{order['total_amount']:.2f}</p>
<hr style="border-top:1px solid #2A2A2A;margin:1rem 0;">
<h4>Items:</h4>
</div>
""",
                            unsafe_allow_html=True,
                        )
                       
                        for item in order['items']:
                            st.markdown(f"- **{item['item_name']}** x{item['quantity']} - ₹{item['total']:.2f}")
                    else:
                        st.error(f"Order not found: {order_ref_input}")
                        st.info("Please check your order reference and try again.")
                except Exception as e:
                    st.error(f"Error searching for order: {e}")
            else:
                st.warning("Please enter an order reference.")

# Admin portal with database integration
def admin_portal():
    st.markdown(
        f"<div class='welcome-header'><h1>Admin Control Panel</h1><p>Administrator: {st.session_state.username}</p></div>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Menu Management", "Inventory", "Sales Report"])

    # TAB 1: Dashboard with Real Statistics
    with tab1:
        st.header("Dashboard Overview")
       
        try:
            with st.spinner("Loading dashboard statistics..."):
                stats = get_dashboard_stats()
           
            if stats:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Today's Orders", stats['today_orders'])
                with col2:
                    st.metric("Today's Revenue", f"₹{stats['today_revenue']:.2f}")
                with col3:
                    st.metric("Menu Items", stats['menu_items'])
                with col4:
                    st.metric("Low Stock Items", stats['low_stock_items'])
               
                col5, col6 = st.columns(2)
                with col5:
                    st.metric("Total Customers", stats['total_customers'])
                with col6:
                    st.metric("Total Orders", stats['total_orders'])
            else:
                st.error("Failed to load dashboard statistics.")
        except Exception as e:
            st.error(f"Error loading statistics: {e}")
       
        st.divider()
       
        # Recent Orders
        st.subheader("Recent Orders")
        try:
            with st.spinner("Loading recent orders..."):
                recent_orders = get_all_orders(limit=10)
           
            if recent_orders:
                orders_data = {
                    "Order ID": [order['order_reference'] for order in recent_orders],
                    "Customer": [order['username'] for order in recent_orders],
                    "Items": [f"{len(order['items'])} items" for order in recent_orders],
                    "Total (₹)": [order['total_amount'] for order in recent_orders],
                    "Status": [order['status'] for order in recent_orders],
                    "Date": [str(order['created_at']) for order in recent_orders],
                }
                orders_df = pd.DataFrame(orders_data)
                st.dataframe(orders_df, use_container_width=True)
            else:
                st.info("No orders found.")
        except Exception as e:
            st.error(f"Error loading recent orders: {e}")
       
        st.divider()
       
        # Low Stock Alerts
        st.subheader("⚠️ Low Stock Alerts")
        try:
            with st.spinner("Checking inventory..."):
                low_stock = get_low_stock_items(threshold=10)
           
            if low_stock:
                for item in low_stock:
                    stock_level = item['stock']
                    if stock_level <= 5:
                        color = "red"
                        icon = "🔴"
                    else:
                        color = "orange"
                        icon = "🟠"
                   
                    st.markdown(
                        f"{icon} **{item['item_name']}** ({item['category']}) - "
                        f"<span style='color:{color};font-weight:bold;'>Stock: {stock_level}</span>",
                        unsafe_allow_html=True
                    )
            else:
                st.success("✅ All items are well stocked!")
        except Exception as e:
            st.error(f"Error loading low stock items: {e}")

    # TAB 2: Menu Management with Database Operations
    with tab2:
        st.header("Menu Management")
       
        try:
            with st.spinner("Loading menu..."):
                menu_items = get_menu(available_only=False)
           
            if menu_items:
                st.subheader("Current Menu Items")
               
                for item in menu_items:
                    with st.expander(f"📋 {item['item_name']} - {item['category']}"):
                        col1, col2, col3 = st.columns(3)
                       
                        with col1:
                            new_price = st.number_input(
                                "Price (₹)",
                                value=float(item['price']),
                                min_value=0.0,
                                step=1.0,
                                key=f"price_{item['id']}"
                            )
                       
                        with col2:
                            new_stock = st.number_input(
                                "Stock",
                                value=item['stock'],
                                min_value=0,
                                step=1,
                                key=f"stock_{item['id']}"
                            )
                       
                        with col3:
                            is_available = st.checkbox(
                                "Available",
                                value=bool(item['is_available']),
                                key=f"avail_{item['id']}"
                            )
                       
                        new_desc = st.text_input(
                            "Description",
                            value=item.get('description', ''),
                            key=f"desc_{item['id']}"
                        )
                       
                        col_btn1, col_btn2 = st.columns(2)
                       
                        with col_btn1:
                            if st.button("💾 Update", key=f"update_{item['id']}", use_container_width=True):
                                try:
                                    success, message = update_menu_item(
                                        item['id'],
                                        item['item_name'],
                                        item['category'],
                                        new_price,
                                        new_stock,
                                        is_available,
                                        new_desc
                                    )
                                    if success:
                                        st.success(message)
                                        st.toast("Menu item updated!")
                                        time.sleep(0.5)
                                        st.rerun()
                                    else:
                                        st.error(message)
                                except Exception as e:
                                    st.error(f"Error updating item: {e}")
                       
                        with col_btn2:
                            if st.button("🗑️ Delete", key=f"delete_{item['id']}", use_container_width=True):
                                try:
                                    success, message = delete_menu_item(item['id'])
                                    if success:
                                        st.success(message)
                                        st.toast("Menu item deleted!")
                                        time.sleep(0.5)
                                        st.rerun()
                                    else:
                                        st.error(message)
                                except Exception as e:
                                    st.error(f"Error deleting item: {e}")
            else:
                st.info("No menu items found.")
        except Exception as e:
            st.error(f"Error loading menu: {e}")
       
        st.divider()
       
        # Add New Item Form
        st.subheader("➕ Add New Menu Item")
        with st.form("add_menu_item_form"):
            col1, col2 = st.columns(2)
           
            with col1:
                new_item_name = st.text_input("Item Name")
                new_category = st.selectbox("Category", ["Food", "Dessert", "Snack", "Beverage"])
                new_price = st.number_input("Price (₹)", min_value=0.0, step=1.0)
           
            with col2:
                new_stock = st.number_input("Initial Stock", min_value=0, step=1)
                new_description = st.text_area("Description (optional)")
           
            submitted = st.form_submit_button("Add Item", use_container_width=True)
           
            if submitted:
                if new_item_name and new_price > 0:
                    try:
                        success, message = add_menu_item(
                            new_item_name,
                            new_category,
                            new_price,
                            new_stock,
                            new_description if new_description else None
                        )
                        if success:
                            st.success(message)
                            st.toast(f"{new_item_name} added to menu!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"Error adding item: {e}")
                else:
                    st.warning("Please provide item name and valid price.")

    # TAB 3: Inventory with Database Data
    with tab3:
        st.header("Inventory Management")
       
        try:
            with st.spinner("Loading inventory data..."):
                low_stock = get_low_stock_items(threshold=10)
           
            st.subheader("Low Stock Items (Stock ≤ 10)")
           
            if low_stock:
                inventory_data = {
                    "Item": [item['item_name'] for item in low_stock],
                    "Category": [item['category'] for item in low_stock],
                    "Current Stock": [item['stock'] for item in low_stock],
                    "Price (₹)": [float(item['price']) for item in low_stock],
                    "Status": ["🔴 Critical" if item['stock'] <= 5 else "🟠 Low" for item in low_stock]
                }
                inventory_df = pd.DataFrame(inventory_data)
                st.dataframe(inventory_df, use_container_width=True)
               
                st.warning(f"⚠️ {len(low_stock)} items need restocking!")
            else:
                st.success("✅ All items are well stocked!")
           
            st.divider()
           
            # Full Inventory
            st.subheader("Full Inventory")
            menu_items = get_menu(available_only=False)
           
            if menu_items:
                full_inventory = {
                    "Item": [item['item_name'] for item in menu_items],
                    "Category": [item['category'] for item in menu_items],
                    "Stock": [item['stock'] for item in menu_items],
                    "Price (₹)": [float(item['price']) for item in menu_items],
                    "Available": ["✅" if item['is_available'] else "❌" for item in menu_items]
                }
                full_df = pd.DataFrame(full_inventory)
                st.dataframe(full_df, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading inventory: {e}")

    # TAB 4: Sales Report
    with tab4:
        st.header("Sales Report")
       
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")
       
        if st.button("Generate Report"):
            try:
                from database import get_sales_data
               
                with st.spinner("Generating sales report..."):
                    sales_data = get_sales_data(start_date, end_date)
               
                if sales_data:
                    st.subheader("Sales Summary")
                    sales_df = pd.DataFrame(sales_data)
                    st.dataframe(sales_df, use_container_width=True)
                   
                    # Export button
                    csv = sales_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"sales_report_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                   
                    # Show total revenue
                    total_revenue = sales_df['revenue'].sum()
                    total_orders = sales_df['orders'].sum()
                    st.metric("Total Revenue", f"₹{total_revenue:,.2f}")
                    st.metric("Total Orders", total_orders)
                else:
                    st.info("No sales data found for the selected period.")
            except Exception as e:
                st.error(f"Error generating report: {e}")

# Card payment page
def card_details_page():
    show_navigation_bar()
    show_back_button()
   
    mode = st.session_state.get("payment_mode")
    ref = st.session_state.get("payment_reference")
   
    if mode != "Card" or not ref:
        st.warning("No active card payment session. Start from checkout.")
        return

    st.markdown("<h1 style='text-align:center;'>Card Payment</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;'>Order reference: <strong>{ref}</strong></p>", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([2, 1])
   
    with col1:
        st.subheader("Enter Card Details")

        with st.form("card_form"):
            card_number = st.text_input("Card Number", placeholder="XXXX XXXX XXXX XXXX")
            name_on_card = st.text_input("Name on Card", placeholder="As printed on card")
           
            cols_e, cols_c = st.columns(2)
            with cols_e:
                expiry = st.text_input("Expiry (MM/YY)", placeholder="MM/YY")
            with cols_c:
                cvv = st.text_input("CVV", type="password", placeholder="3 or 4 digits")
           
            submitted = st.form_submit_button("Pay Securely", use_container_width=True)
           
            if submitted:
                card_number = card_number.replace(" ", "")
                name_on_card = name_on_card.strip()
                expiry = expiry.strip()
                cvv = cvv.strip()

                if not (card_number and name_on_card and expiry and cvv):
                    st.warning("Please fill in all card fields.")
                elif len(card_number) < 12 or len(card_number) > 19 or not card_number.isdigit():
                    st.error("Enter a valid card number.")
                elif len(cvv) not in (3, 4) or not cvv.isdigit():
                    st.error("Enter a valid CVV.")
                else:
                    with st.spinner("Processing payment..."):
                        time.sleep(1)
                   
                    st.session_state.pending_payment_data = {
                        "mode": "Card",
                        "reference": st.session_state.payment_reference,
                    }
                    go_to("PaymentSuccess")

    with col2:
        st.subheader("Charge Summary")
        amount = st.session_state.get("final_payment_amount", st.session_state.cart_total)
        st.write(f"Total amount: {format_currency(amount)}")
        st.write("Payments are simulated in this demo environment.")

# Payment page (UPI/Cash)
def payment_page():
    show_navigation_bar()
    show_back_button()
   
    mode = st.session_state.get("payment_mode")
    ref = st.session_state.get("payment_reference")
   
    if not mode or not ref:
        st.warning("No active payment session. Please add items to your cart and proceed to checkout.")
        return

    st.markdown("<h1 style='text-align:center;'>Payment</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;'>Order reference: <strong>{ref}</strong></p>", unsafe_allow_html=True)
    st.markdown("---")

    if mode == "UPI":
        st.subheader("UPI Demo Payment")
        col1, col2 = st.columns(2)
       
        with col1:
            st.write("Scan the QR code using any UPI application to simulate payment. This is a demo screen; no real transaction takes place.")
            st.write("After scanning, click Confirm Payment to complete the order.")
       
        with col2:
            st.markdown("""
<div style="border-radius:16px;padding:1.5rem;background:linear-gradient(145deg,#050505,#111111);
border:1px solid rgba(6,193,103,0.5);text-align:center;">
  <div style="width:180px;height:180px;margin:0 auto;
  background:repeating-linear-gradient(45deg,#06C167,#06C167 10px,#151515 10px,#151515 20px);
  border-radius:12px;"></div>
  <p style="margin-top:1rem;color:#9E9E9E;font-size:0.9rem;">Demo QR Code (random pattern)</p>
</div>
""", unsafe_allow_html=True)
       
        if st.button("Confirm Payment", use_container_width=True):
            with st.spinner("Processing payment..."):
                time.sleep(1)
           
            st.session_state.pending_payment_data = {
                "mode": "UPI",
                "reference": ref,
            }
            go_to("PaymentSuccess")

    elif mode == "Cash":
        st.subheader("Cash Payment")
        col1, col2 = st.columns([2, 1])
       
        with col1:
            st.write("Please pay the total amount in cash at the counter. Present the coupon shown on the right to the cashier.")
       
        with col2:
            amount = st.session_state.get("final_payment_amount", st.session_state.cart_total)
            st.markdown(f"""
<div style="border-radius:16px;padding:1.2rem 1.4rem;background:linear-gradient(145deg,#262626,#1b1b1b);
border:1px dashed #F5A623;color:#FFFFFF;">
  <p style="font-size:0.9rem;margin:0 0 0.4rem 0;">Cash Coupon</p>
  <p style="font-size:1.1rem;font-weight:600;margin:0 0 0.4rem 0;">Amount: ₹{amount:.2f}</p>
  <p style="font-size:0.9rem;margin:0 0 0.4rem 0;">Reference: {ref}</p>
  <p style="font-size:0.8rem;color:#BBBBBB;margin:0;">Show this coupon at the counter and pay in cash.</p>
</div>
""", unsafe_allow_html=True)
       
        if st.button("Mark as Paid (Cash)", use_container_width=True):
            st.session_state.pending_payment_data = {
                "mode": "Cash",
                "reference": ref,
            }
            go_to("PaymentSuccess")
   
    else:
        st.info("Card payments are handled on the Card Payment screen.")

# Payment success with database save
def payment_success_page():
    show_navigation_bar()
    show_back_button("← Back to Portal")

    data = st.session_state.get("pending_payment_data") or {}
    mode = data.get("mode")
    ref = data.get("reference")

    if not mode or not ref:
        st.warning("No recent payment found.")
        if st.button("Go to Portal"):
            go_to("Portal")
        return

    # Show celebration
    st.balloons()
    st.toast("Processing your order...", icon="⏳")
   
    # Save order to database
    try:
        with st.spinner("Saving your order..."):
            amount = st.session_state.get("final_payment_amount", st.session_state.cart_total)
           
            success, message, order_ref = create_order(
                st.session_state.username,
                st.session_state.cart,
                mode
            )
       
        if success:
            st.toast("Order placed successfully! 🎉", icon="✅")
           
            st.markdown("<h1 style='text-align:center;'>Payment Successful</h1>", unsafe_allow_html=True)
            st.markdown("---")

            ticket_col, info_col = st.columns([2, 1])
           
            with ticket_col:
                st.markdown(f"""
<div style="border-radius:18px;padding:1.5rem 1.7rem;background:linear-gradient(145deg,#111111,#000000);
border:1px solid rgba(255,255,255,0.1);color:#FFFFFF;">
  <h3 style="margin-top:0;">Your Meal Ticket</h3>
  <p style="margin:0.4rem 0;">Reference: <strong>{order_ref}</strong></p>
  <p style="margin:0.4rem 0;">Payment Mode: <strong>{mode}</strong></p>
  <p style="margin:0.4rem 0;">Amount Paid: <strong>₹{amount:.2f}</strong></p>
  <hr style="border-top:1px dashed #333333;margin:0.9rem 0;">
  <p style="margin:0.3rem 0;">Thank you for making the payment.</p>
  <p style="margin:0.3rem 0;">Enjoy your meal!</p>
</div>
""", unsafe_allow_html=True)
           
            with info_col:
                st.subheader("Next Steps")
                st.write("Your order is now registered with the cafeteria team. Please keep this ticket handy until you receive your meal.")
               
                if st.button("Go to Customer Portal", use_container_width=True):
                    # Clear cart and payment data
                    st.session_state.cart = []
                    st.session_state.cart_total = 0
                    st.session_state.payment_mode = None
                    st.session_state.payment_reference = None
                    st.session_state.pending_payment_data = {}
                    st.session_state.final_payment_amount = None
                    st.session_state.discount_applied = 0
                   
                    go_to("Portal")
        else:
            st.error(f"❌ Order creation failed: {message}")
            st.warning("Your payment was processed but order could not be saved. Please contact support with this reference: " + ref)
           
            if st.button("Retry"):
                st.rerun()
           
            if st.button("Go to Portal"):
                go_to("Portal")
               
    except Exception as e:
        st.error(f"❌ Error processing order: {e}")
        st.warning("An unexpected error occurred. Please contact support.")
       
        if st.button("Go to Portal"):
            go_to("Portal")

# Main router
def main():
    page = st.session_state.current_page

    if not st.session_state.logged_in:
        if page == "Home":
            home_page()
        elif page == "About":
            about_page()
        elif page == "Contact":
            contact_page()
        elif page == "CustomerLogin":
            customer_login_page()
        elif page == "AdminLogin":
            admin_login_page()
        elif page == "SignUp":
            signup_page()
        elif page == "GuestPreview":
            guest_preview()
        elif page == "Payment":
            payment_page()
        elif page == "CardDetails":
            card_details_page()
        elif page == "PaymentSuccess":
            payment_success_page()
        else:
            home_page()
    else:
        if page in ["About", "Contact"]:
            if page == "About":
                about_page()
            else:
                contact_page()
        elif page == "Payment":
            payment_page()
        elif page == "CardDetails":
            card_details_page()
        elif page == "PaymentSuccess":
            payment_success_page()
        else:
            portal_page()

if __name__ == "__main__":
    main()