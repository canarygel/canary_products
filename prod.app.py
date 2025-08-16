import streamlit as st
import pandas as pd
import os

# Data path (renamed to avoid spaces)
data_path = os.path.join("data", "products.csv")

# Load CSV safely
if os.path.exists(data_path):
    df = pd.read_csv(data_path)
else:
    st.error(f"❌ Could not find dataset at: {data_path}")
    st.stop()

st.title("🛠️ Canary Products Workflow Tracker")

# Select a product
product_col = "Product Name" if "Product Name" in df.columns else df.columns[0]
product = st.selectbox("Select a product", df[product_col].unique())

# Show product details
st.subheader("📋 Product Details")
st.write(df[df[product_col] == product])

# Example workflow stages & tasks
workflow = {
    "Design": ["Finalize design", "Review specifications", "Get approvals"],
    "Manufacturing": ["Source materials", "Set up production line", "Run initial batch"],
    "Testing": ["QA testing", "Safety compliance", "User feedback"],
    "Launch": ["Marketing prep", "Distribute units", "Post-launch support"]
}

st.subheader("✅ Workflow Checklist")

# Interactive checklist
for stage, tasks in workflow.items():
    st.markdown(f"### {stage}")
    for task in tasks:
        key = f"{product}_{stage}_{task}"
        st.checkbox(task, key=key)
