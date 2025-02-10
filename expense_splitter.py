import streamlit as st  # Import Streamlit for creating the web app
import pandas as pd  # Import Pandas for handling tabular expense data
import os  # Import OS module to check if a file exists
import io  # Import io module for in-memory file operations

# Set Page Configuration (Optimized for Mobile View)
st.set_page_config(page_title="💰 Expense Splitter", page_icon="📱", layout="wide", initial_sidebar_state="collapsed")

# Hide Streamlit's extra UI elements
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# File name for saving and loading expenses data
file_name = "expenses.csv"

# Function to load existing expenses from CSV file
def load_expenses():
    if os.path.exists(file_name):  # Check if the file exists
        df = pd.read_csv(file_name)  # Read the CSV file into a Pandas DataFrame
        return dict(zip(df["Participant"], df["Amount"]))  # Convert DataFrame to dictionary {name: amount}
    return {}  # Return an empty dictionary if the file doesn't exist

# Function to save expenses data into a CSV file
def save_expenses(expenses):
    df = pd.DataFrame(expenses.items(), columns=["Participant", "Amount"])  # Convert dictionary to DataFrame
    df.to_csv(file_name, index=False)  # Save the DataFrame as a CSV file (without row index)

# Function to reset all expenses and participants
def reset_expenses():
    global expenses  # Use global variable to modify
    expenses = {}  # Clear the expenses dictionary
    if os.path.exists(file_name):  # Check if the file exists
        os.remove(file_name)  # Delete the CSV file to remove saved data
    st.session_state.clear()  # Clear Streamlit's session state for UI refresh

# Load expenses at the start of the app
expenses = load_expenses()

# Display the app title
st.title("💰 Expense Splitter (Mobile Friendly)")

# Create navigation tabs for different sections of the app
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home", "👥 Participants", "💵 Add Expense", "📊 Summary"])

# ---- HOME TAB ----
with tab1:
    st.header("🏠 Welcome to the Expense Splitter App")
    st.write("This app helps you split expenses among friends fairly. "
             "You can add participants, add expenses, and view balances. "
             "It works on both mobile and desktop!")
    st.image("https://i.pinimg.com/originals/55/de/06/55de068a005a71c0720cb64c3c6be828.gif", use_container_width=True)

# ---- PARTICIPANTS TAB ----
with tab2:
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
with tab3:
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
                balances = {person: 0 for person in expenses}  # Initialize balance tracking

                if split_type == "Equal":
                    share_per_person = amount / len(expenses)
                    for person in expenses:
                        balances[person] -= share_per_person
                    balances[payer] += amount  # Payer gets reimbursed

                else:  # Unequal split
                    try:
                        shares = list(map(float, split_values.split(",")))
                        if len(shares) == len(expenses) and sum(shares) == 100:
                            for i, person in enumerate(expenses):
                                balances[person] -= (amount * (shares[i] / 100))
                            balances[payer] += amount  # Payer gets reimbursed
                        else:
                            raise ValueError
                    except:
                        st.error("⚠ Invalid shares. Must sum to 100.")
                        st.stop()

                # Update expenses dictionary
                for person in balances:
                    expenses[person] += balances[person]

                save_expenses(expenses)
                st.success(f"💰 {payer} paid {amount:.2f} for {description}")
            else:
                st.warning("⚠ Enter a valid amount!")

# ---- SUMMARY TAB ----
with tab4:
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

    if st.button("📂 Export to CSV"):
        save_expenses(expenses)
        df = pd.DataFrame(expenses.items(), columns=["Participant", "Amount"])
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        st.download_button(label="Download CSV", data=buffer.getvalue(), file_name="expenses.csv", mime="text/csv")

    if st.button("🔄 Reset"):
        reset_expenses()
        st.warning("🔄 All data has been reset!")
