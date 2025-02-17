# 📌 Import required libraries
import streamlit as st
import pandas as pd
import os
import yaml
import bcrypt

# Hide Streamlit's extra UI elements
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)
# -------------------------------------------
# 📌 Load or Create Authentication Config
# -------------------------------------------

CONFIG_FILE = "config.yaml"

# 🔹 Function to load authentication config, create default if missing
def load_config():
    try:
        if not os.path.exists(CONFIG_FILE):
            default_config = {
                "users": {
                    "admin": {
                        "name": "Admin",
                        "email": "admin@example.com",
                        "password": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
                    }
                }
            }
            with open(CONFIG_FILE, "w") as file:
                yaml.dump(default_config, file)
        with open(CONFIG_FILE, "r") as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as e:
        st.error(f"Error loading configuration file: {e}")
        return {}

# 🔹 Function to save updated config
def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        yaml.dump(config, file)

# Load the config file
config = load_config()

# -------------------------------------------
# 📌 Authentication System
# -------------------------------------------

def authenticate_user(username, password):
    """Check if username and password are correct."""
    user_data = config["users"].get(username)
    if user_data and bcrypt.checkpw(password.encode(), user_data["password"].encode()):
        return user_data["name"]
    return None

def register_user(name, email, username, password):
    """Register a new user."""
    if username in config["users"]:
        return False, "Username already exists!"
    
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    config["users"][username] = {"name": name, "email": email, "password": hashed_password}
    save_config(config)
    return True, "User registered successfully! Please log in."

# -------------------------------------------
# 📌 Authentication UI (Login & Sign-Up)
# -------------------------------------------

tab1, tab2 = st.tabs(["🔑 Login", "🆕 Sign Up"])

# --------- LOGIN ---------
with tab1:
    st.header("🔑 Login")

    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", key="login_button"):
        user_name = authenticate_user(username, password)
        if user_name:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["name"] = user_name
            st.success(f"✅ Welcome, {user_name}!")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid username or password!")

# --------- SIGN-UP ---------
with tab2:
    st.header("🆕 Sign Up")
    new_name = st.text_input("Full Name", key="signup_name")
    new_email = st.text_input("Email", key="signup_email")
    new_username = st.text_input("Choose a Username", key="signup_username")
    new_password = st.text_input("Password", type="password", key="signup_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")

    if st.button("🔑 Register", key="signup_button"):
        if new_password != confirm_password:
            st.error("⚠ Passwords do not match!")
        else:
            success, msg = register_user(new_name, new_email, new_username, new_password)
            if success:
                st.success(msg)
            else:
                st.error(msg)


# -------------------------------------------
# 📌 Expense Splitter App UI (Protected Area)
# -------------------------------------------
if st.session_state.get("authenticated", False):
    st.sidebar.title(f"Welcome, {st.session_state['name']}")  # Sidebar welcome message
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

    # 🔹 Private file for each user
    file_name = f"expenses_{st.session_state['username']}.csv"

    # 🔹 Function to load expenses
    def load_expenses():
        if os.path.exists(file_name):
            try:
                df = pd.read_csv(file_name)
                return dict(zip(df["Participant"], df["Amount"]))
            except Exception as e:
                st.error(f"Error loading expenses: {e}")
                return {}
        return {}

    # 🔹 Function to save expenses
    def save_expenses(expenses):
        df = pd.DataFrame(expenses.items(), columns=["Participant", "Amount"])
        df.to_csv(file_name, index=False)

    # 🔹 Function to reset expenses
    def reset_expenses():
        if os.path.exists(file_name):
            os.remove(file_name)
        st.session_state["expenses"] = {}

    if "expenses" not in st.session_state:
        st.session_state["expenses"] = load_expenses()

    expenses = st.session_state["expenses"]

    # -------------------------------------------
    # 📌 Expense Splitter App UI
    # -------------------------------------------

    st.title("💰 Expense Splitter (Private Data)")

    # 🔹 App Navigation Tabs
    tab_home, tab_participants, tab_add_expense, tab_summary = st.tabs(
        ["🏠 Home", "👥 Participants", "💵 Add Expense", "📊 Summary"]
    )

    # ---- HOME TAB ----
    with tab_home:
        st.header("🏠 Welcome to Expense Splitter")
        st.write("Split expenses fairly with friends. Your data is private and secure.")
        st.image("https://i.pinimg.com/originals/55/de/06/55de068a005a71c0720cb64c3c6be828.gif", use_container_width=True)

    # ---- PARTICIPANTS TAB ----
    with tab_participants:
        st.header("👥 Manage Participants")
        new_participant = st.text_input("Enter participant name")

        col1, col2 = st.columns(2)

        if col1.button("➕ Add"):
            if new_participant and new_participant not in expenses:
                expenses[new_participant] = 0
                save_expenses(expenses)
                st.session_state["expenses"] = expenses
                st.success(f"✅ {new_participant} added!")
            else:
                st.warning("⚠ Enter a unique name!")

        if col2.button("❌ Remove"):
            if new_participant in expenses:
                del expenses[new_participant]
                save_expenses(expenses)
                st.session_state["expenses"] = expenses
                st.error(f"❌ {new_participant} removed!")
            else:
                st.warning("⚠ Participant not found!")

        st.write("### Current Participants:")
        st.write(list(expenses.keys()) if expenses else "No participants added yet.")

    # ---- EXPENSES TAB ----
    with tab_add_expense:
        st.header("💵 Add Expenses")

        if expenses:
            payer = st.selectbox("Who paid?", list(expenses.keys()))
            amount = st.number_input("Amount", min_value=0.0, format="%.2f")
            description = st.text_input("Description")

            if st.button("💰 Add Expense"):
                if amount > 0:
                    expenses[payer] += amount
                    save_expenses(expenses)
                    st.session_state["expenses"] = expenses
                    st.success(f"💰 {payer} paid {amount:.2f} for {description}")
                else:
                    st.warning("⚠ Enter a valid amount!")

    # ---- SUMMARY TAB ----
    with tab_summary:
        st.header("📊 Expense Summary")

        if expenses:
            for person, balance in expenses.items():
                st.success(f"✅ {person} balance: {balance:.2f}")

        if st.button("🔄 Reset"):
            reset_expenses()
            st.warning("🔄 All data has been reset!")

