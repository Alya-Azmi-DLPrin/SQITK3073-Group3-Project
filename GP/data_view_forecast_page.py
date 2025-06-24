import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

@st.cache_data (ttl=86400)

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

    # Selection in main layout
    st.subheader("🎯 Select Analysis Scope")
    col1, col2 = st.columns(2)
    with col1:
        division_names = df['division_name'].dropna().unique()
        selected_division_name = st.selectbox("Select Division", sorted(division_names))
        selected_division_code = [k for k, v in division_mapping.items() if v == selected_division_name][0]
    with col2:
        states = df[df['division'] == selected_division_code]['state'].unique()
        selected_state = st.selectbox("Select State", sorted(states))

    state_df = df[(df['division'] == selected_division_code) & (df['state'] == selected_state)].copy()
    state_df = state_df.sort_values('date')

    if page == "📊 Data View":
        st.subheader(f"📊 State-Level Inflation Analysis: {selected_state} - {selected_division_name}")

        min_date = state_df['date'].min().date()
        max_date = state_df['date'].max().date()
        start_date, end_date = st.slider(
            "Select Date Range",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="YYYY-MM"
        )
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        filtered_df = state_df[(state_df['date'] >= start_date) & (state_df['date'] <= end_date)]

        if not filtered_df.empty:
            latest = filtered_df.iloc[-1]
            delta_mom = latest['inflation_mom'] - filtered_df.iloc[-2]['inflation_mom'] if len(filtered_df) > 1 else 0
            delta_yoy = latest['inflation_yoy'] - filtered_df.iloc[-13]['inflation_yoy'] if len(filtered_df) > 12 else 0

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Current MoM Inflation", f"{latest['inflation_mom']:.2f}%", f"{delta_mom:.2f}%")
            with col2:
                st.metric("Current YoY Inflation", f"{latest['inflation_yoy']:.2f}%", f"{delta_yoy:.2f}%")

            tab1, tab2 = st.tabs(["📈 Trend", "📊 Distribution"])
            with tab1:
                fig = px.line(filtered_df, x='date', y=['inflation_mom', 'inflation_yoy'],
                              labels={'value': 'Inflation %', 'date': ''},
                              title=f"{selected_state} - {selected_division_name}")
                st.plotly_chart(fig, use_container_width=True)
            with tab2:
                st.plotly_chart(px.histogram(filtered_df, x='inflation_mom', nbins=20,
                              title="Distribution of Monthly MoM Inflation"), use_container_width=True)

            st.subheader("📋 Summary Statistics")
            st.dataframe(filtered_df[['inflation_mom']].describe().T.style.format("{:.4f}"))

            st.subheader("📂 Raw Data")
            st.dataframe(
                filtered_df[['date', 'inflation_mom', 'inflation_yoy']]
                .sort_values('date', ascending=False)
                .style.format({'inflation_mom': '{:.2f}%', 'inflation_yoy': '{:.2f}%'})
            )
        else:
            st.warning("No data for selected range.")

    elif page == "🔮 Forecast":
        st.subheader(f"🔮 Forecast - Next 6 Months: {selected_state} - {selected_division_name}")

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
