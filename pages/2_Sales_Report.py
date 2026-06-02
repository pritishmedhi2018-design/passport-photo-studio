import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(
    page_title="Sales Report",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Sales Report")

# ----------------------------
# LOAD DATABASE
# ----------------------------

conn = sqlite3.connect("sales.db")

df = pd.read_sql_query(
    """
    SELECT *
    FROM orders
    ORDER BY id DESC
    """,
    conn
)

conn.close()

# ----------------------------
# NO DATA
# ----------------------------

if df.empty:

    st.warning(
        "No sales records found."
    )

    st.stop()

# ----------------------------
# METRICS
# ----------------------------

c1, c2, c3 = st.columns(3)

c1.metric(
    "Total Orders",
    len(df)
)

c2.metric(
    "Total Revenue",
    f"₹{df['amount'].sum():,.0f}"
)

c3.metric(
    "Average Bill",
    f"₹{df['amount'].mean():,.0f}"
)

st.divider()

# ----------------------------
# SALES TABLE
# ----------------------------

st.subheader("Sales Records")

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# ----------------------------
# PHOTO TYPE REPORT
# ----------------------------

st.divider()

st.subheader(
    "Photo Type Summary"
)

photo_summary = (
    df.groupby("photo_type")
    .agg(
        Orders=("id", "count"),
        Revenue=("amount", "sum")
    )
    .reset_index()
)

st.dataframe(
    photo_summary,
    use_container_width=True,
    hide_index=True
)

# ----------------------------
# REVENUE CHART
# ----------------------------

st.divider()

st.subheader(
    "Revenue Distribution"
)

chart_df = (
    df.groupby("photo_type")
    ["amount"]
    .sum()
)

st.bar_chart(chart_df)

# ----------------------------
# EXPORT CSV
# ----------------------------

st.divider()

csv = df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    "⬇ Export Sales Report CSV",
    csv,
    "sales_report.csv",
    "text/csv",
    use_container_width=True
)