# 📌 Import required libraries
import streamlit as st  # Streamlit for the web interface
import streamlit_authenticator as stauth  # User authentication
import pandas as pd  # Pandas for data handling
import os  # OS module for file operations
import yaml  # YAML for storing user credentials
from yaml.loader import SafeLoader  # Safe loading of YAML files
import bcrypt  # For hashing passwords securely

# 📌 Function to load authentication data from config.yaml
def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)

# 📌 Function to save updated authentication data
def save_config(config):
    with open("config.yaml", "w") as file:
        yaml.dump(config, file)

# 📌 Load authentication configuration from YAML file
config = load_config()

# 📌 Initialize authentication system
authenticator = stauth.Authenticate(
    config["credentials"],  # User credentials from config.yaml
    config["cookie"]["name"],  # Cookie name for session storage
    config["cookie"]["key"],  # Secret key for cookies
    config["cookie"]["expiry_days"],  # Cookie expiration time
)

# 📌 Create navigation tabs for Login and Sign-Up
tab1, tab2 = st.tabs(["🔑 Login", "🆕 Sign Up"])

# ------------------------- LOGIN TAB -------------------------
with tab1:
    # 📌 Display login widget
    name, authentication_status, username = authenticator.login("Login", location="main")

    # 📌 If authentication is successful
    if authentication_status:
        st.sidebar.title(f"Welcome, {name}")  # Show user name in sidebar
        authenticator.logout("Logout", "sidebar")  # Add a logout button

        # 📌 Each user gets a separate file to store their expenses
        file_name = f"expenses_{username}.csv"

        # 📌 Function to load expenses
        def load_expenses():
            if os.path.exists(file_name):  # Check if user file exists
                df = pd.read_csv(file_name)  # Read CSV file into DataFrame
                return dict(zip(df["Participant"], df["Amount"]))  # Convert to dictionary
            return {}  # Return empty dictionary if file doesn't exist

        # 📌 Function to save expenses
        def save_expenses(expenses):
            df = pd.DataFrame(expenses.items(), columns=["Participant", "Amount"])
            df.to_csv(file_name, index=False)  # Save to user's CSV file

        # 📌 Function to reset expenses (clear data)
        def reset_expenses():
            global expenses
            expenses = {}  # Reset dictionary
            if os.path.exists(file_name):  # Check if file exists
                os.remove(file_name)  # Delete the file
            st.session_state.clear()  # Clear session state

        # 📌 Load user-specific expenses
        expenses = load_expenses()

        # ------------------------- EXPENSE SPLITTER APP UI -------------------------

        # 📌 App title
        st.title("💰 Expense Splitter (Private Data)")

        # 📌 Create navigation tabs for different sections
        tab_home, tab_participants, tab_add_expense, tab_summary = st.tabs(
            ["🏠 Home", "👥 Participants", "💵 Add Expense", "📊 Summary"]
        )

        # ---- HOME TAB ----
        with tab_home:
            st.header("🏠 Welcome to the Expense Splitter App")
            st.write(
                "This app helps you split expenses among friends fairly. "
                "Your data is private and secured with authentication."
            )
            st.image(
                "https://i.pinimg.com/originals/55/de/06/55de068a005a71c0720cb64c3c6be828.gif",
                use_container_width=True,
            )

        # ---- PARTICIPANTS TAB ----
        with tab_participants:
            st.header("👥 Manage Participants")
            new_participant = st.text_input("Enter participant name")

            col1, col2 = st.columns(2)

            # Add Participant Button
            if col1.button("➕ Add"):
                if new_participant and new_participant not in expenses:
                    expenses[new_participant] = 0
                    save_expenses(expenses)
                    st.success(f"✅ {new_participant} added!")
                else:
                    st.warning("⚠ Enter a unique name!")

            # Remove Participant Button
            if col2.button("❌ Remove"):
                if new_participant in expenses:
                    del expenses[new_participant]
                    save_expenses(expenses)
                    st.error(f"❌ {new_participant} removed!")
                else:
                    st.warning("⚠ Participant not found!")

            # Display current participants
            st.write("### Current Participants:")
            if expenses:
                st.write(list(expenses.keys()))
            else:
                st.info("No participants added yet.")

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
                                if len(shares) == len(expenses) and sum(shares) == 100:
                                    for i, person in enumerate(expenses):
                                        balances[person] -= (amount * (shares[i] / 100))
                                    balances[payer] += amount
                                else:
                                    raise ValueError
                            except:
                                st.error("⚠ Invalid shares. Must sum to 100.")
                                st.stop()

                        for person in balances:
                            expenses[person] += balances[person]

                        save_expenses(expenses)
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
                    if balance > 0:
                        st.success(f"✅ {person} should receive {balance:.2f}")
                    elif balance < 0:
                        st.error(f"❌ {person} owes {-balance:.2f}")
                    else:
                        st.info(f"✔ {person} is settled.")

            if st.button("🔄 Reset"):
                reset_expenses()
                st.warning("🔄 All data has been reset!")

# ------------------------- SIGN-UP TAB -------------------------
with tab2:
    st.header("🆕 Sign Up")

    new_name = st.text_input("Full Name")
    new_email = st.text_input("Email")
    new_username = st.text_input("Choose a Username")
    new_password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("🔑 Register"):
        if new_username in config["credentials"]["usernames"]:
            st.error("⚠ Username already exists!")
        elif new_password != confirm_password:
            st.error("⚠ Passwords do not match!")
        else:
            hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            config["credentials"]["usernames"][new_username] = {"email": new_email, "name": new_name, "password": hashed_password}
            save_config(config)
            st.success(f"✅ {new_name} registered successfully! Please log in.")
