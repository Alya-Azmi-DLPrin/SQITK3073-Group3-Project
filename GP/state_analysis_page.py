# state_analysis_page.py
import streamlit as st
import pandas as pd
import plotly.express as px

def render_state_analysis_page(df):
    st.title("📊 State-Level Inflation Analysis")

    division_names = sorted(df['division_name'].unique(), key=lambda x: str(x))

    col1, col2 = st.columns(2)
    with col1:
        selected_division = st.selectbox("Select Economic Sector", options=division_names, key='state_division')
    with col2:
        available_states = df[df['division_name'] == selected_division]['state'].unique()
        selected_state = st.selectbox("Select State", options=sorted(available_states), key='state_select')

    min_date = df['date'].min().date()
    max_date = df['date'].max().date()

    date_range = st.slider(
        "Date Range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM"
    )

    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])

    filtered_df = df[
        (df['division_name'] == selected_division) &
        (df['state'] == selected_state) &
        (df['date'] >= start_date) &
        (df['date'] <= end_date)
    ].sort_values('date')

    if not filtered_df.empty:
        latest = filtered_df.iloc[-1]
        delta_mom = latest['inflation_mom'] - filtered_df.iloc[-2]['inflation_mom'] if len(filtered_df) > 1 else 0
        delta_yoy = latest['inflation_yoy'] - filtered_df.iloc[-13]['inflation_yoy'] if len(filtered_df) > 12 else 0

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current MoM Inflation", f"{latest['inflation_mom']:.2f}%", f"{delta_mom:.2f}% from previous")
        with col2:
            st.metric("Current YoY Inflation", f"{latest['inflation_yoy']:.2f}%", f"{delta_yoy:.2f}% from last year")

        tab1, tab2 = st.tabs(["📈 Trend Analysis", "📊 Distribution"])

        with tab1:
            fig = px.line(
                filtered_df,
                x='date',
                y=['inflation_mom', 'inflation_yoy'],
                labels={'value': 'Inflation %', 'date': ''},
                title=f"Inflation Trend for {selected_state} - {selected_division}"
            )
            fig.update_layout(legend_title_text='Metric')
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            fig = px.histogram(
                filtered_df,
                x='inflation_mom',
                nbins=20,
                title="Distribution of Monthly Inflation Rates"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Raw Data")
        st.dataframe(
            filtered_df[['date', 'inflation_mom', 'inflation_yoy']]
            .sort_values('date', ascending=False)
            .style.format({
                'inflation_mom': '{:.2f}%',
                'inflation_yoy': '{:.2f}%'
            })
        )
    else:
        st.warning("No data available for selected filters")
