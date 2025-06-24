import streamlit as st
import pandas as pd
import plotly.express as px

def render_national_trends_page(df, core_divisions):
    st.title("📈 National Inflation Trends")
    st.markdown("### Explore headline vs core inflation and filter sectors using the dropdown below.")

    # ========== National Aggregates ==========
    national_df = df.groupby('date').agg({
        'inflation_mom': 'mean',
        'inflation_yoy': 'mean'
    }).reset_index()

    core_df = df[df['division'].isin(core_divisions)].groupby('date')['inflation_mom'].mean().reset_index()
    core_df.rename(columns={'inflation_mom': 'core_inflation'}, inplace=True)

    # ========== Line Chart ==========
    st.subheader("📊 Headline vs Core Inflation")
    fig = px.line(
        pd.merge(national_df, core_df, on='date'),
        x='date', y=['inflation_mom', 'core_inflation'],
        labels={'value': 'Inflation %', 'date': ''},
        title="National Inflation Trends"
    )
    fig.update_layout(legend_title_text='Metric')
    st.plotly_chart(fig, use_container_width=True)

    # ========== Sectoral Contribution ==========
    st.subheader("🧭 Sectoral Contribution to Inflation")

    sector_df = df.pivot_table(index='date', columns='division_name', values='inflation_mom', aggfunc='mean')
    all_sectors = sorted(sector_df.columns)

    # Initialize session state for sectors
    if "selected_sectors" not in st.session_state:
        st.session_state.selected_sectors = all_sectors.copy()

    with st.expander("📌 Filter Economic Sectors", expanded=True):
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("✅ Select All Sectors"):
                st.session_state.selected_sectors = all_sectors.copy()
            if st.button("❌ Clear All Sectors"):
                st.session_state.selected_sectors = []

        with col2:
            selected = st.multiselect(
                "Choose sectors to display",
                options=all_sectors,
                default=st.session_state.selected_sectors,
                key="sector_dropdown",
                help="Use this to filter the area chart by sectors"
            )
            st.session_state.selected_sectors = selected

    if st.session_state.selected_sectors:
        filtered_df = sector_df[st.session_state.selected_sectors]
        fig = px.area(
            filtered_df,
            labels={'value': 'Inflation %', 'date': ''},
            title="Inflation by Selected Economic Sectors"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("☝️ Please select at least one sector to display the area chart.")

    # ========== Latest Table ==========
    st.subheader("📅 Latest National Data")
    latest_date = df['date'].max()
    st.dataframe(
        df[df['date'] == latest_date]
        .pivot_table(index='division_name', columns='state', values='inflation_mom')
        .style.background_gradient(cmap='RdYlGn_r', axis=None)
        .format('{:.2f}%')
    )
