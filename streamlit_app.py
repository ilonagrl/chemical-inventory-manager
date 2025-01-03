import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

conn = st.connection("gsheets", type=GSheetsConnection)
inventory = conn.read()

# Title of the app
st.title("Chemical Inventory Manager")

# Add a new chemical
st.header("Add New Chemical")
with st.form("add_chemical_form"):
    name = st.text_input("Chemical Name")
    cas_number = st.text_input("CAS Number")
    quantity = st.number_input("Quantity", min_value=0.0, step=0.1)
    unit = st.selectbox("Unit", ["g", "kg", "mL", "L"])
    storage = st.text_input("Storage Location")
    expiry_date = st.date_input("Expiry Date")
    safety_notes = st.text_area("Safety Notes")
    submitted = st.form_submit_button("Add Chemical")

    if submitted:
        # Append data to Google Sheets
        new_row = pd.DataFrame([{
            "Chemical Name": name,
            "CAS Number": cas_number,
            "Quantity": quantity,
            "Unit": unit,
            "Storage Location": storage,
            "Expiry Date": str(expiry_date),
            "Safety Notes": safety_notes
        }])
        inventory = pd.concat([inventory, new_row], ignore_index=True)

        # Write the updated inventory back to Google Sheets
        conn.update(
            data=inventory
        )
        # Success message
        st.success(f"{name} added to inventory!")

# Display the inventory
st.header("Current Inventory")
st.write(inventory)
