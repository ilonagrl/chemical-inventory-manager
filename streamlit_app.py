import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import requests

# Connect to the Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyc34ID-pOXilSRyKATdL_9BN9DPig_eUOFKYMRtb8Um4yDOTVqg930OeVgKlE0fODr/exec"

# usage = conn.read(worksheet="Usage") # 2nd way - optimal but might provide conflicts with users > 1

# Title of the app
st.title("Chemical Inventory Manager")

# Define the pages as functions
def add_chemical(conn):
    st.header("Add New Chemical")

    inventory = conn.read(worksheet="Inventory", ttl=1)

    with st.form("add_chemical_form"):
        name = st.text_input("Chemical Name")
        cas_number = st.text_input("CAS Number")
        initial_quantity = st.number_input("Initial Quantity (g)", min_value=0.0, step=0.1)
        expiry_date = st.date_input("Expiry Date")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Chemical")

        if submitted:
            # Append data to Google Sheets
            new_row = pd.DataFrame([{
                "Chemical Name": name,
                "CAS Number": cas_number,
                "Quantity": initial_quantity,
                "Expiry Date": str(expiry_date),
                "Safety Notes": notes
                #"Unit": unit,
                #"Storage Location": storage,
    
            }])
            updated_inventory = pd.concat([inventory, new_row], ignore_index=True)
            # Write the updated inventory back to Google Sheets
            conn.update(data=updated_inventory,  worksheet="Inventory")
            st.success(f"{name} added to inventory!")

def add_chemical_web_app():
    st.header("Add New Chemical")
    with st.form("add_chemical_form"):
        name = st.text_input("Chemical Name")
        cas_number = st.text_input("CAS Number")
        initial_quantity = st.number_input("Initial Quantity (g)", min_value=0.0, step=0.1)
        expiry_date = st.date_input("Expiry Date")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Chemical")

        if submitted:
            # Prepare the data payload
            data = {
                "name": name,
                "casNumber": cas_number,
                "initialQuantity": initial_quantity,
                "expiryDate": str(expiry_date),
                "notes": notes
            }

            # Send the data to the Google Apps Script Web App
            response = requests.post(WEB_APP_URL, json=data)

            if response.status_code == 200:
                st.success(f"{name} added successfully!")
            else:
                st.error("Failed to add chemical. Please try again.")

def log_chemical_usage(conn):
    # Load the Inventory and Usage tabs
    inventory = conn.read(worksheet="Inventory", ttl=1)
    usage = conn.read(worksheet="Usage", ttl=1) # 1 way, not optimal, loading usage after every click (tll=1 means cache for 1 sec)

    st.header("Log Chemical Usage")
    with st.form("log_chemical_usage_form"):
        chemical_name = st.selectbox("Select Chemical", inventory["Chemical Name"].unique())
        amount_used = st.number_input("Amount Used (g)", min_value=0.0, step=0.1)
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Log Usage")

        if submitted:
            # Add a new usage entry to Usage sheet
            new_entry = pd.DataFrame([{
                "Date": pd.Timestamp.now().strftime("%Y-%m-%d"),
                "Chemical Name": chemical_name,
                "Amount Used (g)": amount_used,
                "Notes": notes
            }])
            updated_usage = pd.concat([usage, new_entry], ignore_index=True)
            conn.update(data=updated_usage, worksheet="Usage")
            st.success(f"Logged {amount_used} g of {chemical_name}.")

def view_inventory(conn):
    st.header("Current Inventory")
    inventory = conn.read(worksheet="Inventory", ttl=1)
    st.write(inventory)

def view_usage_history(conn):
    st.header("Usage History")
    usage = conn.read(worksheet="Usage", ttl=1)
    st.write(usage)

# Map pages to functions
PAGES = {
    "Add Chemical": lambda: add_chemical(conn),
    "Log Usage": lambda: log_chemical_usage(conn),
    "View Inventory": lambda: view_inventory(conn),
    "View Usage History": lambda: view_usage_history(conn)
}

# Select the operation
section = st.selectbox("Select an Operation", list(PAGES.keys()))

# Render the selected page
PAGES[section]()
