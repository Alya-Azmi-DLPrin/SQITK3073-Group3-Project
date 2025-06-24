# data_view_forecast_page.py
import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data
def load_data():
    URL_DATA = 'https://storage.dosm.gov.my/cpi/cpi_2d_state_inflation.parquet'
    df = pd.read_parquet(URL_DATA)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    # Compute YoY if not present
    if 'inflation_yoy' not in df.columns:
        df = df.sort_values(['state', 'division', 'date'])
        df['inflation_yoy'] = df.groupby(['state', 'division'])['inflation_mom'].transform(lambda x: x.pct_change(periods=12) * 100)

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

def render_forecast_page(df, division_mapping):
    st.title("🔮 Forecast Inflation (6 Months)")
    st.markdown("### Instructions:\nSelect a division and state to forecast inflation using linear trend.")

    division_names = df['division_name'].dropna().unique()
    selected_division_name = st.selectbox("Select Division", sorted(division_names))
    selected_division_code = [k for k, v in division_mapping.items() if v == selected_division_name][0]
    states = df[df['division'] == selected_division_code]['state'].unique()
    selected_state = st.selectbox("Select State", sorted(states))

    state_df = df[(df['division'] == selected_division_code) & (df['state'] == selected_state)].sort_values('date')

    if len(state_df) >= 6:
        state_df['t'] = np.arange(len(state_df))
        X = state_df['t'].values
        y = state_df['inflation_mom'].values
        a, b = np.polyfit(X, y, deg=1)
        future_t = np.arange(len(X), len(X) + 6)
        future_pred = a * future_t + b

        future_dates = pd.date_range(start=state_df['date'].iloc[-1] + pd.DateOffset(months=1), periods=6, freq='MS')
        forecast_df = pd.DataFrame({'date': future_dates, 'inflation_mom': future_pred})
        combined_df = pd.concat([state_df[['date', 'inflation_mom']], forecast_df]).set_index('date')

        st.subheader("📈 Forecast + History")
        st.line_chart(combined_df)

        st.subheader("📅 Forecast Table")
        st.dataframe(pd.DataFrame({
            'Date': future_dates.strftime('%Y-%m'),
            'Predicted Inflation MoM (%)': future_pred
        }).style.format({"Predicted Inflation MoM (%)": "{:.4f}"}))
    else:
        st.warning("Not enough data to generate forecast.")

def render_data_view_forecast_page():
    df = load_data()
    df['division_name'] = df['division'].map(division_mapping)

    page = st.sidebar.radio("📄 Select Page", ["📊 Data View", "🔮 Forecast"])

    if page == "📊 Data View":
        division_names = df['division_name'].dropna().unique()
        selected_division_name = st.sidebar.selectbox("Select Division", sorted(division_names))
        selected_division_code = [k for k, v in division_mapping.items() if v == selected_division_name][0]
        states = df[df['division'] == selected_division_code]['state'].unique()
        selected_state = st.sidebar.selectbox("Select State", sorted(states))

        state_df = df[(df['division'] == selected_division_code) & (df['state'] == selected_state)].copy()
        state_df = state_df.sort_values('date')

        st.title("📊 Inflation Rate Dashboard - Data View")
        st.markdown("""
        Explore **month-over-month (MoM)** and **year-over-year (YoY)** inflation trends by Malaysian states and divisions.  
        Use the filters on the left to select a **division** and **state**, and narrow down by **date** range.
        """)

        min_date = state_df['date'].min()
        max_date = state_df['date'].max()
        start_date, end_date = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        filtered_df = state_df[
            (state_df['date'] >= pd.to_datetime(start_date)) &
            (state_df['date'] <= pd.to_datetime(end_date))
        ]

        if not filtered_df.empty:
            latest_row = filtered_df.iloc[-1]
            st.subheader(f"Latest Inflation Data for {selected_state} - {selected_division_name}")
            st.write(f"**Date:** {latest_row['date'].strftime('%Y-%m-%d')}")
            st.write(f"**MoM Inflation:** {latest_row['inflation_mom']:.4f}%")
            if not pd.isna(latest_row.get('inflation_yoy')):
                st.write(f"**YoY Inflation:** {latest_row['inflation_yoy']:.4f}%")
            st.caption("MoM = Month-over-Month, YoY = Year-over-Year inflation change.")

            chart_cols = ['inflation_mom']
            if 'inflation_yoy' in filtered_df.columns:
                chart_cols.append('inflation_yoy')
            dynamic_chart_df = filtered_df[['date'] + chart_cols].set_index('date')
            st.subheader("📈 Interactive Inflation Trend (MoM & YoY)")
            st.line_chart(dynamic_chart_df)

            st.subheader("📊 Summary Statistics")
            summary_cols = ['inflation_mom']
            if 'inflation_yoy' in filtered_df.columns:
                summary_cols.append('inflation_yoy')
            stats = filtered_df[summary_cols].describe().T
            st.dataframe(stats.style.format("{:.4f}"))
        else:
            st.warning("No data available for the selected range.")

    elif page == "🔮 Forecast":
        render_forecast_page(df, division_mapping)
