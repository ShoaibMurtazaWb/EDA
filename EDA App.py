
import os
import io
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="🛒 Ecommerce — Assignment 2 Style (Streamlit)", page_icon="🛒", layout="wide")

st.title("🛒 Ecommerce Dataset — Assignment 2 Style Analysis (Streamlit)")

st.sidebar.header("Load Data")
uploaded = st.sidebar.file_uploader("Upload CSV (optional)", type=["csv"])
default_path = "/mnt/data/ecommerce_dataset.csv"

if uploaded is not None:
    df = pd.read_csv(uploaded)
    source = "Uploaded file"
elif os.path.exists(default_path):
    df = pd.read_csv(default_path)
    source = "Default ecommerce_dataset.csv"
else:
    st.error("No dataset found. Please upload a CSV.")
    st.stop()

if "order_date" in df.columns:
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

st.caption(f"Data source: **{source}** • Shape: **{df.shape}**")

st.header("1) Dataset Info")
buffer = io.StringIO()
df.info(buf=buffer)
st.text(buffer.getvalue())

st.header("2) Summary Statistics (include='all')")
st.dataframe(df.describe(include='all').transpose(), use_container_width=True)

st.header("3) Data Quality Checks")
c1, c2 = st.columns(2)
with c1:
    st.subheader("Missing values per column")
    miss = df.isna().sum().to_frame("missing_count")
    miss["missing_pct"] = (miss["missing_count"] / len(df) * 100).round(2)
    st.dataframe(miss, use_container_width=True)
with c2:
    dup_count = len(df) - len(df.drop_duplicates())
    st.subheader("Duplicates")
    st.metric("Duplicate rows", f"{dup_count:,}")

st.markdown("### Note: Excluding identifier columns from numeric analysis (`order_id`, `customer_id`, `product_id`).")
id_cols = [c for c in ["order_id","customer_id","product_id"] if c in df.columns]
num_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in id_cols]
cat_cols = [c for c in df.select_dtypes(exclude=[np.number]).columns if c not in id_cols and c != "order_date"]

st.caption(f"Numeric columns used: {num_cols}")
st.caption(f"Categorical columns used: {cat_cols}")

st.header("4) Univariate — Numeric Columns")
if len(num_cols):
    for col in num_cols:
        st.subheader(f"Distribution of {col}")
        fig = px.histogram(df, x=col, nbins=30, title=f"Distribution of {col}", marginal="box")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No numeric columns to plot (after excluding ID columns).")

st.header("5) Univariate — Categorical Columns")
if len(cat_cols):
    for col in cat_cols:
        st.subheader(f"Counts of {col}")
        counts = df[col].astype(str).value_counts().reset_index()
        counts.columns = [col, "count"]
        fig = px.bar(counts, x=col, y="count", title=f"Counts of {col}", text_auto=True)
        fig.update_layout(xaxis=dict(tickangle=45))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No categorical columns to plot.")

st.header("6) Bivariate — Price vs Discount by Category")
if set(["price","discount"]).issubset(df.columns):
    color_col = "category" if "category" in df.columns else None
    fig = px.scatter(df, x="discount", y="price", color=color_col, opacity=0.6,
                     title="Price vs Discount" + ("" if color_col is None else " by Category"))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("Requires `price` and `discount` columns.")

if set(["quantity","price"]).issubset(df.columns):
    discount = df["discount"] if "discount" in df.columns else 0.0
    discount = pd.to_numeric(discount, errors="coerce").fillna(0.0)
    discount = np.where(discount > 1, discount/100.0, discount)
    df["net_revenue"] = pd.to_numeric(df["quantity"], errors="coerce") * pd.to_numeric(df["price"], errors="coerce") * (1 - discount)
    st.success("Computed `net_revenue = quantity * price * (1 - discount)`")
else:
    st.warning("`quantity` and `price` required to compute `net_revenue`.")

st.header("7) Revenue by Groups")
if "net_revenue" in df.columns:
    if "category" in df.columns:
        cat_rev = df.groupby("category", as_index=False)["net_revenue"].sum().sort_values("net_revenue", ascending=False)
        fig = px.bar(cat_rev, x="category", y="net_revenue", title="Total Revenue by Category", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)
    if "region" in df.columns:
        reg_rev = df.groupby("region", as_index=False)["net_revenue"].sum().sort_values("net_revenue", ascending=False)
        fig = px.bar(reg_rev, x="region", y="net_revenue", title="Total Revenue by Region", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)
    if "payment_method" in df.columns:
        pay_cnt = df["payment_method"].value_counts().reset_index()
        pay_cnt.columns = ["payment_method","count"]
        fig = px.pie(pay_cnt, names="payment_method", values="count", title="Payment Method Distribution", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("Revenue charts need `net_revenue`.")

st.header("8) Time Series — Daily Net Revenue")
if "order_date" in df.columns and "net_revenue" in df.columns:
    daily = df.groupby(df["order_date"].dt.date)["net_revenue"].sum().reset_index()
    daily.columns = ["order_date","net_revenue"]
    fig = px.line(daily, x="order_date", y="net_revenue", markers=True, title="Daily Net Revenue")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("Requires `order_date` and computed `net_revenue`.")

st.header("9) Correlation Heatmap")
if len(num_cols):
    use_cols = list(dict.fromkeys(num_cols + (["net_revenue"] if "net_revenue" in df.columns else [])))
    if len(use_cols) >= 2:
        corr = df[use_cols].corr(numeric_only=True)
        fig = px.imshow(corr, text_auto=True, aspect="auto", title="Correlation Heatmap")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Need at least two numeric columns for correlation.")
else:
    st.caption("No numeric columns for correlation.")

st.header("10) Data Preview & Export")
st.dataframe(df.head(200), use_container_width=True)
st.download_button("⬇️ Download CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="ecommerce_analysis_output.csv")
