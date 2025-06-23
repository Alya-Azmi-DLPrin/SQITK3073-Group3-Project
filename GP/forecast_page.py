# forecast_page.py
import streamlit as st
import pandas as pd
import numpy as np

def render_forecast_page(df, division_mapping):
    st.title("🔮 Inflation Forecast - Next 6 Months")

    division_names = df['division_name'].dropna().unique()
    selected_division_name = st.selectbox("Select Division", sorted(division_names))
    selected_division_code = [k for k, v in division_mapping.items() if v == selected_division_name][0]
    states = df[df['division'] == selected_division_code]['state'].unique()
    selected_state = st.selectbox("Select State", sorted(states))

    state_df = df[(df['division'] == selected_division_code) & (df['state'] == selected_state)].copy()
    state_df = state_df.sort_values('date')

    if len(state_df) >= 6:
        state_df['t'] = np.arange(len(state_df))
        X = state_df['t'].values
        y = state_df['inflation_mom'].values
        a, b = np.polyfit(X, y, deg=1)

        future_t = np.arange(len(X), len(X) + 6)
        future_pred = a * future_t + b
        last_date = state_df['date'].iloc[-1]
        future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=6, freq='MS')

        forecast_df = pd.DataFrame({
            'date': future_dates,
            'inflation_mom': future_pred
        })
        combined_df = pd.concat([state_df[['date', 'inflation_mom']], forecast_df])
        combined_df = combined_df.set_index('date')

        st.subheader("📈 Forecast + Historical Trend")
        st.line_chart(combined_df)

        st.subheader("📅 Forecast Table (Next 6 Months)")
        forecast_display = pd.DataFrame({
            'Date': future_dates.strftime('%Y-%m'),
            'Predicted Inflation MoM (%)': future_pred
        })
        st.dataframe(forecast_display.style.format({"Predicted Inflation MoM (%)": "{:.4f}"}))
    else:
        st.warning("Not enough data to generate forecast.")
