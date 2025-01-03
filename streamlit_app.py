import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Authenticate and connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
client = gspread.authorize(credentials)

# Open your Google Sheet
sheet = client.open("Chemical Inventory").sheet1

# Load data from Google Sheets into a DataFrame
data = sheet.get_all_records()
inventory = pd.DataFrame(data)

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
        new_row = [name, cas_number, quantity, unit, storage, str(expiry_date), safety_notes]
        sheet.append_row(new_row)
        st.success(f"{name} added to inventory!")

# Display the inventory
st.header("Current Inventory")
st.write(inventory)
