
import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Assignment 2 • Ecommerce EDA", page_icon="🛒", layout="wide")

st.title("🛒 Assignment 2 — Ecommerce Dataset EDA")
st.markdown(
    """
    **About this dataset**  
    This dataset represents synthetic e‑commerce **orders**. Each row is an order record with:
    - **Identifier columns**: `order_id`, `customer_id`, `product_id` (unique IDs; not used for analysis).
    - **Product/category info**: `category`.
    - **Order details**: `quantity`, `price`, and `discount` (as a fraction like 0.15 for 15% in this sample).
    - **When/where/how**: `order_date`, `region`, and `payment_method`.

    **Goal of this EDA**  
    Provide a **beginner‑friendly** overview: understand distributions (price, quantity, discount),
    compare groups (category/region/payment), examine **revenue** patterns over time,
    and look at simple relationships between numeric columns.
    """
)

st.sidebar.header("Load Data")
uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"], help="Optional: upload your own CSV.")
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
    if pd.api.types.is_datetime64_any_dtype(df["order_date"]):
        try:
            df["order_date"] = df["order_date"].dt.tz_localize(None)
        except Exception:
            try:
                df["order_date"] = df["order_date"].dt.tz_convert(None)
            except Exception:
                pass

st.caption(f"Data source: **{source}** • Rows: **{len(df):,}** • Columns: **{df.shape[1]}**")

# Overview
st.header("1) Data Overview")
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Preview")
    st.dataframe(df.head(), use_container_width=True)
with col_b:
    st.subheader("Dtypes & Summary")
    st.write(df.dtypes.astype(str))
    st.write(df.describe(include='all').transpose())

st.subheader("Data Quality")
c1, c2, c3 = st.columns(3)
c1.metric("Rows", f"{len(df):,}")
c2.metric("Missing cells", f"{int(df.isna().sum().sum()):,}")
dup_count = len(df) - len(df.drop_duplicates())
c3.metric("Duplicate rows", f"{dup_count:,}")
with st.expander("Missing values by column"):
    miss = df.isna().sum().to_frame("missing_count")
    miss["missing_pct"] = (miss["missing_count"]/len(df)*100).round(2)
    st.dataframe(miss, use_container_width=True)

id_cols = [c for c in ["order_id","customer_id","product_id"] if c in df.columns]
num_cols_all = df.select_dtypes(include=[np.number]).columns.tolist()
num_cols = [c for c in num_cols_all if c not in id_cols]
cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
if "order_date" in cat_cols:
    cat_cols.remove("order_date")

if set(["quantity","price"]).issubset(df.columns):
    discount = df["discount"] if "discount" in df.columns else 0.0
    discount = pd.to_numeric(discount, errors="coerce").fillna(0.0)
    discount = np.where(discount > 1, discount/100.0, discount)
    df["net_revenue"] = pd.to_numeric(df["quantity"], errors="coerce") * pd.to_numeric(df["price"], errors="coerce") * (1 - discount)
    if "net_revenue" not in num_cols:
        num_cols = df.select_dtypes(include=[np.number]).columns.difference(id_cols).tolist()

st.header("2) Univariate Analysis")
if len(num_cols):
    st.subheader("Numeric Distributions")
    col1, col2 = st.columns(2)
    with col1:
        num_sel = st.selectbox("Histogram column", num_cols, index=0, key="hist_col")
        fig = px.histogram(df, x=num_sel, nbins=40, title=f"Distribution of {num_sel}", opacity=0.9)
        fig.update_traces(hovertemplate=f"{num_sel}: "+"%{x}<br>Count: %{y}<extra></extra>")
        fig.update_layout(margin=dict(l=10,r=10,t=50,b=10))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        num_sel2 = st.selectbox("Boxplot column", num_cols, index=min(1, len(num_cols)-1), key="box_col")
        fig = px.box(df, y=num_sel2, points="suspectedoutliers", title=f"Boxplot of {num_sel2}")
        fig.update_traces(hovertemplate=f"{num_sel2}: "+"%{y}<extra></extra>")
        fig.update_layout(margin=dict(l=10,r=10,t=50,b=10))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No numeric columns available (excluding ID columns).")

if len(cat_cols):
    st.subheader("Categorical Counts")
    cat_sel = st.selectbox("Categorical column", cat_cols, key="cat_bar")
    counts = df[cat_sel].astype(str).value_counts().head(20).reset_index()
    counts.columns = [cat_sel, "count"]
    fig = px.bar(counts, x=cat_sel, y="count", title=f"Top {cat_sel} (by count)", text_auto=True)
    fig.update_traces(hovertemplate=f"{cat_sel}: "+"%{x}<br>Count: %{y}<extra></extra>")
    fig.update_layout(xaxis=dict(tickangle=45), margin=dict(l=10,r=10,t=50,b=10))
    st.plotly_chart(fig, use_container_width=True)

st.header("3) Relationships")
if len(num_cols) >= 2:
    x = st.selectbox("X (numeric)", num_cols, key="x_scatter")
    y_opts = [c for c in num_cols if c != x]
    y = st.selectbox("Y (numeric)", y_opts, key="y_scatter")
    color = st.selectbox("Color (optional)", [None] + cat_cols, key="color_scatter")
    fig = px.scatter(df, x=x, y=y, color=color, opacity=0.7, title=f"{x} vs {y}", hover_data=cat_cols[:3])
    fig.update_traces(hovertemplate=f"{x}: "+"%{x}<br>"+f"{y}: "+"%{y}<extra></extra>")
    fig.update_layout(margin=dict(l=10,r=10,t=50,b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("Provide at least two numeric columns to see a scatter plot.")

st.header("4) Revenue Breakdowns")
metric = "net_revenue" if "net_revenue" in df.columns else None
group_cands = [c for c in ["category","region","payment_method"] if c in df.columns]
if metric and group_cands:
    grp = st.selectbox("Group by", group_cands, key="group_by")
    grouped = df.groupby(grp, as_index=False)[metric].sum().sort_values(metric, ascending=False)
    fig = px.bar(grouped, x=grp, y=metric, title=f"{metric} by {grp}", text_auto=True)
    fig.update_traces(hovertemplate=f"{grp}: "+"%{x}<br>"+f"{metric}: "+"%{y}<extra></extra>")
    fig.update_layout(xaxis=dict(tickangle=0), margin=dict(l=10,r=10,t=50,b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("Revenue breakdowns appear when `quantity`, `price` (and optional `discount`) exist.")

st.header("5) Time Series (Daily)")
if "order_date" in df.columns and df["order_date"].notna().any() and metric:
    tmp = df.dropna(subset=["order_date"]).copy()
    tmp["date_only"] = tmp["order_date"].dt.date
    daily = tmp.groupby("date_only", as_index=False)[metric].sum()
    fig = px.line(daily, x="date_only", y=metric, markers=True, title=f"Daily {metric}")
    fig.update_traces(hovertemplate="Date: %{x}<br>"+f"{metric}: "+"%{y}<extra></extra>")
    fig.update_layout(margin=dict(l=10,r=10,t=50,b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("Provide a valid `order_date` to see a daily trend.")

st.header("6) Correlation (Numeric)")
num_only = df.select_dtypes(include=[np.number]).drop(columns=id_cols, errors="ignore")
if num_only.shape[1] >= 2:
    corr = num_only.corr(numeric_only=True)
    fig = px.imshow(corr, text_auto=True, aspect="auto", title="Correlation Heatmap")
    fig.update_layout(margin=dict(l=10,r=10,t=50,b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("Need at least two numeric columns for correlation.")

st.header("7) Data Preview & Export")
st.dataframe(df.head(200), use_container_width=True)
st.download_button("⬇️ Download CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="ecommerce_filtered.csv")
