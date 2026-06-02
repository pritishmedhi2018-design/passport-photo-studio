import streamlit as st
from modules.database import get_orders

st.set_page_config(
    page_title="Order History",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Order History")

orders = get_orders()

if not orders:

    st.warning(
        "No orders found."
    )

for row in orders:

    st.info(
        f"""
Date : {row[1]}

Photo Type : {row[2]}

Layout : {row[3]} Photos/Row

Total Photos : {row[4]}

Amount : ₹{row[5]}
"""
    )
