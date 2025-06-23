# national_trends_page.py
import streamlit as st
import pandas as pd
import plotly.express as px

def render_national_trends_page(df, core_divisions):
    st.title("📈 National Inflation Trends")

    # National aggregates
    national_df = df.groupby('date').agg({
        'inflation_mom': 'mean',
        'inflation_yoy': 'mean'
    }).reset_index()

    # Core inflation series
    core_df = df[df['division'].isin(core_divisions)].groupby('date')['inflation_mom'].mean().reset_index()
    core_df.rename(columns={'inflation_mom': 'core_inflation'}, inplace=True)

    # Line chart: Headline vs Core
    st.subheader("Headline vs Core Inflation")
    fig = px.line(
        pd.merge(national_df, core_df, on='date'),
        x='date',
        y=['inflation_mom', 'core_inflation'],
        labels={'value': 'Inflation %', 'date': ''},
        title="National Inflation Trends"
    )
    fig.update_layout(legend_title_text='Metric')
    st.plotly_chart(fig, use_container_width=True)

    # Area chart: Sectoral breakdown
    st.subheader("Sectoral Contribution to Inflation")
    sector_df = df.pivot_table(
        index='date',
        columns='division_name',
        values='inflation_mom',
        aggfunc='mean'
    )
    fig = px.area(
        sector_df,
        labels={'value': 'Inflation %', 'date': ''},
        title="Inflation by Economic Sector Over Time"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Latest data table
    st.subheader("Latest National Data")
    latest_date = df['date'].max()
    st.dataframe(
        df[df['date'] == latest_date]
        .pivot_table(index='division_name', columns='state', values='inflation_mom')
        .style.background_gradient(cmap='RdYlGn_r', axis=None)
        .format('{:.2f}%')
    )
