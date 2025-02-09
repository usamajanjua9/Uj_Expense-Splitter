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

# Load expenses at the start of the app
expenses = load_expenses()

# Display the app title
st.title("💰 Expense Splitter (Mobile Friendly)")

# Create navigation tabs for different sections of the app
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home", "👥 Participants", "💵 Add Expense", "📊 Summary"])

# ---- HOME TAB ----
with tab1:
    st.header("🏠 Welcome to the Expense Splitter App")  # Heading for Home Tab
    st.write(
        "This app helps you split expenses among friends fairly. "
        "You can add participants, add expenses, and view balances. "
        "It works on both mobile and desktop!"
    )  # Description of the app
    st.image("https://i.pinimg.com/originals/55/de/06/55de068a005a71c0720cb64c3c6be828.gif", use_container_width=True)  # Display an image (placeholder)

# ---- PARTICIPANTS TAB ----
with tab2:
    st.header("👥 Manage Participants")  # Heading for Participants Section
    new_participant = st.text_input("Enter participant name")  # Text input for participant name

    col1, col2 = st.columns(2)  # Create two columns for Add & Remove buttons

    # Add Participant Button
    if col1.button("➕ Add"):
        if new_participant and new_participant not in expenses:  # Check if input is valid & unique
            expenses[new_participant] = 0  # Initialize participant's expense to 0
            save_expenses(expenses)  # Save updated data to CSV
            st.success(f"✅ {new_participant} added!")  # Show success message
        else:
            st.warning("⚠ Enter a unique name!")  # Show warning if name is invalid

    # Remove Participant Button
    if col2.button("❌ Remove"):
        if new_participant in expenses:  # Check if participant exists
            del expenses[new_participant]  # Remove from dictionary
            save_expenses(expenses)  # Save updated data to CSV
            st.error(f"❌ {new_participant} removed!")  # Show removal message
        else:
            st.warning("⚠ Participant not found!")  # Show warning if participant doesn't exist

    # Display current participants
    st.write("### Current Participants:")
    if expenses:
        st.write(list(expenses.keys()))  # Show list of participant names
    else:
        st.info("No participants added yet.")  # Display message if no participants exist

# ---- EXPENSES TAB ----
with tab3:
    st.header("💵 Add Expenses")  # Heading for Add Expense section

    if expenses:  # Check if participants exist before allowing expenses
        payer = st.selectbox("Who paid?", list(expenses.keys()))  # Dropdown to select the payer
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")  # Input for expense amount
        description = st.text_input("Description")  # Text input for expense description
        split_type = st.radio("Split Type", ["Equal", "Unequal"])  # Choose how the expense is split

        if split_type == "Unequal":
            split_values = st.text_input("Enter shares (e.g., 50,30,20)")  # Get custom shares if Unequal split

        # Add Expense Button
        if st.button("💰 Add Expense"):
            if amount > 0:  # Ensure the entered amount is valid
                if split_type == "Equal":  # If expense is split equally
                    share_per_person = amount / len(expenses)  # Calculate equal share
                    for person in expenses:
                        expenses[person] += share_per_person  # Add equal share to each participant
                else:  # If expense is split unequally
                    try:
                        shares = list(map(float, split_values.split(",")))  # Convert input to list of numbers
                        if len(shares) == len(expenses) and sum(shares) == 100:  # Ensure shares sum to 100%
                            for i, person in enumerate(expenses):
                                expenses[person] += (amount * (shares[i] / 100))  # Distribute shares accordingly
                        else:
                            raise ValueError  # Raise error if shares don't sum to 100%
                    except:
                        st.error("⚠ Invalid shares. Must sum to 100.")  # Show error message
                        st.stop()  # Stop execution

                save_expenses(expenses)  # Save updated expenses to CSV
                st.success(f"💰 {payer} paid {amount:.2f} for {description}")  # Show confirmation message
            else:
                st.warning("⚠ Enter a valid amount!")  # Show warning if amount is invalid

# ---- SUMMARY TAB ----
with tab4:
    st.header("📊 Expense Summary")  # Heading for Expense Summary

    if expenses:  # Ensure there are expenses to display
        total_expense = sum(expenses.values())  # Calculate total amount spent
        num_people = len(expenses)  # Get number of participants
        fair_share = total_expense / num_people  # Calculate fair share per person

        # Calculate balance for each participant
        balances = {person: expenses[person] - fair_share for person in expenses}

        # Display balances with color-coded messages
        for person, balance in balances.items():
            if balance > 0:
                st.success(f"✅ {person} should receive {balance:.2f}")  # Green for positive balance
            elif balance < 0:
                st.error(f"❌ {person} owes {-balance:.2f}")  # Red for negative balance
            else:
                st.info(f"✔ {person} is settled.")  # Blue for settled accounts

    # Export and Download Button
    if st.button("📂 Export to CSV"):
        save_expenses(expenses)  # Save the latest data

        # Convert DataFrame to CSV format in-memory
        df = pd.DataFrame(expenses.items(), columns=["Participant", "Amount"])
        buffer = io.StringIO()  # Create an in-memory file
        df.to_csv(buffer, index=False)  # Write CSV content to buffer
        buffer.seek(0)

        # Display Download Button
        st.download_button(
            label="Download CSV",
            data=buffer.getvalue(),
            file_name="expenses.csv",
            mime="text/csv"
        )

    # Reset Button - Clears all expenses and participants
    if st.button("🔄 Reset"):
        reset_expenses()  # Call reset function
        st.warning("🔄 All data has been reset!")  # Show reset confirmation

