import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from fpdf import FPDF
from datetime import datetime

# Load and cache data from URL (.parquet)
@st.cache_data
def load_data():
    URL_DATA = 'https://storage.dosm.gov.my/cpi/cpi_2d_state_inflation.parquet'
    df = pd.read_parquet(URL_DATA)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    # Calculate YoY inflation using the existing 'inflation_mom' column
    # First we need to calculate cumulative inflation for YoY
    df['price_index'] = (1 + df['inflation_mom']/100).cumprod()
    df['inflation_yoy'] = df.groupby(['state', 'division'])['price_index'].pct_change(periods=12) * 100
    df.drop('price_index', axis=1, inplace=True)
    
    return df

# Division code-to-name mapping
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

try:
    df = load_data()
    df['division_name'] = df['division'].map(division_mapping)

    # Core inflation divisions (excluding volatile food/energy)
    core_divisions = ['03', '05', '06', '08', '09', '10', '12']

    # Sidebar navigation
    page = st.sidebar.radio("Navigation", ["📊 State Analysis", "🌡️ FDI Heatmap", "📈 Trends"])

    # =============================================
    # ENHANCED HEATMAP PAGE (FDI FOCUS)
    # =============================================
    if page == "🌡️ FDI Heatmap":
        st.title("🇲🇾 Malaysia Inflation Heatmap (FDI View)")
        st.markdown("""
        **Foreign Investor Focus**: Compare inflation stability across states and sectors.  
        Key features:  
        - 🎯 IMF threshold alerts  
        - 🏭 Core inflation toggle  
        - 📍 State competitiveness scores  
        """)
        
        # Date selection
        latest_date = df['date'].max()
        selected_date = st.selectbox(
            "Reference Date",
            options=sorted(df['date'].unique(), reverse=True),
            index=0,
            format_func=lambda x: x.strftime('%b %Y')
        )
        
        # Core inflation toggle
        show_core = st.checkbox("Show Core Inflation (Excluding Food & Energy)", True)
        filtered_df = df[df['date'] == selected_date]
        
        if show_core:
            filtered_df = filtered_df[filtered_df['division'].isin(core_divisions)]
        
        # Prepare heatmap data
        heatmap_df = filtered_df.pivot_table(
            index='division_name',
            columns='state',
            values='inflation_mom',
            aggfunc='mean'
        ).sort_index()
        
        # Calculate state competitiveness scores (lower inflation + lower volatility = better)
        volatility_df = df.groupby('state')['inflation_mom'].std().rename('volatility')
        heatmap_df = heatmap_df.T.merge(volatility_df, left_index=True, right_index=True)
        heatmap_df['competitiveness'] = (1 / (heatmap_df.mean(axis=1) + heatmap_df['volatility'])).round(2)
        heatmap_df = heatmap_df.sort_values('competitiveness', ascending=False)
        
        # Create enhanced heatmap
        fig = px.imshow(
            heatmap_df.drop(['volatility', 'competitiveness'], axis=1).T,
            color_continuous_scale='RdYlGn_r',
            zmin=0, # Set minimum
            zmax=4, # Set maximum
            labels={'color': 'Inflation %'},
            title=f"{'Core ' if show_core else ''}Inflation by State & Sector ({selected_date.strftime('%b %Y')})"
        )
        
        fig.update_layout(
            coloraxis=dict(
                cmin=0,
                cmax=4,
                colorscale=[[0,'red'],[0.5,'yellow'],[1,'green']]
            )
        )
        # Add annotations
        annotations = []
        for i, division in enumerate(heatmap_df.columns[:-2]):
            for j, state in enumerate(heatmap_df.index):
                val = heatmap_df.loc[state, division]
                color = 'white' if abs(val - 2) > 1 else 'black'
                annotations.append(
                    dict(
                        text=f"{val:.1f}",
                        x=state, y=division,
                        showarrow=False,
                        font=dict(color=color)
                    )
                )
        
        # Final layout adjustments
        fig.update_layout(
            annotations=annotations,
            xaxis_title=f"State (Competitiveness Rank) | Avg: {heatmap_df['competitiveness'].mean():.2f}",
            yaxis_title="Economic Sector",
            height=800,
        )
        
        # Display
        st.plotly_chart(fig, use_container_width=True)
        
        # Competitiveness leaderboard
        st.subheader("🏆 State Competitiveness Ranking")
        st.dataframe(
            heatmap_df[['competitiveness', 'volatility']].sort_values('competitiveness', ascending=False).style
            .background_gradient(cmap='Greens', subset=['competitiveness'])
            .background_gradient(cmap='Reds_r', subset=['volatility'])
            .format({'competitiveness': '{:.2f}', 'volatility': '{:.2f}'})
        )
        
        # Export button
        if st.button("📥 Generate Investor Brief"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Malaysia Inflation Brief - {datetime.now().strftime('%Y-%m-%d')}", ln=1)
            pdf.cell(200, 10, txt=f"Top State: {heatmap_df.index[0]} (Score: {heatmap_df['competitiveness'].iloc[0]:.2f})", ln=1)
            pdf.output("malaysia_inflation_brief.pdf")
            st.success("Report generated!")

    # =============================================
    # OTHER PAGES (State Analysis & Trends)
    # =============================================
    elif page == "📊 State Analysis":
        st.title("📊 State-Level Inflation Analysis")
        
        # State and division selection
        division_names = df['division_name'].dropna().unique()
        selected_division_name = st.sidebar.selectbox("Select Division", sorted(division_names))
        selected_division_code = [k for k, v in division_mapping.items() if v == selected_division_name][0]
        states = df[df['division'] == selected_division_code]['state'].unique()
        selected_state = st.sidebar.selectbox("Select State", sorted(states))
        
        # Filter data
        state_df = df[(df['division'] == selected_division_code) & 
                     (df['state'] == selected_state)].copy().sort_values('date')
        
        # Date range filter
        min_date, max_date = state_df['date'].min(), state_df['date'].max()
        start_date, end_date = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Filter by date
        filtered_df = state_df[(state_df['date'] >= pd.to_datetime(start_date)) & 
                              (state_df['date'] <= pd.to_datetime(end_date))]
        
        if not filtered_df.empty:
            # Display metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Latest MoM Inflation", 
                         f"{filtered_df['inflation_mom'].iloc[-1]:.2f}%")
            with col2:
                st.metric("Latest YoY Inflation",
                         f"{filtered_df['inflation_yoy'].iloc[-1]:.2f}%")
            
            # Time series chart
            st.subheader("Inflation Trend")
            chart_df = filtered_df.set_index('date')[['inflation_mom', 'inflation_yoy']]
            st.line_chart(chart_df)
            
            # Data table
            st.subheader("Detailed Data")
            st.dataframe(filtered_df[['date', 'inflation_mom', 'inflation_yoy']].sort_values('date', ascending=False))
        
    elif page == "📈 Trends":
        st.title("📈 National Inflation Trends")
        
        # National aggregate calculation
        national_df = df.groupby('date').agg({
            'inflation_mom': 'mean',
            'inflation_yoy': 'mean'
        }).reset_index()
        
        # Display trends
        st.subheader("National Inflation Rates")
        st.line_chart(national_df.set_index('date'))
        
        # Sectoral breakdown
        st.subheader("Sectoral Contribution to Inflation")
        sector_df = df.pivot_table(
            index='date',
            columns='division_name',
            values='inflation_mom',
            aggfunc='mean'
        )
        st.area_chart(sector_df)

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.stop()
