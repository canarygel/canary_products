import os
import pandas as pd
import streamlit as st
from io import StringIO

st.set_page_config(page_title="Canary Products Workflow", page_icon="🛠️", layout="wide")

DATA_PATH = os.path.join("data", "products.csv")

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    # Try to auto-detect delimiter (comma, tab, semicolon)
    try:
        df = pd.read_csv(path, sep=None, engine="python")
    except Exception:
        # Fallback to tab-delimited
        df = pd.read_csv(path, sep="\t")
    # Normalize column names and strip whitespace
    df.columns = [c.strip() for c in df.columns]
    # Map likely header variants
    colmap = {c.lower(): c for c in df.columns}
    def find(colnames):
        for want in colnames:
            for k, v in colmap.items():
                if k == want.lower():
                    return v
        return None

    prod_col  = find(["Product", "Product Name", "product_name"])
    stage_col = find(["Stage", "Phase"])
    task_col  = find(["Checklist", "Task", "To Do", "Todo", "Item"])

    missing = [n for n, c in [("Product", prod_col), ("Stage", stage_col), ("Checklist", task_col)] if c is None]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    # Clean values
    for c in [prod_col, stage_col, task_col]:
        df[c] = df[c].astype(str).str.strip()

    # Drop empty tasks
    df = df[df[task_col].astype(str).str.len() > 0]

    return df, prod_col, stage_col, task_col

if not os.path.exists(DATA_PATH):
    st.error(f"❌ Could not find dataset at: {DATA_PATH}")
    st.stop()

try:
    df, PROD, STAGE, TASK = load_data(DATA_PATH)
except Exception as e:
    st.error(f"⚠️ Failed to load/parse the CSV: {e}")
    st.stop()

st.title("🛠️ Canary Products Workflow Tracker")

# Sidebar: product picker
products = sorted(df[PROD].dropna().unique().tolist())
if not products:
    st.error("No products found in the CSV.")
    st.stop()

product = st.sidebar.selectbox("Select a product", products, index=0)

# Filter for selected product
pdf = df[df[PROD] == product].copy()
if pdf.empty:
    st.warning("No rows found for this product.")
    st.stop()

# Keep stage appearance order (first occurrence wins)
stage_order = pd.Index(pdf[STAGE]).drop_duplicates().tolist()

# Header + details
st.subheader(f"📋 Product: {product}")
st.caption(f"{len(pdf)} tasks across {len(stage_order)} stage(s)")

# Progress helpers
def task_key(p, s, t):
    return f"chk::{p}::{s}::{t}"

def stage_progress(stage_df):
    total = len(stage_df)
    done = sum(bool(st.session_state.get(task_key(product, row[STAGE], row[TASK]), False))
               for _, row in stage_df.iterrows())
    return done, total

# Buttons to set/clear a whole stage
def set_stage(stage_df, value: bool):
    for _, row in stage_df.iterrows():
        st.session_state[task_key(product, row[STAGE], row[TASK])] = value

# Render stages
overall_done = 0
overall_total = 0

for stage in stage_order:
    sdf = pdf[pdf[STAGE] == stage]

    # Progress before rendering
    done, total = stage_progress(sdf)
    overall_done += done
    overall_total += total

    with st.expander(f"🧭 {stage} — {done}/{total} done", expanded=True):
        cols = st.columns([1, 1, 8])
        with cols[0]:
            if st.button("Mark all", key=f"all_{stage}"):
                set_stage(sdf, True)
        with cols[1]:
            if st.button("Clear all", key=f"clear_{stage}"):
                set_stage(sdf, False)

        # List tasks with checkboxes
        for _, row in sdf.iterrows():
            key = task_key(product, row[STAGE], row[TASK])
            st.checkbox(str(row[TASK]), key=key)

# Overall progress
if overall_total > 0:
    st.subheader("📈 Overall Progress")
    st.progress(int((overall_done / overall_total) * 100))
    st.caption(f"{overall_done} of {overall_total} tasks completed")

# Download current checklist state
state_rows = []
for _, row in pdf.iterrows():
    key = task_key(product, row[STAGE], row[TASK])
    state_rows.append({
        "Product": product,
        "Stage": row[STAGE],
        "Checklist": row[TASK],
        "Done": bool(st.session_state.get(key, False))
    })
state_df = pd.DataFrame(state_rows).sort_values([ "Stage", "Checklist" ])

csv_buf = StringIO()
state_df.to_csv(csv_buf, index=False)
st.download_button(
    label="⬇️ Download current checklist state (CSV)",
    data=csv_buf.getvalue(),
    file_name=f"{product}_checklist_state.csv",
    mime="text/csv",
)
