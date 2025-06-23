import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from fpdf import FPDF
from datetime import datetime, date
from io import BytesIO
import base64
import sys
import kaleido

# Load and cache data
@st.cache_data
def load_data():
    URL_DATA = 'https://storage.dosm.gov.my/cpi/cpi_2d_state_inflation.parquet'
    df = pd.read_parquet(URL_DATA)
    df['date'] = pd.to_datetime(df['date'])
    
    # Calculate YoY inflation
    df['price_index'] = (1 + df['inflation_mom']/100).cumprod()
    df['inflation_yoy'] = df.groupby(['state', 'division'])['price_index'].pct_change(periods=12) * 100
    return df.drop('price_index', axis=1)

# Division mapping
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

# Core inflation divisions
core_divisions = ['03', '05', '06', '08', '09', '10', '12']

def main():
    st.set_page_config(layout="wide", page_title="Malaysia Inflation Dashboard")
    df = load_data()
    
    # Ensure clean division names
    df['division_name'] = df['division'].map(division_mapping).astype(str).str.strip()
    df['division_name'] = df['division_name'].fillna('Unknown')
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("", ["🌡️ FDI Heatmap", "📊 State Analysis", "📈 National Trends"])

    # ==================== FDI HEATMAP PAGE ====================
    if page == "🌡️ FDI Heatmap":
        st.title("🇲🇾 Malaysia Inflation Dashboard (FDI View)")
        
        # Controls
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

        # Prepare data
        filtered_df = df[df['date'] == selected_date]
        if show_core:
            filtered_df = filtered_df[filtered_df['division'].isin(core_divisions)]
        
        heatmap_df = filtered_df.pivot_table(
            index='division_name',
            columns='state',
            values='inflation_mom',
            aggfunc='mean'
        ).sort_index()

        # Enhanced Heatmap
        fig = px.imshow(
            heatmap_df,
            color_continuous_scale='RdYlGn_r',
            zmin=-1,
            zmax=2,
            labels={'color': 'Inflation %'},
            aspect="auto",
            text_auto=".1f" if show_values else False
        )

        # Improved Hover Text
        fig.update_traces(
            hovertemplate=(
                "<b><span style='font-size:16px; color:black'>%{y}</span></b><br>"
                "<span style='font-size:14px'>State: %{x}</span><br>"
                "<span style='font-size:16px; color:blue'><b>Inflation: %{z:.2f}%</b></span>"
                "<extra></extra>"
            ),
            hoverlabel=dict(
                bgcolor="white",
                bordercolor="black",
                font=dict(size=14, color="black", family="Arial")
            )
        )

        fig.update_layout(
            title=f"<b>MoM Inflation Rates by Division and State ({selected_date.strftime('%Y-%m')})</b>",
            xaxis_title="<b>State</b>",
            yaxis_title="<b>Division</b>",
            height=700,
            font=dict(color="#333333"),
            margin=dict(l=120, r=50, b=100, t=100)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Competitiveness Analysis
        st.subheader("🔍 State Competitiveness Analysis")
        volatility_df = df.groupby('state')['inflation_mom'].std().rename('volatility')
        score_df = heatmap_df.T.merge(volatility_df, left_index=True, right_index=True)
        score_df['stability_score'] = (1 / (score_df.mean(axis=1) + score_df['volatility'])).round(2)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🏆 Top 5 Most Stable States**")
            st.dataframe(
                score_df['stability_score'].sort_values(ascending=False).head(5)
                .to_frame().style.format('{:.2f}')
                .background_gradient(cmap='Greens')
            )
        
        with col2:
            st.markdown("**⚠️ Top 5 Most Volatile States**")
            st.dataframe(
                score_df['volatility'].sort_values(ascending=False).head(5)
                .to_frame().style.format('{:.2f}')
                .background_gradient(cmap='Reds_r')
            )

        # PDF Report Generation
        st.subheader("📑 Generate Custom Report")
        report_name = st.text_input("Report Name", "Malaysia_Inflation_Analysis")
        
        if st.button("📥 Generate PDF Report"):
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                
                # Title
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, txt=f"{report_name}", ln=1, align='C')
                
                # Date
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=1)
                pdf.ln(10)
                
                # Add heatmap image
                img_bytes = fig.to_image(format="png", width=800)
                temp_img = "temp_heatmap.png"
                with open(temp_img, "wb") as f:
                    f.write(img_bytes)
                pdf.image(temp_img, x=10, y=40, w=190)
                
                # Key findings
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
                
                # Convert to download link
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                b64 = base64.b64encode(pdf_bytes).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="{report_name}.pdf">Download Full Report</a>'
                st.markdown(href, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Failed to generate PDF: {str(e)}")

    # ==================== STATE ANALYSIS PAGE ====================
    elif page == "📊 State Analysis":
        st.title("📊 State-Level Inflation Analysis")
        
        # Get clean sorted divisions
        division_names = sorted(df['division_name'].unique(), key=lambda x: str(x))
        
        col1, col2 = st.columns(2)
        with col1:
            selected_division = st.selectbox(
                "Select Economic Sector",
                options=division_names,
                key='state_division'
            )
        with col2:
            available_states = df[df['division_name'] == selected_division]['state'].unique()
            selected_state = st.selectbox(
                "Select State",
                options=sorted(available_states),
                key='state_select'
            )
        
        # Date range
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()

        date_range = st.slider(
            "Date Range",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="YYYY-MM"
        )
        
        #Covert back to Timestamp for filtering
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])

        # Filter data
        filtered_df = df[
            (df['division_name'] == selected_division) &
            (df['state'] == selected_state) &
            (df['date'] >= start_date) &
            (df['date'] <= end_date)
        ].sort_values('date')

        if not filtered_df.empty:
            # Metrics
            latest = filtered_df.iloc[-1]
            delta_mom = latest['inflation_mom'] - filtered_df.iloc[-2]['inflation_mom']
            delta_yoy = latest['inflation_yoy'] - filtered_df.iloc[-13]['inflation_yoy'] if len(filtered_df) > 12 else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Current MoM Inflation",
                    f"{latest['inflation_mom']:.2f}%",
                    f"{delta_mom:.2f}% from previous"
                )
            with col2:
                st.metric(
                    "Current YoY Inflation",
                    f"{latest['inflation_yoy']:.2f}%",
                    f"{delta_yoy:.2f}% from last year"
                )
            
            # Charts
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
            
            # Raw data
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

    # ==================== NATIONAL TRENDS PAGE ====================
    elif page == "📈 National Trends":
        st.title("📈 National Inflation Trends")
        
        # National aggregates
        national_df = df.groupby('date').agg({
            'inflation_mom': 'mean',
            'inflation_yoy': 'mean'
        }).reset_index()
        
        # Core vs headline
        core_df = df[df['division'].isin(core_divisions)].groupby('date')['inflation_mom'].mean().reset_index()
        core_df.rename(columns={'inflation_mom': 'core_inflation'}, inplace=True)
        
        # Combined chart
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
        
        # Sectoral breakdown
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
        
        # Latest data
        st.subheader("Latest National Data")
        latest_date = df['date'].max()
        st.dataframe(
            df[df['date'] == latest_date]
            .pivot_table(index='division_name', columns='state', values='inflation_mom')
            .style.background_gradient(cmap='RdYlGn_r', axis=None)
            .format('{:.2f}%')
        )

if __name__ == "__main__":
    main()
