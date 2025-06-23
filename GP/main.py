# main.py
import streamlit as st
import pandas as pd
import numpy as np

from heatmap_page import render_heatmap_page
from state_analysis_page import render_state_analysis_page
from national_trends_page import render_national_trends_page
from forecast_page import render_forecast_page

@st.cache_data
def load_data():
    URL_DATA = 'https://storage.dosm.gov.my/cpi/cpi_2d_state_inflation.parquet'
    df = pd.read_parquet(URL_DATA)
    df['date'] = pd.to_datetime(df['date'])
    df['price_index'] = (1 + df['inflation_mom']/100).cumprod()
    df['inflation_yoy'] = df.groupby(['state', 'division'])['price_index'].pct_change(periods=12) * 100
    return df.drop('price_index', axis=1)

# Division mappings
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

# Main driver
st.set_page_config(layout="wide", page_title="Malaysia Inflation Dashboard")
df = load_data()
df['division_name'] = df['division'].map(division_mapping).astype(str).str.strip().fillna('Unknown')

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("", ["🌡️ FDI Heatmap", "📊 State Analysis", "📈 National Trends", "🔮 Forecast"])

if page == "🌡️ FDI Heatmap":
    render_heatmap_page(df, core_divisions, division_mapping)
elif page == "📊 State Analysis":
    render_state_analysis_page(df)
elif page == "📈 National Trends":
    render_national_trends_page(df, core_divisions)
elif page == "🔮 Forecast":
    render_forecast_page(df, division_mapping)
