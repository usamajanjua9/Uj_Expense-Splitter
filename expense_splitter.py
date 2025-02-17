# 📌 Import required libraries
import streamlit as st
import streamlit_authenticator as stauth  # For user authentication
import pandas as pd
import os
import yaml
from yaml.loader import SafeLoader
import bcrypt  # Secure password hashing

# -------------------------------------------
# 📌 Load or Create Authentication Config
# -------------------------------------------

CONFIG_FILE = "config.yaml"

# 🔹 Function to load authentication config, create default if missing
def load_config():
    try:
        if not os.path.exists(CONFIG_FILE):
            default_config = {
                "credentials": {
                    "usernames": {
                        "admin": {
                            "name": "Admin",
                            "email": "admin@example.com",
                            "password": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
                        }
                    }
                },
                "cookie": {
                    "expiry_days": 30,
                    "key": "some_random_key",
                    "name": "expense_splitter_auth",
                },
                "preauthorized": {"emails": ["admin@example.com"]},
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

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

# -------------------------------------------
# 📌 Authentication UI (Login & Sign-Up)
# -------------------------------------------

tab1, tab2 = st.tabs(["🔑 Login", "🆕 Sign Up"])

# --------- LOGIN ---------
with tab1:
    name, authentication_status, username = authenticator.login("Login", "main")  

    if authentication_status:
        st.sidebar.title(f"Welcome, {name}")  # Sidebar welcome message
        if st.sidebar.button("Logout"):
            authenticator.logout("Logout", "sidebar")
            st.experimental_rerun()

        # 🔹 Private file for each user
        file_name = f"expenses_{username}.csv"

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
            global expenses
            expenses = {}
            if os.path.exists(file_name):
                os.remove(file_name)
            st.session_state.clear()

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
                split_type = st.radio("Split Type", ["Equal", "Unequal"])

                if split_type == "Unequal":
                    split_values = st.text_input("Enter shares (e.g., 50,30,20)")

                if st.button("💰 Add Expense"):
                    if amount > 0:
                        balances = {person: 0 for person in expenses}

                        if split_type == "Equal":
                            share_per_person = amount / len(expenses)
                            for person in expenses:
                                balances[person] -= share_per_person
                            balances[payer] += amount
                        else:
                            try:
                                shares = list(map(float, split_values.split(",")))
                                if len(shares) != len(expenses) or sum(shares) != 100:
                                    raise ValueError
                                for i, person in enumerate(expenses):
                                    balances[person] -= (amount * (shares[i] / 100))
                                balances[payer] += amount
                            except:
                                st.error("⚠ Invalid shares. Must sum to 100.")
                                st.stop()

                        for person in balances:
                            expenses[person] += balances[person]

                        save_expenses(expenses)
                        st.session_state["expenses"] = expenses
                        st.success(f"💰 {payer} paid {amount:.2f} for {description}")
                    else:
                        st.warning("⚠ Enter a valid amount!")

        # ---- SUMMARY TAB ----
        with tab_summary:
            st.header("📊 Expense Summary")

            if expenses:
                total_paid = {person: expenses[person] for person in expenses}
                total_spent = sum(expenses.values())
                fair_share = total_spent / len(expenses)

                balances = {person: total_paid[person] - fair_share for person in expenses}

                for person, balance in balances.items():
                    st.success(f"✅ {person} should receive {balance:.2f}") if balance > 0 else (
                        st.error(f"❌ {person} owes {-balance:.2f}") if balance < 0 else st.info(f"✔ {person} is settled.")
                    )

            if st.button("🔄 Reset"):
                reset_expenses()
                st.warning("🔄 All data has been reset!")

# --------- SIGN-UP ---------
with tab2:
    st.header("🆕 Sign Up")
    new_name, new_email, new_username, new_password, confirm_password = (
        st.text_input("Full Name"),
        st.text_input("Email"),
        st.text_input("Choose a Username"),
        st.text_input("Password", type="password"),
        st.text_input("Confirm Password", type="password"),
    )

    if st.button("🔑 Register"):
        if new_username in config["credentials"]["usernames"]:
            st.error("⚠ Username already exists!")
        elif new_password != confirm_password:
            st.error("⚠ Passwords do not match!")
        else:
            config["credentials"]["usernames"][new_username] = {
                "email": new_email, "name": new_name, "password": bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode(),
            }
            save_config(config)
            st.success(f"✅ {new_name} registered! Please log in.")
