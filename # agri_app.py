# agri_app.py
import streamlit as st
import sqlite3
from PIL import Image
import io
import time
import smtplib
from email.mime.text import MIMEText

# --- Email Setup ---
MANUFACTURER_EMAIL = "jaydishkennedy@gamil.com"
SENDER_EMAIL = "kennedyjaydish@gmail.com"
SENDER_PASSWORD = "Jayd1234"  # Use App Password, NOT Gmail password

def send_order_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Email error:", e)
        return False

# --- DB Functions ---
def create_tables():
    conn = sqlite3.connect("agri_products.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, image BLOB)''')
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect("agri_products.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect("agri_products.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

def get_products():
    conn = sqlite3.connect("agri_products.db")
    c = conn.cursor()
    c.execute("SELECT id, name, price, image FROM products")
    products = c.fetchall()
    conn.close()
    return products

def delete_product(product_id):
    conn = sqlite3.connect("agri_products.db")
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()

# --- Streamlit App ---
create_tables()

st.set_page_config(page_title="Agri Product Sale App")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.cart = []

if not st.session_state.logged_in:
    st.title("\U0001F33E Agri Product Sale Portal")
    st.markdown("> _\"Farming is not just a job, it's a way of life that feeds the world.\"_")
    st.markdown("> _\"Support agriculture – the backbone of every nation.\"_")
    st.markdown("> _\"Buy local, support a farmer, strengthen a community.\"_")

    choice = st.radio("Login or Signup", ["Login", "Signup"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if choice == "Signup":
        if st.button("Signup"):
            if add_user(username, password):
                st.success("Signup successful. Please login.")
            else:
                st.error("Username already exists.")
    else:
        if st.button("Login"):
            if authenticate_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful. Redirecting...")
                time.sleep(1.5)
                st.rerun()
            else:
                st.error("Invalid credentials")
else:
    st.sidebar.success(f"Logged in as: {st.session_state.username}")
    if st.session_state.username == "admin":
        nav = st.sidebar.radio("Navigation", ["\U0001F6D2 View Products", "\U0001F9FA View Cart", "➕ Admin: Add Product"])
    else:
        nav = st.sidebar.radio("Navigation", ["\U0001F6D2 View Products", "\U0001F9FA View Cart"])

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.cart = []
        time.sleep(0.5)
        st.rerun()

    if nav == "\U0001F6D2 View Products":
        st.header("\U0001F6D2 Available Agri Products")
        products = get_products()
        if products:
            for pid, name, price, img in products:
                cols = st.columns([1, 2, 1])
                with cols[0]:
                    if img:
                        st.image(io.BytesIO(img), width=150)
                with cols[1]:
                    st.markdown(f"**Name:** {name}")
                    st.markdown(f"**Price:** ₹{price}")
                    if st.button(f"Add to Cart: {name}", key=f"cart_{pid}"):
                        st.session_state.cart.append((name, price))
                        st.success(f"{name} added to cart")
                with cols[2]:
                    if st.session_state.username == "admin":
                        if st.button("❌ Remove", key=f"remove_{pid}"):
                            delete_product(pid)
                            st.success(f"Removed {name}")
                            time.sleep(1)
                            st.rerun()
        else:
            st.info("No products available.")

    elif nav == "\U0001F9FA View Cart":
        st.header("\U0001F9FA Your Cart")
        total = 0
        if st.session_state.cart:
            for name, price in st.session_state.cart:
                st.markdown(f"✅ {name} - ₹{price}")
                total += price
            st.markdown(f"**Total: ₹{total}**")

            payment_option = st.radio("Choose Payment Method:", ["Online (GPay)", "Cash on Delivery"])

            full_name = st.text_input("Full Name")
            address = st.text_area("Delivery Address")
            contact = st.text_input("Contact Number")

            order_details = f"Name: {full_name}\nAddress: {address}\nContact: {contact}\n"

            if payment_option == "Online (GPay)":
                st.markdown("📱 Send payment to GPay Number: **9876543210**")
                txn_id = st.text_input("Enter GPay Transaction ID")
                order_details += f"Payment: GPay\nTransaction ID: {txn_id}\n"
            else:
                order_details += f"Payment: Cash on Delivery\n"

            if st.button("Confirm Order"):
                cart_text = "\n".join([f"- {n}: ₹{p}" for n, p in st.session_state.cart])
                body = f"\U0001F6D2 New Order by {st.session_state.username}:\n\n{cart_text}\n\nTotal: ₹{total}\n\n{order_details}"
                if send_order_email(MANUFACTURER_EMAIL, "New Agri Product Order", body):
                    st.success("✅ Order placed! Manufacturer will contact you soon.")
                else:
                    st.warning("⚠️ Order placed but email failed to send.")
                st.session_state.cart = []
        else:
            st.info("Your cart is empty.")

    elif nav == "➕ Admin: Add Product":
        st.header("➕ Add New Product")
        product_name = st.text_input("Product Name")
        product_price = st.number_input("Product Price (₹)", min_value=1.0)
        product_image = st.file_uploader("Upload Product Image", type=["jpg", "png", "jpeg"])

        if st.button("Add Product"):
            if product_name and product_price and product_image:
                img_data = product_image.read()
                conn = sqlite3.connect("agri_products.db")
                c = conn.cursor()
                c.execute("INSERT INTO products (name, price, image) VALUES (?, ?, ?)",
                          (product_name, product_price, img_data))
                conn.commit()
                conn.close()
                st.success(f"{product_name} added successfully!")
            else:
                st.warning("Please provide all details.")
