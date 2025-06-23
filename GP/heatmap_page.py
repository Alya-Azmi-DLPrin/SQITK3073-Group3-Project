# heatmap_forecast_analysis.py
import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from datetime import datetime
import base64

# ========== FDI HEATMAP ==========
def render_heatmap_page(df, core_divisions, division_mapping):
    st.title("🇲🇾 Malaysia Inflation Dashboard (FDI View)")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        selected_date = st.selectbox(
            "Select Report Date",
            options=sorted(df['date'].unique(), reverse=True),
            format_func=lambda x: x.strftime('%b %Y')
        )
    with col2:
        show_core = st.checkbox("Core Inflation Only", True)
    with col3:
        show_values = st.checkbox("Show Values", True)

    filtered_df = df[df['date'] == selected_date]
    if show_core:
        filtered_df = filtered_df[filtered_df['division'].isin(core_divisions)]

    heatmap_df = filtered_df.pivot_table(
        index='division_name', columns='state', values='inflation_mom', aggfunc='mean'
    ).sort_index()

    fig = px.imshow(
        heatmap_df,
        color_continuous_scale='RdYlGn_r',
        zmin=-1, zmax=2,
        labels={'color': 'Inflation %'},
        aspect="auto",
        text_auto=".1f" if show_values else False
    )
    fig.update_layout(
        title=f"<b>MoM Inflation Rates by Division and State ({selected_date.strftime('%Y-%m')})</b>",
        xaxis_title="<b>State</b>",
        yaxis_title="<b>Division</b>",
        height=700,
        margin=dict(l=120, r=50, b=100, t=100)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🔍 State Competitiveness Analysis")
    volatility_df = df.groupby('state')['inflation_mom'].std().rename('volatility')
    score_df = heatmap_df.T.merge(volatility_df, left_index=True, right_index=True)
    score_df['stability_score'] = (1 / (score_df.mean(axis=1) + score_df['volatility'])).round(2)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🏆 Top 5 Most Stable States**")
        st.dataframe(score_df['stability_score'].sort_values(ascending=False).head(5).to_frame()
                     .style.format('{:.2f}').background_gradient(cmap='Greens'))
    with col2:
        st.markdown("**⚠️ Top 5 Most Volatile States**")
        st.dataframe(score_df['volatility'].sort_values(ascending=False).head(5).to_frame()
                     .style.format('{:.2f}').background_gradient(cmap='Reds_r'))

    st.subheader("📑 Generate Custom Report")
    report_name = st.text_input("Report Name", "Malaysia_Inflation_Analysis")

    if st.button("📥 Generate PDF Report"):
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt=f"{report_name}", ln=1, align='C')

            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=1)
            pdf.ln(10)

            img_bytes = fig.to_image(format="png", width=800)
            temp_img = "temp_heatmap.png"
            with open(temp_img, "wb") as f:
                f.write(img_bytes)
            pdf.image(temp_img, x=10, y=40, w=190)

            pdf.set_y(140)
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(200, 10, txt="Key Findings:", ln=1)

            findings = [
                f"Most Stable State: {score_df['stability_score'].idxmax()} (Score: {score_df['stability_score'].max():.2f})",
                f"Most Volatile State: {score_df['volatility'].idxmax()} (Score: {score_df['volatility'].max():.2f})",
                f"Average Inflation: {heatmap_df.values.mean():.2f}%",
                f"Core Inflation Average: {heatmap_df[heatmap_df.index.isin([division_mapping[d] for d in core_divisions])].values.mean():.2f}%"
            ]

            pdf.set_font('Arial', size=12)
            for finding in findings:
                pdf.cell(200, 8, txt=finding, ln=1)

            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{report_name}.pdf">Download Full Report</a>'
            st.markdown(href, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Failed to generate PDF: {str(e)}")

# ========== STATE ANALYSIS ==========
def render_state_analysis_page(df):
    st.title("📊 State-Level Inflation Analysis")
    division_names = sorted(df['division_name'].unique())

    col1, col2 = st.columns(2)
    with col1:
        selected_division = st.selectbox("Select Economic Sector", options=division_names)
    with col2:
        selected_state = st.selectbox("Select State", options=sorted(df[df['division_name'] == selected_division]['state'].unique()))

    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    date_range = st.slider("Date Range", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="YYYY-MM")

    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])

    filtered_df = df[(df['division_name'] == selected_division) & (df['state'] == selected_state) &
                     (df['date'] >= start_date) & (df['date'] <= end_date)].sort_values('date')

    if not filtered_df.empty:
        latest = filtered_df.iloc[-1]
        delta_mom = latest['inflation_mom'] - filtered_df.iloc[-2]['inflation_mom']
        delta_yoy = latest['inflation_yoy'] - filtered_df.iloc[-13]['inflation_yoy'] if len(filtered_df) > 12 else 0

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current MoM Inflation", f"{latest['inflation_mom']:.2f}%", f"{delta_mom:.2f}% from previous")
        with col2:
            st.metric("Current YoY Inflation", f"{latest['inflation_yoy']:.2f}%", f"{delta_yoy:.2f}% from last year")

        tab1, tab2 = st.tabs(["📈 Trend Analysis", "📊 Distribution"])
        with tab1:
            fig = px.line(filtered_df, x='date', y=['inflation_mom', 'inflation_yoy'],
                          labels={'value': 'Inflation %', 'date': ''},
                          title=f"Inflation Trend for {selected_state} - {selected_division}")
            fig.update_layout(legend_title_text='Metric')
            st.plotly_chart(fig, use_container_width=True)
        with tab2:
            fig = px.histogram(filtered_df, x='inflation_mom', nbins=20,
                               title="Distribution of Monthly Inflation Rates")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Raw Data")
        st.dataframe(filtered_df[['date', 'inflation_mom', 'inflation_yoy']]
                     .sort_values('date', ascending=False)
                     .style.format({'inflation_mom': '{:.2f}%', 'inflation_yoy': '{:.2f}%'}))
    else:
        st.warning("No data available for selected filters")

# ========== NATIONAL TRENDS ==========
def render_national_trends_page(df, core_divisions):
    st.title("📈 National Inflation Trends")

    national_df = df.groupby('date').agg({'inflation_mom': 'mean', 'inflation_yoy': 'mean'}).reset_index()
    core_df = df[df['division'].isin(core_divisions)].groupby('date')['inflation_mom'].mean().reset_index()
    core_df.rename(columns={'inflation_mom': 'core_inflation'}, inplace=True)

    st.subheader("Headline vs Core Inflation")
    fig = px.line(pd.merge(national_df, core_df, on='date'),
                  x='date', y=['inflation_mom', 'core_inflation'],
                  labels={'value': 'Inflation %', 'date': ''},
                  title="National Inflation Trends")
    fig.update_layout(legend_title_text='Metric')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Sectoral Contribution to Inflation")
    sector_df = df.pivot_table(index='date', columns='division_name', values='inflation_mom', aggfunc='mean')
    fig = px.area(sector_df, labels={'value': 'Inflation %', 'date': ''},
                  title="Inflation by Economic Sector Over Time")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Latest National Data")
    latest_date = df['date'].max()
    st.dataframe(df[df['date'] == latest_date]
                 .pivot_table(index='division_name', columns='state', values='inflation_mom')
                 .style.background_gradient(cmap='RdYlGn_r', axis=None)
                 .format('{:.2f}%'))
