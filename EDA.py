
import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Interactive EDA • Plotly", page_icon="📈", layout="wide")

st.title("📈 Interactive EDA (Plotly)")
st.write("Beginner-friendly EDA using **pandas**, **numpy**, **plotly**, and **streamlit** with full-width, interactive charts.")

# -----------------------------
# 1) Load data
# -----------------------------
st.sidebar.header("1) Load Data")
uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])

def load_default():
    default_path = "/mnt/data/ecommerce_dataset.csv"
    if os.path.exists(default_path):
        return pd.read_csv(default_path)
    st.error("No file uploaded and sample dataset not found.")
    st.stop()

if uploaded is not None:
    df = pd.read_csv(uploaded)
    source = "Uploaded file"
else:
    df = load_default()
    source = "Sample dataset"

st.caption(f"Data source: **{source}**  •  Rows: **{len(df):,}**, Cols: **{df.shape[1]}**")

# -----------------------------
# 2) Light typing
# -----------------------------
with st.expander("Optional: parse a date column"):
    date_guess = next((c for c in df.columns if "date" in c.lower()), None)
    date_col = st.selectbox("Pick a date column (optional)", [None] + df.columns.tolist(),
                            index=(df.columns.get_loc(date_guess)+1) if date_guess in df.columns else 0)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        if pd.api.types.is_datetime64_any_dtype(df[date_col]):
            try:
                df[date_col] = df[date_col].dt.tz_localize(None)
            except Exception:
                try:
                    df[date_col] = df[date_col].dt.tz_convert(None)
                except Exception:
                    pass

num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

# Optional simple derived metric if present
with st.expander("Optional: create Net Revenue"):
    qty_guess = "quantity" if "quantity" in df.columns else None
    price_guess = "price" if "price" in df.columns else None
    disc_guess = "discount" if "discount" in df.columns else None
    qty_col = st.selectbox("Quantity column", [None] + df.columns.tolist(), index=(df.columns.get_loc(qty_guess)+1) if qty_guess else 0)
    price_col = st.selectbox("Price column", [None] + df.columns.tolist(), index=(df.columns.get_loc(price_guess)+1) if price_guess else 0)
    disc_col = st.selectbox("Discount column (0–1 or 0–100)", [None] + df.columns.tolist(), index=(df.columns.get_loc(disc_guess)+1) if disc_guess else 0)
    if qty_col and price_col:
        gross = pd.to_numeric(df[qty_col], errors="coerce") * pd.to_numeric(df[price_col], errors="coerce")
        if disc_col:
            disc = pd.to_numeric(df[disc_col], errors="coerce")
            disc = np.where(disc > 1, disc/100.0, disc)
        else:
            disc = 0.0
        df["net_revenue"] = gross * (1 - disc)
        if "net_revenue" not in num_cols:
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        st.success("Created **net_revenue** column")

# -----------------------------
# 3) Filters
# -----------------------------
st.header("🔎 Filters")
if date_col and df[date_col].notna().any():
    mind = df[date_col].min().date()
    maxd = df[date_col].max().date()
    start, end = st.date_input("Date range", value=(mind, maxd), min_value=mind, max_value=maxd)
    if isinstance(start, tuple) or isinstance(start, list):
        start, end = start
    date_mask = df[date_col].dt.date.between(start, end)
else:
    date_mask = pd.Series(True, index=df.index)

filter_col = st.selectbox("Pick a column to filter values (optional)", [None] + df.columns.tolist())
if filter_col:
    vals = df.loc[date_mask, filter_col].dropna().astype(str).value_counts().head(50).index.tolist()
    sel_vals = st.multiselect("Select values", vals, default=vals[: min(10, len(vals))])
    value_mask = df[filter_col].astype(str).isin(sel_vals) if len(sel_vals) else pd.Series(True, index=df.index)
else:
    value_mask = pd.Series(True, index=df.index)

fdf = df[date_mask & value_mask].copy()
st.caption(f"Filtered rows: **{len(fdf):,}**")

# Common layout helper
def full_width(fig):
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# 4) Overview KPIs
# -----------------------------
st.header("📊 Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{len(fdf):,}")
c2.metric("Numeric cols", f"{len(num_cols)}")
c3.metric("Categorical cols", f"{len(cat_cols)}")
c4.metric("Missing cells", f"{int(fdf.isna().sum().sum()):,}")

with st.expander("Missing values by column"):
    miss = fdf.isna().sum().to_frame("missing_count")
    miss["missing_pct"] = (miss["missing_count"]/len(fdf)*100).round(2)
    st.dataframe(miss, use_container_width=True)

# -----------------------------
# 5) Univariate
# -----------------------------
st.header("📈 Univariate Distributions")
cols = st.columns(2)

if len(num_cols):
    with cols[0]:
        num_sel = st.selectbox("Numeric column (histogram)", num_cols, key="hist_col")
        fig = px.histogram(fdf, x=num_sel, nbins=40, title=f"Distribution of {num_sel}", opacity=0.9)
        fig.update_traces(hovertemplate=f"{num_sel}: "+"%{x}<br>Count: %{y}<extra></extra>")
        full_width(fig)

    with cols[1]:
        num_sel2 = st.selectbox("Numeric column (box)", num_cols, index=min(1, len(num_cols)-1), key="box_col")
        fig = px.box(fdf, y=num_sel2, points="suspectedoutliers", title=f"Boxplot of {num_sel2}")
        fig.update_traces(hovertemplate=f"{num_sel2}: "+"%{y}<extra></extra>")
        full_width(fig)
else:
    st.info("No numeric columns to plot.")

if len(cat_cols):
    cat_sel = st.selectbox("Categorical column (top 20)", cat_cols, key="cat_bar")
    bar = fdf[cat_sel].astype(str).value_counts().head(20).reset_index()
    bar.columns = [cat_sel, "count"]
    fig = px.bar(bar, x=cat_sel, y="count", title=f"Top {cat_sel} (by count)")
    fig.update_traces(hovertemplate=f"{cat_sel}: "+"%{x}<br>Count: %{y}<extra></extra>", textauto=True)
    fig.update_layout(xaxis=dict(tickangle=45))
    full_width(fig)

# -----------------------------
# 6) Bivariate
# -----------------------------
st.header("🔗 Relationships")
if len(num_cols) >= 2:
    x = st.selectbox("X (numeric)", num_cols, key="x_sc")
    y_options = [c for c in num_cols if c != x]
    y = st.selectbox("Y (numeric)", y_options, key="y_sc")
    color = st.selectbox("Color (optional)", [None] + cat_cols, key="color_sc")
    fig = px.scatter(fdf, x=x, y=y, color=color, opacity=0.7, title=f"{x} vs {y}", hover_data=cat_cols[:3])
    fig.update_traces(hovertemplate=f"{x}: "+"%{x}<br>"+f"{y}: "+"%{y}"+"<extra></extra>")
    full_width(fig)

# -----------------------------
# 7) Time Series
# -----------------------------
st.header("🕒 Time Series")
if date_col and fdf[date_col].notna().any() and len(num_cols):
    tmp = fdf.dropna(subset=[date_col]).copy()
    tmp["date_only"] = tmp[date_col].dt.date
    kpi_candidates = ["net_revenue"] + [c for c in num_cols if c != "net_revenue"]
    kpi_candidates = [c for c in kpi_candidates if c in tmp.columns]
    kpi = st.selectbox("Metric to sum by day", kpi_candidates, key="ts_metric")
    daily = tmp.groupby("date_only", as_index=False)[kpi].sum()
    fig = px.line(daily, x="date_only", y=kpi, markers=True, title=f"Daily {kpi}")
    fig.update_traces(hovertemplate="Date: %{x}<br>"+f"{kpi}: "+"%{y}<extra></extra>")
    full_width(fig)
else:
    st.info("Select a date column and ensure there’s at least one numeric column.")

# -----------------------------
# 8) Category & Region Examples (if present)
# -----------------------------
st.header("🏷️ Category & Grouped Views")
# Auto-detect common e‑commerce columns but keep generic
cat_like_cols = [c for c in ["category","region","payment_method"] if c in fdf.columns]
metric_options = ["net_revenue"] + [c for c in num_cols if c != "net_revenue"]
metric_options = [m for m in metric_options if m in fdf.columns]

if cat_like_cols and metric_options:
    group_col = st.selectbox("Group by", cat_like_cols, key="group_by")
    metric = st.selectbox("Metric (sum)", metric_options, key="group_metric")
    grouped = fdf.groupby(group_col, as_index=False)[metric].sum().sort_values(metric, ascending=False)
    fig = px.bar(grouped, x=group_col, y=metric, title=f"{metric} by {group_col}", text_auto=True)
    fig.update_traces(hovertemplate=f"{group_col}: "+"%{x}<br>"+f"{metric}: "+"%{y}<extra></extra>")
    full_width(fig)
else:
    st.caption("Tip: If your dataset has columns like **category, region, payment_method**, you’ll see grouped bars here.")

# -----------------------------
# 9) Correlation
# -----------------------------
st.header("🧪 Correlation (numeric)")
num_only = fdf.select_dtypes(include=[np.number])
if num_only.shape[1] >= 2:
    corr = num_only.corr(numeric_only=True)
    fig = px.imshow(corr, text_auto=True, aspect="auto", title="Correlation Heatmap")
    full_width(fig)
else:
    st.info("Need at least two numeric columns for correlation.")

# -----------------------------
# 10) Data Preview & Export
# -----------------------------
st.header("📄 Data Preview & Export")
st.dataframe(fdf.head(200), use_container_width=True)
st.download_button("⬇️ Download filtered CSV", data=fdf.to_csv(index=False).encode("utf-8"), file_name="filtered_data.csv")
