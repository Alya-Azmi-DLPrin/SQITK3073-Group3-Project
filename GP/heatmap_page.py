import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from datetime import datetime
import base64

def render_heatmap_page(df, core_divisions, division_mapping):
    st.title("🌡️ FDI Heatmap & Stability Report")
    st.markdown("""
    ### Instructions:
    - Select report date and toggle core inflation.
    - Heatmap shows MoM inflation by division/state.
    - Download a full PDF report with findings.
    """)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        selected_date = st.selectbox("Select Report Date", options=sorted(df['date'].unique(), reverse=True),
                                     format_func=lambda x: x.strftime('%b %Y'))
    with col2:
        show_core = st.checkbox("Core Inflation Only", True)
    with col3:
        show_values = st.checkbox("Show Values", True)

    filtered_df = df[df['date'] == selected_date]
    if show_core:
        filtered_df = filtered_df[filtered_df['division'].isin(core_divisions)]

    heatmap_df = filtered_df.pivot_table(index='division_name', columns='state', values='inflation_mom', aggfunc='mean').sort_index()

    fig = px.imshow(
        heatmap_df, color_continuous_scale='RdYlGn_r', zmin=-1, zmax=2,
        labels={'color': 'Inflation %'}, aspect="auto",
        text_auto=".1f" if show_values else False
    )
    fig.update_layout(
        title=f"<b>MoM Inflation Rates by Division and State ({selected_date.strftime('%Y-%m')})</b>",
        xaxis_title="<b>State</b>", yaxis_title="<b>Division</b>", height=700,
        margin=dict(l=120, r=50, b=100, t=100)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📊 State Competitiveness Analysis")
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

    st.subheader("📑 Generate Custom PDF Report")
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
            with open("temp_heatmap.png", "wb") as f:
                f.write(img_bytes)
            pdf.image("temp_heatmap.png", x=10, y=40, w=190)

            pdf.set_y(140)
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(200, 10, txt="Key Findings:", ln=1)
            findings = [
                f"Most Stable State: {score_df['stability_score'].idxmax()}",
                f"Most Volatile State: {score_df['volatility'].idxmax()}",
                f"Avg Inflation: {heatmap_df.values.mean():.2f}%",
                f"Core Avg Inflation: {heatmap_df[heatmap_df.index.isin([division_mapping[d] for d in core_divisions])].values.mean():.2f}%"
            ]
            pdf.set_font('Arial', size=12)
            for fnd in findings:
                pdf.cell(200, 8, txt=fnd, ln=1)

            b64 = base64.b64encode(pdf.output(dest='S').encode('latin-1')).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{report_name}.pdf">Download Full Report</a>'
            st.markdown(href, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"PDF generation failed: {str(e)}")
