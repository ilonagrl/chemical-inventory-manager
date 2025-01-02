import streamlit as st
import pandas as pd
import os

# File to save the inventory
INVENTORY_FILE = "inventory.csv"

# Title of the app
st.title("Chemical Inventory Manager")

# Description
st.write("Manage your lab's chemical inventory efficiently adasd!")

# Load inventory from file
if os.path.exists(INVENTORY_FILE):
    st.session_state["inventory"] = pd.read_csv(INVENTORY_FILE)
else:
    st.session_state["inventory"] = pd.DataFrame(columns=["Chemical Name", "Quantity", "Unit", "Expiry Date"])

# Add a new chemical
st.header("Add New Chemical")
with st.form("add_chemical_form"):
    name = st.text_input("Chemical Name")
    quantity = st.number_input("Quantity", min_value=0.0, step=0.1)
    unit = st.selectbox("Unit", ["g", "kg", "mL", "L"])
    expiry_date = st.date_input("Expiry Date")
    submitted = st.form_submit_button("Add Chemical")

    if submitted:
        # Add the chemical to inventory
        new_row = pd.DataFrame({
            "Chemical Name": [name],
            "Quantity": [quantity],
            "Unit": [unit],
            "Expiry Date": [expiry_date]
        })
        st.session_state["inventory"] = pd.concat([st.session_state["inventory"], new_row], ignore_index=True)
        st.session_state["inventory"].to_csv(INVENTORY_FILE, index=False)  # Save to file
        st.success(f"{name} added to inventory!")

# Display inventory
st.header("Current Inventory")
st.write(st.session_state["inventory"])
