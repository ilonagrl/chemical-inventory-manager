import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import requests

# Connect to the Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)
 
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
                "Initial Quantity (g)": initial_quantity,
                "Expiry Date": str(expiry_date),
                "Notes": notes
                #"Unit": unit,
                #"Storage Location": storage,
    
            }])
            updated_inventory = pd.concat([inventory, new_row], ignore_index=True)
            # Write the updated inventory back to Google Sheets
            conn.update(data=updated_inventory,  worksheet="Inventory")
            st.success(f"{name} added to inventory!")

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
    usage = conn.read(worksheet="Usage", ttl=1)

    usage["Amount Used (g)"] = usage["Amount Used (g)"].astype(float)

    df_inventory_with_usage = pd.merge(
        inventory,
        usage[["Date", "Chemical Name", "Amount Used (g)"]],
        on=["Chemical Name"],
        how="left"
    )

    df_total_usage_per_chemical_name = df_inventory_with_usage.groupby(["Chemical Name"])["Amount Used (g)"].sum().reset_index()
    df_total_usage_per_chemical_name.rename(columns={"Amount Used (g)": "Total Amount Used (g)"}, inplace=True)

    df_total_usage_per_chemical_name = pd.merge(
        inventory,
        df_total_usage_per_chemical_name,
        on=["Chemical Name"],
        how="left"
    )

    df_total_usage_per_chemical_name["Total Amount Used (g)"] = df_total_usage_per_chemical_name["Total Amount Used (g)"].fillna(0.0)

    df_total_usage_per_chemical_name["Remaining Amount (g)"] = df_total_usage_per_chemical_name["Initial Quantity (g)"] - df_total_usage_per_chemical_name["Total Amount Used (g)"] 
    
    st.write(df_total_usage_per_chemical_name)

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
