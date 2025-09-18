
import os
import pandas as pd
import numpy as np
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Notebook‑Style EDA", page_icon="📒", layout="wide")

st.title("📒 Notebook‑Style EDA (Beginner Friendly)")
st.write("This app mirrors a typical **Jupyter notebook EDA** flow using **pandas, numpy, seaborn/matplotlib, and streamlit**.")

# -----------------------------
# 1) Load data
# -----------------------------
st.sidebar.header("1) Load Data")
uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"], help="Upload your dataset (.csv).")
default_path = "/mnt/data/ecommerce_dataset.csv"

if uploaded is not None:
    df = pd.read_csv(uploaded)
    source = "Uploaded file"
elif os.path.exists(default_path):
    df = pd.read_csv(default_path)
    source = "Sample dataset"
else:
    st.error("No data available. Please upload a CSV.")
    st.stop()

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
        # Drop timezone info if present
        if pd.api.types.is_datetime64_any_dtype(df[date_col]):
            try:
                df[date_col] = df[date_col].dt.tz_localize(None)
            except Exception:
                try:
                    df[date_col] = df[date_col].dt.tz_convert(None)
                except Exception:
                    pass

# Identify numeric & categorical
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

# -----------------------------
# 3) Head & Info
# -----------------------------
st.header("1) Quick Look")
st.subheader("Head (first 5 rows)")
st.dataframe(df.head(), use_container_width=True)

st.subheader("Column dtypes")
st.write(df.dtypes.astype(str))

# -----------------------------
# 4) Missing values & duplicates
# -----------------------------
st.header("2) Data Quality")
c1, c2 = st.columns(2)
with c1:
    st.subheader("Missing values by column")
    miss = df.isna().sum().to_frame("missing_count")
    miss["missing_pct"] = (miss["missing_count"]/len(df)*100).round(2)
    st.dataframe(miss, use_container_width=True)
with c2:
    dup = len(df) - len(df.drop_duplicates())
    st.subheader("Duplicates")
    st.metric("Duplicate rows", f"{dup:,}")

# -----------------------------
# 5) Summary statistics
# -----------------------------
st.header("3) Summary Statistics")
if len(num_cols):
    st.subheader("Numeric columns")
    st.dataframe(df[num_cols].describe().T, use_container_width=True)
else:
    st.info("No numeric columns.")

if len(cat_cols):
    st.subheader("Categorical columns")
    # Simple freq table for first few categorical columns
    for c in cat_cols[:5]:
        st.write(f"**{c}** (top 10)")
        freq = df[c].astype(str).value_counts().head(10).to_frame("count")
        st.dataframe(freq, use_container_width=True)
else:
    st.info("No categorical columns.")

# -----------------------------
# 6) Univariate plots
# -----------------------------
st.header("4) Univariate Plots")
if len(num_cols):
    col_hist, col_box = st.columns(2)
    with col_hist:
        st.subheader("Histogram")
        num_sel = st.selectbox("Numeric column", num_cols, key="hist_sel")
        fig, ax = plt.subplots()
        sns.histplot(df[num_sel].dropna(), kde=True, ax=ax)
        ax.set_title(f"Distribution of {num_sel}")
        st.pyplot(fig, use_container_width=True)
    with col_box:
        st.subheader("Boxplot")
        num_sel2 = st.selectbox("Numeric column (boxplot)", num_cols, index=min(1, len(num_cols)-1), key="box_sel")
        fig, ax = plt.subplots()
        sns.boxplot(x=df[num_sel2], ax=ax)
        ax.set_title(f"Boxplot of {num_sel2}")
        st.pyplot(fig, use_container_width=True)

if len(cat_cols):
    st.subheader("Countplot (Top categories)")
    cat_sel = st.selectbox("Categorical column", cat_cols, key="cat_sel")
    top = df[cat_sel].astype(str).value_counts().head(15).index.tolist()
    fig, ax = plt.subplots()
    sns.countplot(data=df[df[cat_sel].astype(str).isin(top)], x=cat_sel, order=top, ax=ax)
    ax.set_title(f"Counts of {cat_sel} (top 15)")
    ax.tick_params(axis='x', rotation=45)
    st.pyplot(fig, use_container_width=True)

# -----------------------------
# 7) Bivariate plots
# -----------------------------
st.header("5) Bivariate Plots")
if len(num_cols) >= 2:
    st.subheader("Scatter")
    x_col = st.selectbox("X", num_cols, key="x_scatter")
    y_col = st.selectbox("Y", [c for c in num_cols if c != x_col], key="y_scatter")
    fig, ax = plt.subplots()
    sns.scatterplot(data=df, x=x_col, y=y_col, ax=ax)
    ax.set_title(f"{x_col} vs {y_col}")
    st.pyplot(fig, use_container_width=True)

if len(num_cols) >= 2:
    st.subheader("Correlation heatmap")
    corr = df[num_cols].corr(numeric_only=True)
    fig, ax = plt.subplots()
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="crest", ax=ax)
    ax.set_title("Correlation (numeric only)")
    st.pyplot(fig, use_container_width=True)

# -----------------------------
# 8) Time series (if date col)
# -----------------------------
st.header("6) Time Series (optional)")
if date_col and df[date_col].notna().any():
    kpi_cols = ["net_revenue"] + [c for c in num_cols if c != "net_revenue"]
    kpi_cols = [c for c in kpi_cols if c in df.columns]
    if kpi_cols:
        kpi = st.selectbox("Metric by day", kpi_cols)
        tmp = df.dropna(subset=[date_col]).copy()
        tmp["date_only"] = tmp[date_col].dt.date
        daily = tmp.groupby("date_only", as_index=False)[kpi].sum()
        fig, ax = plt.subplots()
        ax.plot(daily["date_only"], daily[kpi])
        ax.set_title(f"Daily {kpi}")
        ax.set_xlabel("Date")
        ax.set_ylabel(kpi)
        plt.xticks(rotation=45)
        st.pyplot(fig, use_container_width=True)
    else:
        st.info("Pick a date column above and ensure there is at least one numeric metric.")

# -----------------------------
# 9) Data preview & export
# -----------------------------
st.header("7) Data Preview & Export")
st.dataframe(df.head(100), use_container_width=True)
st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode("utf-8"), file_name="data_preview.csv")
