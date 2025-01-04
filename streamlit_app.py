import streamlit as st
import numpy as np
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import requests
import plotly.express as px




st.set_page_config(page_title = "Chemical Inventory Manager", page_icon = "owl")

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
    # Title: Current Inventory
    st.header("Current Inventory")
    st.subheader("Important Messages")
    
    # Load data
    inventory = conn.read(worksheet="Inventory", ttl=1)
    usage = conn.read(worksheet="Usage", ttl=1)

    # Process usage data
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
    
    # Calculate Remaining Percentage
    df_total_usage_per_chemical_name["Remaining Percent (%)"] = round(
        100 * df_total_usage_per_chemical_name["Remaining Amount (g)"] / df_total_usage_per_chemical_name["Initial Quantity (g)"], 2
    )
    
    # Convert "Expiry Date" to datetime format
    df_total_usage_per_chemical_name["Expiry Date"] = pd.to_datetime(df_total_usage_per_chemical_name["Expiry Date"])
    
    # Current date for calculations
    today = pd.Timestamp.now()

    # Red warning filters
    red_critical_expiry = df_total_usage_per_chemical_name[
        df_total_usage_per_chemical_name["Expiry Date"] < today + pd.Timedelta(days=90)
    ]["Chemical Name"].tolist()

    red_critical_remaining = df_total_usage_per_chemical_name[
        df_total_usage_per_chemical_name["Remaining Percent (%)"] < 30
    ]["Chemical Name"].tolist()

    # Yellow warning filters, excluding chemicals in red warnings
    yellow_critical_expiry = df_total_usage_per_chemical_name[
        (df_total_usage_per_chemical_name["Expiry Date"] < today + pd.Timedelta(days=180)) &
        (df_total_usage_per_chemical_name["Expiry Date"] >= today + pd.Timedelta(days=90))
    ]["Chemical Name"].tolist()

    yellow_critical_remaining = df_total_usage_per_chemical_name[
        (df_total_usage_per_chemical_name["Remaining Percent (%)"] < 50) &
        (df_total_usage_per_chemical_name["Remaining Percent (%)"] >= 30)
    ]["Chemical Name"].tolist()

    yellow_critical_expiry = [chem for chem in yellow_critical_expiry if chem not in red_critical_expiry]
    yellow_critical_remaining = [chem for chem in yellow_critical_remaining if chem not in red_critical_remaining]

    # Display warning messages
    if red_critical_expiry or red_critical_remaining:
        st.error(f"""
        ⚠️ **Critical Chemicals Usage (RED)**:
        - Expiration date in the next 3 months: {', '.join(red_critical_expiry) if red_critical_expiry else 'None'}
        - Remaining percentage < 30%: {', '.join(red_critical_remaining) if red_critical_remaining else 'None'}
        """)

    if yellow_critical_expiry or yellow_critical_remaining:
        st.warning(f"""
        ⚠️ **Monitor These Chemicals (YELLOW)**:
        - Expiration date in the next 3-6 months: {', '.join(yellow_critical_expiry) if yellow_critical_expiry else 'None'}
        - Remaining percentage 30-50%: {', '.join(yellow_critical_remaining) if yellow_critical_remaining else 'None'}
        """)

    # Create a new column for the combined Chemical Name and Expiry Date
    df_total_usage_per_chemical_name["Chemical Name (Expiry Date)"] = (
        df_total_usage_per_chemical_name["Chemical Name"] + 
        " (" + 
        df_total_usage_per_chemical_name["Expiry Date"].dt.strftime('%Y-%m-%d') + 
        ")"
    )
    
    # Sort data by expiry date
    df_sorted = df_total_usage_per_chemical_name.sort_values("Expiry Date", ascending=False)
    
    # Title of chart: Remaining Percentage of Chemicals
    st.subheader("Remaining Percentage of Chemicals")
    
    # Create a bar chart
    fig = px.bar(
        df_sorted,
        x="Remaining Percent (%)",
        y="Chemical Name (Expiry Date)",
        color="Remaining Percent (%)",  # Color bars based on remaining percentage
        color_continuous_scale="Viridis",  # Choose a color scale (e.g., Viridis, Plasma, etc.)
        #title="Remaining Percentage of Chemicals",
        labels={"Remaining Percent (%)": "Remaining Percentage (%)"},  # Axis labels
        height=700
    )

    # Update hovertemplate to show "Expire Date"
    fig.update_traces(
        hovertemplate="Chemical Name: %{y}<br>Remaining Percent: %{x}%<br>Expiry Date: %{customdata}",
        customdata=df_sorted["Expiry Date"].dt.strftime('%Y-%m-%d')
    )

    # Expander: How to read this chart?
    with st.expander("How to read this chart?"):
        st.markdown("""
        - **Sorting:** Bars are arranged by expiry dates (earliest at the top, latest at the bottom).
        - **Colors:** Darker bars indicate lower remaining percentages, highlighting chemicals to prioritize.
        - **Details:** Hover over a bar to view the chemical name, remaining percentage, and expiry date.
        """)

    # Display chart
    st.plotly_chart(fig)

    # Title of table: Table: Current Inventory
    st.subheader("Table: Current Inventory")
    
    # Expander: How to read this table?
    with st.expander("How to read this table?"):
        st.markdown("""
        - This table lists all chemicals in the laboratory, including:
          - **CAS number**: Unique identifier for each chemical.
          - **Initial quantity**: The starting amount of the chemical.
          - **Expiry date**: The date when the chemical expires.
          - **Important notes**: Additional information or remarks about the chemical.
          - **Total amount used**: The cumulative amount consumed so far.
          - **Remaining amount**: The amount left in the package.
        """)

    # Select only the desired columns
    columns_to_display = [
        "Chemical Name", 
        "CAS Number", 
        "Initial Quantity (g)", 
        "Expiry Date", 
        "Notes", 
        "Total Amount Used (g)", 
        "Remaining Amount (g)"
    ]
    filtered_table = df_total_usage_per_chemical_name[columns_to_display]

    # Display the filtered table
    st.dataframe(filtered_table)




def view_usage_history(conn):
    st.header("Usage History")
    usage = conn.read(worksheet="Usage", ttl=1)
    st.subheader("Usage Table")
    st.write(usage)

    # Load inventory and usage data
    inventory = conn.read(worksheet="Inventory", ttl=1)

    # Merge inventory and usage data
    df_usage = pd.merge(
        inventory,
        usage[["Date", "Chemical Name", "Amount Used (g)"]],
        on=["Chemical Name"],
        how="left"
    )

    # Ensure Date is in datetime format
    df_usage["Date"] = pd.to_datetime(df_usage["Date"])

    # Sort data by Chemical Name and Date
    df_usage = df_usage.sort_values(by=["Chemical Name", "Date"])

    # Calculate cumulative usage for each chemical
    df_usage["Cumulative Amount Used (g)"] = df_usage.groupby("Chemical Name")["Amount Used (g)"].cumsum()

    # Calculate remaining quantity
    df_usage["Remaining Quantity (g)"] = (
        df_usage["Initial Quantity (g)"] - df_usage["Cumulative Amount Used (g)"]
    )

    # Create tabs
    tab1, tab2 = st.tabs(["Cumulative Usage", "Remaining Quantities"])

    # Tab 1: Cumulative Usage Chart
    with tab1:
        st.subheader("Cumulative Usage of Chemicals Over Time")
        fig_cumulative = px.line(
            df_usage,
            x="Date",
            y="Cumulative Amount Used (g)",
            color="Chemical Name",  # One line per chemical
            title="Cumulative Chemical Usage Over Time",
            labels={
                "Cumulative Amount Used (g)": "Cumulative Amount Used (g)",
                "Date": "Date"
            },
            height=500
        )
        st.plotly_chart(fig_cumulative)

    # Tab 2: Remaining Quantities Chart
    with tab2:
        st.subheader("Remaining Quantities of Chemicals Over Time")
        fig_remaining = px.line(
            df_usage,
            x="Date",
            y="Remaining Quantity (g)",
            color="Chemical Name",  # One line per chemical
            title="Remaining Quantities of Chemicals Over Time",
            labels={
                "Remaining Quantity (g)": "Remaining Quantity (g)",
                "Date": "Date"
            },
            height=500
        )
        st.plotly_chart(fig_remaining)


# Map pages to functions
PAGES = {
    "Add Chemical": lambda: add_chemical(conn),
    "Log Usage": lambda: log_chemical_usage(conn),
    "View Inventory": lambda: view_inventory(conn),
    "View Usage History": lambda: view_usage_history(conn)
}

# Select the operation
# section = st.selectbox("Select an Operation", list(PAGES.keys()))

# Sidebar navigation
st.sidebar.title("Navigation")
section = st.sidebar.selectbox("Select a Page", list(PAGES.keys()))

# Render the selected page
PAGES[section]()
