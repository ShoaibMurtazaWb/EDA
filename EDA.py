
import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Beginner EDA • E‑commerce", page_icon="📊", layout="wide")

st.title("📊 Beginner EDA Dashboard (Streamlit)")
st.write("This app performs **basic exploratory data analysis (EDA)** using only **pandas, numpy, plotly, and streamlit**. Upload your CSV or use the included sample.")

# 1) Load data
st.sidebar.header("1) Load Data")
uploaded = st.sidebar.file_uploader("Upload a CSV file", type=["csv"])

def load_default():
    default_path = "/mnt/data/ecommerce_dataset.csv"
    if os.path.exists(default_path):
        return pd.read_csv(default_path)
    else:
        st.error("No file uploaded and sample dataset not found.")
        st.stop()

if uploaded is not None:
    df = pd.read_csv(uploaded)
else:
    df = load_default()

# 2) Basic cleaning / typing
st.sidebar.header("2) Basic Cleaning")
# Try to parse a likely datetime column
date_col_guess = None
for c in df.columns:
    if "date" in c.lower():
        date_col_guess = c
        break
date_col = st.sidebar.selectbox("Date column (optional)", [None] + df.columns.tolist(), index=(df.columns.get_loc(date_col_guess)+1) if date_col_guess in df.columns else 0)
if date_col is not None:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

# Numeric hints
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

st.subheader("👀 Quick Peek")
top_cols = st.multiselect("Choose columns to preview", options=df.columns.tolist(), default=df.columns.tolist()[:6])
st.dataframe(df[top_cols].head(), use_container_width=True)

# 3) Basic dataset info
st.subheader("ℹ️ Dataset Info")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{len(df):,}")
c2.metric("Columns", f"{df.shape[1]}")
c3.metric("Numeric cols", f"{len(num_cols)}")
c4.metric("Categorical cols", f"{len(cat_cols)}")

with st.expander("Show column dtypes"):
    st.write(df.dtypes.astype(str))

with st.expander("Show summary statistics (numeric)"):
    if len(num_cols):
        st.dataframe(df[num_cols].describe().T, use_container_width=True)
    else:
        st.info("No numeric columns found.")

with st.expander("Show missing values by column"):
    miss = df.isna().sum().to_frame("missing_count")
    miss["missing_pct"] = (miss["missing_count"]/len(df)*100).round(2)
    st.dataframe(miss, use_container_width=True)

dup_count = len(df) - len(df.drop_duplicates())
st.caption(f"Duplicate rows: **{dup_count}**")

# 4) Simple derived metric (optional)
st.subheader("🧮 Simple Derived Metric (optional)")
qty_col = st.selectbox("Quantity column", [None] + df.columns.tolist(), index=(df.columns.get_loc("quantity")+1) if "quantity" in df.columns else 0)
price_col = st.selectbox("Price column", [None] + df.columns.tolist(), index=(df.columns.get_loc("price")+1) if "price" in df.columns else 0)
disc_col = st.selectbox("Discount column (0–1 or 0–100)", [None] + df.columns.tolist(), index=(df.columns.get_loc("discount")+1) if "discount" in df.columns else 0)

if qty_col and price_col:
    gross = df[qty_col].astype(float) * df[price_col].astype(float)
    if disc_col:
        disc = pd.to_numeric(df[disc_col], errors="coerce")
        disc = np.where(disc > 1, disc/100.0, disc)
    else:
        disc = 0.0
    df["net_revenue"] = gross * (1 - disc)
    st.success("Added **net_revenue** column.")

# 5) Filters (beginner-friendly)
st.subheader("🔎 Basic Filters")
if date_col is not None and df[date_col].notna().any():
    mind, maxd = df[date_col].min(), df[date_col].max()
    start, end = st.slider("Date range", min_value=mind, max_value=maxd, value=(mind, maxd))
    date_mask = df[date_col].between(start, end)
else:
    date_mask = pd.Series(True, index=df.index)

# Category-like filter (pick a column to filter by values)
filter_col = st.selectbox("Pick a column to filter values", [None] + df.columns.tolist())
if filter_col:
    vals = sorted(df.loc[date_mask, filter_col].dropna().unique().tolist())
    sel_vals = st.multiselect("Select values", vals, default=vals[: min(5, len(vals))])
    value_mask = df[filter_col].isin(sel_vals) if len(sel_vals) else pd.Series(True, index=df.index)
else:
    value_mask = pd.Series(True, index=df.index)

fdf = df[date_mask & value_mask].copy()
st.caption(f"Filtered rows: **{len(fdf):,}**")

# 6) Univariate plots
st.subheader("📈 Univariate Distributions")
if len(num_cols):
    num_for_plot = st.selectbox("Numeric column for histogram", num_cols, index=0)
    fig = px.histogram(fdf, x=num_for_plot, nbins=30, title=f"Histogram of {num_for_plot}")
    st.plotly_chart(fig, use_container_width=True)

if len(cat_cols):
    cat_for_plot = st.selectbox("Categorical column for bar chart", cat_cols, index=0)
    bar = fdf[cat_for_plot].value_counts().reset_index()
    bar.columns = [cat_for_plot, "count"]
    fig = px.bar(bar, x=cat_for_plot, y="count", title=f"Counts of {cat_for_plot}")
    st.plotly_chart(fig, use_container_width=True)

# 7) Bivariate: numeric vs numeric
st.subheader("🔗 Simple Relationships")
if len(num_cols) >= 2:
    x_col = st.selectbox("X (numeric)", num_cols, index=0, key="x_scatter")
    y_col = st.selectbox("Y (numeric)", num_cols, index=1, key="y_scatter")
    fig = px.scatter(fdf, x=x_col, y=y_col, opacity=0.7, title=f"{x_col} vs {y_col}")
    st.plotly_chart(fig, use_container_width=True)

# 8) Time series (if date present)
st.subheader("🕒 Time Series (by day)")
if date_col is not None and fdf[date_col].notna().any():
    tmp = fdf.dropna(subset=[date_col]).copy()
    tmp["date_only"] = tmp[date_col].dt.date
    # pick a numeric KPI
    kpi_cols = ["net_revenue"] + [c for c in num_cols if c != "net_revenue"]
    kpi_cols = [c for c in kpi_cols if c in tmp.columns]
    if kpi_cols:
        kpi = st.selectbox("KPI to aggregate by day", kpi_cols, index=0)
        daily = tmp.groupby("date_only", as_index=False)[kpi].sum()
        fig = px.line(daily, x="date_only", y=kpi, title=f"Daily {kpi}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No numeric columns available for time series.")

# 9) Correlation (numeric)
st.subheader("🧪 Correlation (numeric)")
if len(fdf.select_dtypes(include=[np.number]).columns) >= 2:
    corr = fdf.select_dtypes(include=[np.number]).corr(numeric_only=True)
    fig = px.imshow(corr, text_auto=True, aspect="auto", title="Correlation Heatmap")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Need at least two numeric columns for correlation.")

# 10) Data preview & download
st.subheader("📄 Data Preview")
st.dataframe(fdf.head(100), use_container_width=True)
st.download_button("⬇️ Download filtered CSV", data=fdf.to_csv(index=False).encode("utf-8"), file_name="filtered_data.csv")
