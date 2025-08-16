import streamlit as st
import pandas as pd
import os

# Path to your dataset
data_path = os.path.join("data", "products.csv")

# Load dataset
if os.path.exists(data_path):
    df = pd.read_csv(data_path, sep=",")  # adjust delimiter if needed
else:
    st.error(f"❌ Could not find dataset at: {data_path}")
    st.stop()

st.title("🛠️ Canary Products Workflow Tracker")

# Select a product
product = st.selectbox("Select a product", df["Product"].unique())

# Filter data for the selected product
product_data = df[df["Product"] == product]

st.subheader("📋 Product Workflow")

# Group by stage and list tasks
for stage, group in product_data.groupby("Stage"):
    st.markdown(f"### {stage}")
    for task in group["Checklist"]:
        key = f"{product}_{stage}_{task}"
        st.checkbox(task, key=key)
