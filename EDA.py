import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Simple EDA", page_icon="📊", layout="wide")
st.title("📊 Simple EDA App (Beginner Friendly)")

# 1) Load data
st.sidebar.header("Load Data")
uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])
default_path = "/mnt/data/ecommerce_dataset.csv"

if uploaded is not None:
    df = pd.read_csv(uploaded)
    source = "Uploaded file"
elif os.path.exists(default_path):
    df = pd.read_csv(default_path)
    source = "Sample dataset"
else:
    st.error("No CSV found. Please upload one.")
    st.stop()

st.caption(f"Data source: **{source}**  |  Rows: {len(df)}, Cols: {df.shape[1]}")

# 2) Show head and info
st.subheader("👀 Quick Look at Data")
st.dataframe(df.head())

st.subheader("ℹ️ Dataset Info")
st.write(df.dtypes.astype(str))
st.write(df.describe(include="all").T)

# 3) Numeric and categorical columns
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

# 4) Histogram
if len(num_cols):
    st.subheader("📈 Histogram")
    num_sel = st.selectbox("Pick numeric column", num_cols)
    fig = px.histogram(df, x=num_sel, nbins=30, title=f"Distribution of {num_sel}")
    st.plotly_chart(fig, use_container_width=True)

# 5) Boxplot
if len(num_cols):
    st.subheader("📦 Boxplot")
    num_sel2 = st.selectbox("Pick numeric column (boxplot)", num_cols, index=min(1, len(num_cols)-1))
    fig = px.box(df, y=num_sel2, title=f"Boxplot of {num_sel2}")
    st.plotly_chart(fig, use_container_width=True)

# 6) Bar chart (categorical)
if len(cat_cols):
    st.subheader("🏷️ Bar Chart (Categorical)")
    cat_sel = st.selectbox("Pick categorical column", cat_cols)
    counts = df[cat_sel].astype(str).value_counts().reset_index()
    counts.columns = [cat_sel, "count"]
    fig = px.bar(counts, x=cat_sel, y="count", title=f"Counts of {cat_sel}", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

# 7) Scatter plot
if len(num_cols) >= 2:
    st.subheader("🔗 Scatter Plot")
    x = st.selectbox("X axis", num_cols, key="x_scatter")
    y_options = [c for c in num_cols if c != x]
    y = st.selectbox("Y axis", y_options, key="y_scatter")
    fig = px.scatter(df, x=x, y=y, title=f"{x} vs {y}", opacity=0.7)
    st.plotly_chart(fig, use_container_width=True)
