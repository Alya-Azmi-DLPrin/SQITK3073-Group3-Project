# main.py
import streamlit as st
import pandas as pd
import numpy as np

from heatmap_page import render_heatmap_page
from state_analysis_page import render_state_analysis_page
from national_trends_page import render_national_trends_page
from data_view_forecast_page import render_data_view_forecast_page  # Includes View & Forecast

@st.cache_data
def load_data():
    URL_DATA = 'https://storage.dosm.gov.my/cpi/cpi_2d_state_inflation.parquet'
    df = pd.read_parquet(URL_DATA)
    df['date'] = pd.to_datetime(df['date'])
    df['price_index'] = (1 + df['inflation_mom'] / 100).cumprod()
    df['inflation_yoy'] = df.groupby(['state', 'division'])['price_index'].pct_change(periods=12) * 100
    return df.drop('price_index', axis=1)

division_mapping = {
    '01': 'Food & Beverages',
    '02': 'Alcoholic Beverages & Tobacco',
    '03': 'Clothing & Footwear',
    '04': 'Housing, Utilities, Gas & Other Fuels',
    '05': 'Household Furnishings, Equipment & Maintenance',
    '06': 'Health',
    '07': 'Transport',
    '08': 'Information & Communication',
    '09': 'Recreation, Sport & Culture',
    '10': 'Education',
    '11': 'Restaurant & Accommodation Services',
    '12': 'Insurance & Financial Services',
    '13': 'Personal Care, Social Protection & Miscellaneous Goods and Services'
}

core_divisions = ['03', '05', '06', '08', '09', '10', '12']

st.set_page_config(layout="wide", page_title="Malaysia Cost Intelligence Dashboard")

df = load_data()
df['division_name'] = df['division'].map(division_mapping).astype(str).str.strip().fillna('Unknown')

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "",
    [
        "🏠 Welcome",
        "🧪 Data View & Forecast",
        "📊 State Analysis",
        "📈 National Trends",
        "🌡️ FDI Heatmap"
    ]
)

# Page Routing
if page == "🏠 Welcome":
    st.markdown("<h1 style='text-align: center;'>🇲🇾 Malaysia Cost Intelligence Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; font-size: 18px;'>
        Welcome! This interactive dashboard provides a deep dive into the cost-of-living trends across Malaysia.<br>
        Explore inflation by state and sector, discover national patterns, and visualize FDI dynamics.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.subheader("🔍 Features at a Glance")
    st.markdown("""
    - 📊 **Data View & Forecast**: View monthly and yearly inflation by state and category with trend projections  
    - 🧭 **State Analysis**: Dive into how inflation impacts each Malaysian state  
    - 📈 **National Trends**: Compare inflation trends at the national level  
    - 🌍 **FDI Heatmap**: Visualize Foreign Direct Investment across regions
    """)

    st.markdown("---")
    st.markdown("<div style='text-align: center; font-size: 14px; color: gray;'>Crafted with ❤️ for data insights</div>", unsafe_allow_html=True)

elif page == "🧪 Data View & Forecast":
    st.title("Malaysia Cost Intelligence Dashboard")
    render_data_view_forecast_page()
elif page == "📊 State Analysis":
    render_state_analysis_page(df)
elif page == "📈 National Trends":
    render_national_trends_page(df, core_divisions)
elif page == "🌡️ FDI Heatmap":
    render_heatmap_page(df, core_divisions, division_mapping)
