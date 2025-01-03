import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
inventory = conn.read()

# Title of the app
st.title("Chemical Inventory Manager")

# Define the pages as functions
def add_chemical(inventory, conn):
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
            conn.update(data=inventory)
            st.success(f"{name} added to inventory!")

def search_inventory(inventory):
    st.header("Search Inventory")
    search_query = st.text_input("Enter Chemical Name or CAS Number to Search")
    if search_query:
        # Filter the inventory based on the query
        search_results = inventory[
            inventory["Chemical Name"].str.contains(search_query, case=False, na=False) |
            inventory["CAS Number"].str.contains(search_query, case=False, na=False)
        ]
        if not search_results.empty:
            st.write("Search Results:")
            st.write(search_results)
        else:
            st.warning("No matching chemicals found.")

def update_inventory(inventory, conn):
    st.header("Update Inventory")
    chemical_to_update = st.selectbox("Select Chemical to Update", inventory["Chemical Name"].unique())
    if chemical_to_update:
        selected_row = inventory[inventory["Chemical Name"] == chemical_to_update]
        new_quantity = st.number_input(
            f"Update Quantity for {chemical_to_update}",
            min_value=0.0,
            step=0.1,
            value=float(selected_row["Quantity"].iloc[0])
        )
        if st.button("Update Quantity"):
            # Update the quantity in the inventory
            inventory.loc[inventory["Chemical Name"] == chemical_to_update, "Quantity"] = new_quantity

            # Write the updated inventory back to Google Sheets
            conn.update(data=inventory)
            st.success(f"Quantity for {chemical_to_update} updated to {new_quantity}!")

# Map pages to functions
PAGES = {
    "Add Chemical": lambda: add_chemical(inventory, conn),
    "Search Inventory": lambda: search_inventory(inventory),
    "Update Inventory": lambda: update_inventory(inventory, conn)
}

# Select the operation
section = st.selectbox("Select an Operation", list(PAGES.keys()))

# Render the selected page
PAGES[section]()
