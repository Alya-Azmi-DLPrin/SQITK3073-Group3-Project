# data_view_forecast_page.py
import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data
def load_data():
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

    return df

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

def render_data_view_forecast_page():
    df = load_data()
    df['division_name'] = df['division'].map(division_mapping)

    page = st.sidebar.radio("📄 Select Page", ["📊 Data View", "🔮 Forecast"])

    division_names = df['division_name'].dropna().unique()
    selected_division_name = st.sidebar.selectbox("Select Division", sorted(division_names))

    selected_division_code = [k for k, v in division_mapping.items() if v == selected_division_name][0]
    states = df[df['division'] == selected_division_code]['state'].unique()
    selected_state = st.sidebar.selectbox("Select State", sorted(states))

    state_df = df[(df['division'] == selected_division_code) & (df['state'] == selected_state)].copy()
    state_df = state_df.sort_values('date')

    if page == "📊 Data View":
        st.subheader("📊 Inflation Data View")
        min_date = state_df['date'].min()
        max_date = state_df['date'].max()
        start_date, end_date = st.sidebar.date_input("Select Date Range", (min_date, max_date), min_value=min_date, max_value=max_date)

        filtered_df = state_df[(state_df['date'] >= pd.to_datetime(start_date)) & (state_df['date'] <= pd.to_datetime(end_date))]

        if not filtered_df.empty:
            latest_row = filtered_df.iloc[-1]
            st.write(f"**Date:** {latest_row['date'].strftime('%Y-%m-%d')}")
            st.write(f"**MoM Inflation:** {latest_row['inflation_mom']:.4f}%")
            st.write(f"**YoY Inflation:** {latest_row['inflation_yoy']:.4f}%")

            st.line_chart(filtered_df.set_index('date')[['inflation_mom']])

            stats = filtered_df['inflation_mom'].describe().to_frame().T
            st.subheader("📊 Summary Statistics")
            st.dataframe(stats.style.format("{:.4f}"))
        else:
            st.warning("No data for selected range.")

    elif page == "🔮 Forecast":
        st.subheader("🔮 Forecast - Next 6 Months")

        if len(state_df) >= 6:
            state_df['t'] = np.arange(len(state_df))
            X = state_df['t'].values
            y = state_df['inflation_mom'].values
            a, b = np.polyfit(X, y, deg=1)

            future_t = np.arange(len(X), len(X) + 6)
            future_pred = a * future_t + b
            last_date = state_df['date'].iloc[-1]
            future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=6, freq='MS')

            forecast_df = pd.DataFrame({'date': future_dates, 'inflation_mom': future_pred})
            combined_df = pd.concat([state_df[['date', 'inflation_mom']], forecast_df]).set_index('date')

            st.line_chart(combined_df)

            st.dataframe(pd.DataFrame({
                'Date': future_dates.strftime('%Y-%m'),
                'Predicted Inflation MoM (%)': future_pred
            }).style.format({"Predicted Inflation MoM (%)": "{:.4f}"}))
        else:
            st.warning("Not enough data for forecast.")
