import streamlit as st
import pandas as pd
import numpy as np

from heatmap_page import render_heatmap_page
from national_trends_page import render_national_trends_page
from data_view_forecast_page import render_data_view_forecast_page

@st.cache_data
def fetch_cpi_data():
    try:
        url = "https://storage.dosm.gov.my/cpi/cpi_2d_state_inflation.csv"
        df = pd.read_csv(url)

        rename_map = {
            'ref_area': 'state',
            'coicop': 'division',
            'inflation_m-o-m': 'inflation_mom',
            'inflation_y-o-y': 'inflation_yoy'
        }
        df = df.rename(columns=rename_map)

        df['inflation_mom'] = pd.to_numeric(df['inflation_mom'], errors='coerce')
        df['inflation_yoy'] = pd.to_numeric(df['inflation_yoy'], errors='coerce')
        df['date'] = pd.to_datetime(df['date'])

        st.success("✅ CPI data successfully loaded.")
        return df

    except Exception as e:
        st.error(f"❌ Failed to fetch CPI data. Error: {e}")
        return pd.DataFrame()

# Mapping
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

# Config
st.set_page_config(layout="wide", page_title="Malaysia Cost Intelligence Dashboard")

# Load data
df = fetch_cpi_data()

# Show API status
if not df.empty:
    st.sidebar.info(f"📡 API data: {len(df)} rows loaded")
else:
    st.sidebar.error("❌ No data loaded from API.")

# Add readable division names
if 'division' in df.columns:
    df['division_name'] = df['division'].map(division_mapping).astype(str).str.strip().fillna('Unknown')
else:
    st.error("🛑 Column 'division' missing in dataset.")
    st.stop()

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "",
    [
        "🏠 Welcome",
        "🧪 Data View & Forecast",
        "📈 National Trends",
        "🌡️ FDI Heatmap"
    ]
)

# Page routing
if page == "🏠 Welcome":
    st.markdown("<h1 style='text-align: center;'>🇲🇾 Malaysia Cost Intelligence Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; font-size: 18px;'>
        Welcome! This dashboard helps you explore inflation across Malaysia by state and category.<br>
        View trends, generate forecasts, and understand inflation patterns interactively.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("🔎 Key Features:")
    st.markdown("""
    - 🧪 **Data View & Forecast**  
    - 📈 **National Trends**  
    - 🌡️ **FDI Heatmap**
    """)
    st.markdown("---")
    st.markdown("<div style='text-align: center; font-size: 14px; color: gray;'>Powered by DOSM - Department of Statistics Malaysia</div>", unsafe_allow_html=True)

elif page == "🧪 Data View & Forecast":
    render_data_view_forecast_page()

elif page == "📈 National Trends":
    render_national_trends_page(df, core_divisions)

elif page == "🌡️ FDI Heatmap":
    render_heatmap_page(df, core_divisions, division_mapping)
