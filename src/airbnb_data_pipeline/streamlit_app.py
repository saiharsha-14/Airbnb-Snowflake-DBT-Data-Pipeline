import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ---------------------------------------------------------
# PAGE CONFIGURATION & AIRBNB THEME STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="Airbnb Executive Analytics | Gold Warehouse",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern Cards, Metric Badges, and Clean Spacing
st.markdown("""
<style>
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #717171;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.55rem;
        font-weight: 700;
        color: #222222;
        white-space: nowrap;
        margin-bottom: 4px;
    }
    .metric-delta {
        font-size: 0.85rem;
        font-weight: 600;
        color: #008a05;
    }
    
    /* Header Container */
    .header-box {
        padding: 18px 0px 24px 0px;
        border-bottom: 1px solid #ebebeb;
        margin-bottom: 24px;
    }
    
    /* Tag Badges */
    .tier-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# SNOWFLAKE SESSION / DATA LOADER
# ---------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner="Querying Snowflake Gold Layer...")
def get_gold_data():
    try:
        # 1. Attempt Streamlit-in-Snowflake Native Session
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        query = """
            SELECT 
                BOOKING_ID,
                LISTING_ID,
                HOST_ID,
                BOOKING_DATE,
                TOTAL_AMOUNT,
                CLEANING_FEE,
                SERVICE_FEE,
                BOOKING_STATUS,
                PROPERTY_TYPE,
                ROOM_TYPE,
                CITY,
                COUNTRY,
                ACCOMMODATES,
                BEDROOMS,
                BATHROOMS,
                PRICE_PER_NIGHT,
                PRICE_PER_NIGHT_TAG,
                HOST_NAME,
                IS_SUPERHOST,
                RESPONSE_RATE_QUALITY
            FROM AIRBNB.GOLD.OBT
        """
        df = session.sql(query).to_pandas()
    except Exception:
        # 2. Fallback Mock Data Generator for Local Development/Demo testing
        np.random.seed(42)
        n_rows = 5000
        cities = ['New York', 'Paris', 'Tokyo', 'London', 'Berlin', 'Sydney']
        room_types = ['Entire home/apt', 'Private room', 'Shared room', 'Hotel room']
        property_types = ['Apartment', 'Condo', 'House', 'Loft', 'Villa']
        tags = ['low', 'medium', 'high']
        statuses = ['confirmed', 'cancelled', 'pending']
        
        dates = pd.date_range(start="2024-01-01", end="2025-12-31", periods=n_rows)
        prices = np.random.lognormal(mean=4.8, sigma=0.6, size=n_rows)
        nights = np.random.randint(1, 14, size=n_rows)
        
        df = pd.DataFrame({
            'BOOKING_ID': [f"BK-{10000+i}" for i in range(n_rows)],
            'LISTING_ID': [f"LS-{20000 + np.random.randint(1, 800)}" for _ in range(n_rows)],
            'HOST_ID': [f"HST-{30000 + np.random.randint(1, 300)}" for _ in range(n_rows)],
            'BOOKING_DATE': dates,
            'PRICE_PER_NIGHT': np.round(prices, 2),
            'CLEANING_FEE': np.round(prices * 0.15, 2),
            'SERVICE_FEE': np.round(prices * 0.10, 2),
            'TOTAL_AMOUNT': np.round(prices * nights + (prices * 0.25), 2),
            'BOOKING_STATUS': np.random.choice(statuses, size=n_rows, p=[0.85, 0.10, 0.05]),
            'PROPERTY_TYPE': np.random.choice(property_types, size=n_rows),
            'ROOM_TYPE': np.random.choice(room_types, size=n_rows, p=[0.60, 0.30, 0.05, 0.05]),
            'CITY': np.random.choice(cities, size=n_rows),
            'COUNTRY': 'Global',
            'ACCOMMODATES': np.random.randint(1, 10, size=n_rows),
            'BEDROOMS': np.random.randint(1, 5, size=n_rows),
            'BATHROOMS': np.random.randint(1, 4, size=n_rows),
            'PRICE_PER_NIGHT_TAG': np.random.choice(tags, size=n_rows, p=[0.35, 0.45, 0.20]),
            'HOST_NAME': [f"Host_{i%100}" for i in range(n_rows)],
            'IS_SUPERHOST': np.random.choice([True, False], size=n_rows, p=[0.38, 0.62]),
            'RESPONSE_RATE_QUALITY': np.random.choice(['very good', 'good', 'fair', 'poor'], size=n_rows, p=[0.55, 0.25, 0.15, 0.05])
        })
        
    df['BOOKING_DATE'] = pd.to_datetime(df['BOOKING_DATE'])
    return df

df_raw = get_gold_data()

# ---------------------------------------------------------
# SIDEBAR: INTERACTIVE CONTROLS & FILTERING
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/6/69/Airbnb_Logo_B%C3%A9lo.svg", width=140)
    st.markdown("### 🎛️ Analytics Controls")
    
    # Date Range Filter
    min_date = df_raw['BOOKING_DATE'].min().date()
    max_date = df_raw['BOOKING_DATE'].max().date()
    
    date_range = st.date_input(
        "Select Booking Window",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # City Multi-Select
    city_options = sorted(df_raw['CITY'].dropna().unique())
    selected_cities = st.multiselect("Filter Cities", options=city_options, default=city_options)
    
    # Room Type Multi-Select
    room_options = sorted(df_raw['ROOM_TYPE'].dropna().unique())
    selected_rooms = st.multiselect("Room Category", options=room_options, default=room_options)
    
    # Price Tier Filter
    tier_options = ['low', 'medium', 'high']
    selected_tiers = st.multiselect("Price Tiers", options=tier_options, default=tier_options)
    
    # Superhost Toggle
    superhost_only = st.checkbox("⭐ Superhosts Only", value=False)
    
    st.markdown("---")
    st.caption("⚡ **Medallion Pipeline**: Ingested via S3 ➔ Snowflake Staging ➔ dbt Silver Upsert ➔ Gold Star/OBT.")

# Apply Filters
df = df_raw.copy()

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_dt, end_dt = date_range
    df = df[(df['BOOKING_DATE'].dt.date >= start_dt) & (df['BOOKING_DATE'].dt.date <= end_dt)]

if selected_cities:
    df = df[df['CITY'].isin(selected_cities)]
if selected_rooms:
    df = df[df['ROOM_TYPE'].isin(selected_rooms)]
if selected_tiers:
    df = df[df['PRICE_PER_NIGHT_TAG'].isin(selected_tiers)]
if superhost_only:
    df = df[df['IS_SUPERHOST'] == True]

# Color Palette
AIRBNB_RED = "#FF5A5F"
AIRBNB_TEAL = "#00A699"
AIRBNB_ORANGE = "#FC642D"
AIRBNB_DARK = "#484848"
COLOR_SCALE = [AIRBNB_TEAL, "#FFB400", AIRBNB_RED, AIRBNB_ORANGE]

# ---------------------------------------------------------
# HEADER SECTION
# ---------------------------------------------------------
st.markdown("""
<div class="header-box">
    <h1 style="margin-bottom: 4px; font-weight: 800;">🏠 Airbnb Executive Performance Hub</h1>
    <p style="color: #717171; font-size: 1.05rem; margin: 0;">
        Real-time telemetry powered by <b>Snowflake Cloud Data Warehouse</b> & <b>dbt Medallion Architecture</b>
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# KPI SUMMARY CARDS
# ---------------------------------------------------------
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

total_revenue = df['TOTAL_AMOUNT'].sum()
total_bookings = len(df)
avg_nightly_price = df['PRICE_PER_NIGHT'].mean()
superhost_pct = (df['IS_SUPERHOST'].mean() * 100) if len(df) > 0 else 0
total_fees = (df['CLEANING_FEE'] + df['SERVICE_FEE']).sum()

def render_kpi(col, label, value, delta_text=""):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-delta">{delta_text}</div>
    </div>
    """, unsafe_allow_html=True)

render_kpi(kpi1, "Gross Revenue", f"${total_revenue:,.0f}", "▲ Live Ingestion")
render_kpi(kpi2, "Total Bookings", f"{total_bookings:,}", "▲ Validated")
render_kpi(kpi3, "Avg Nightly Rate", f"${avg_nightly_price:.2f}", "Macro Dynamic Tag")
render_kpi(kpi4, "Superhost Share", f"{superhost_pct:.1f}%", "SCD Type-2 Dim")
render_kpi(kpi5, "Ancillary Fees", f"${total_fees:,.0f}", "Cleaning & Service")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# DASHBOARD TABS
# ---------------------------------------------------------
tab_overview, tab_market, tab_hosts, tab_data = st.tabs([
    "📈 Revenue & Demand Trends",
    "🗺️ Geospatial & Pricing Dynamics",
    "⭐ Host Ecosystem & Quality",
    "🔍 Gold Data Explorer & Lineage"
])

# ---------------------------------------------------------
# TAB 1: REVENUE & DEMAND TRENDS
# ---------------------------------------------------------
with tab_overview:
    row1_c1, row1_c2 = st.columns([7, 3])
    
    with row1_c1:
        # Time-series trend (Revenue + Booking Volume)
        df_time = df.set_index('BOOKING_DATE').resample('W-MON').agg(
            weekly_revenue=('TOTAL_AMOUNT', 'sum'),
            weekly_bookings=('BOOKING_ID', 'count')
        ).reset_index()
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=df_time['BOOKING_DATE'],
            y=df_time['weekly_revenue'],
            name="Weekly Revenue ($)",
            marker_color=AIRBNB_RED,
            opacity=0.85,
            yaxis="y"
        ))
        fig_trend.add_trace(go.Scatter(
            x=df_time['BOOKING_DATE'],
            y=df_time['weekly_bookings'],
            name="Booking Volume",
            mode="lines+markers",
            line=dict(color=AIRBNB_TEAL, width=3),
            yaxis="y2"
        ))
        fig_trend.update_layout(
            title="<b>Weekly Revenue & Booking Velocity</b>",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(title="Revenue ($)", showgrid=True, gridcolor="#f0f0f0"),
            yaxis2=dict(title="Bookings Count", overlaying="y", side="right", showgrid=False),
            margin=dict(l=20, r=20, t=50, b=20),
            height=380
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with row1_c2:
        # Revenue Breakdown by Room Type (Donut)
        fig_room = px.pie(
            df,
            names='ROOM_TYPE',
            values='TOTAL_AMOUNT',
            title="<b>Revenue by Room Class</b>",
            hole=0.55,
            color_discrete_sequence=[AIRBNB_RED, AIRBNB_TEAL, "#FFB400", AIRBNB_DARK]
        )
        fig_room.update_traces(textposition='inside', textinfo='percent+label')
        fig_room.update_layout(
            template="plotly_white",
            showlegend=False,
            margin=dict(l=10, r=10, t=50, b=10),
            height=380
        )
        st.plotly_chart(fig_room, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Secondary Revenue Breakdown
    row2_c1, row2_c2 = st.columns(2)
    
    with row2_c1:
        # Revenue by Property Type
        prop_rev = df.groupby('PROPERTY_TYPE')['TOTAL_AMOUNT'].sum().reset_index().sort_values(by='TOTAL_AMOUNT', ascending=True)
        fig_prop = px.bar(
            prop_rev,
            x='TOTAL_AMOUNT',
            y='PROPERTY_TYPE',
            orientation='h',
            title="<b>Revenue Contribution by Property Type</b>",
            color='TOTAL_AMOUNT',
            color_continuous_scale=[AIRBNB_TEAL, AIRBNB_RED],
            template="plotly_white"
        )
        fig_prop.update_layout(
            coloraxis_showscale=False,
            xaxis_title="Gross Amount ($)",
            yaxis_title="",
            margin=dict(l=10, r=10, t=40, b=10),
            height=320
        )
        st.plotly_chart(fig_prop, use_container_width=True)

    with row2_c2:
        # Booking Status Funnel/Share
        status_df = df['BOOKING_STATUS'].value_counts().reset_index()
        fig_status = px.bar(
            status_df,
            x='BOOKING_STATUS',
            y='count',
            title="<b>Booking Lifecycle Status Distribution</b>",
            color='BOOKING_STATUS',
            color_discrete_map={'confirmed': AIRBNB_TEAL, 'cancelled': AIRBNB_RED, 'pending': '#FFB400'},
            template="plotly_white"
        )
        fig_status.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="Record Count",
            margin=dict(l=10, r=10, t=40, b=10),
            height=320
        )
        st.plotly_chart(fig_status, use_container_width=True)

# ---------------------------------------------------------
# TAB 2: GEOSPATIAL & PRICING DYNAMICS
# ---------------------------------------------------------
with tab_market:
    geo_c1, geo_c2 = st.columns([5, 5])
    
    with geo_c1:
        # City Performance Matrix
        city_metrics = df.groupby('CITY').agg(
            Gross_Revenue=('TOTAL_AMOUNT', 'sum'),
            Avg_Nightly_Rate=('PRICE_PER_NIGHT', 'mean'),
            Total_Stays=('BOOKING_ID', 'count')
        ).reset_index().sort_values(by='Gross_Revenue', ascending=False)
        
        fig_city = px.bar(
            city_metrics,
            x='CITY',
            y='Gross_Revenue',
            color='Avg_Nightly_Rate',
            title="<b>Metropolitan Market Sizing & Price Intensity</b>",
            color_continuous_scale='Reds',
            text_auto='.2s',
            template="plotly_white"
        )
        fig_city.update_layout(
            xaxis_title="",
            yaxis_title="Total Revenue ($)",
            coloraxis_colorbar_title="Avg Rate ($)",
            margin=dict(l=10, r=10, t=40, b=10),
            height=360
        )
        st.plotly_chart(fig_city, use_container_width=True)
        
    with geo_c2:
        # Price Distribution by Tag (Box Plot)
        fig_box = px.box(
            df,
            x='PRICE_PER_NIGHT_TAG',
            y='PRICE_PER_NIGHT',
            color='PRICE_PER_NIGHT_TAG',
            category_orders={'PRICE_PER_NIGHT_TAG': ['low', 'medium', 'high']},
            color_discrete_map={'low': AIRBNB_TEAL, 'medium': '#FFB400', 'high': AIRBNB_RED},
            title="<b>Price Per Night Variance by Macro-Tier</b>",
            template="plotly_white"
        )
        fig_box.update_layout(
            showlegend=False,
            xaxis_title="dbt Macro Tag Tier",
            yaxis_title="Nightly Price ($)",
            margin=dict(l=10, r=10, t=40, b=10),
            height=360
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # Capacity Correlation Scatter Plot
    fig_scatter = px.scatter(
        df,
        x='ACCOMMODATES',
        y='PRICE_PER_NIGHT',
        color='ROOM_TYPE',
        size='BEDROOMS',
        hover_data=['CITY', 'PROPERTY_TYPE'],
        title="<b>Capacity Elasticity: Guest Headcount vs. Nightly Pricing</b>",
        color_discrete_sequence=[AIRBNB_RED, AIRBNB_TEAL, AIRBNB_ORANGE, AIRBNB_DARK],
        template="plotly_white"
    )
    fig_scatter.update_layout(
        xaxis_title="Guest Capacity (Accommodates)",
        yaxis_title="Price Per Night ($)",
        height=380,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# ---------------------------------------------------------
# TAB 3: HOST ECOSYSTEM & QUALITY
# ---------------------------------------------------------
with tab_hosts:
    host_c1, host_c2 = st.columns(2)
    
    with host_c1:
        # Superhost vs Regular Host Comparison
        sh_analysis = df.groupby('IS_SUPERHOST').agg(
            Avg_Price=('PRICE_PER_NIGHT', 'mean'),
            Avg_Total_Amount=('TOTAL_AMOUNT', 'mean'),
            Booking_Count=('BOOKING_ID', 'count')
        ).reset_index()
        sh_analysis['Host_Status'] = sh_analysis['IS_SUPERHOST'].map({True: 'Superhost ⭐', False: 'Standard Host'})
        
        fig_sh = px.bar(
            sh_analysis,
            x='Host_Status',
            y='Avg_Price',
            color='Host_Status',
            color_discrete_map={'Superhost ⭐': AIRBNB_RED, 'Standard Host': AIRBNB_DARK},
            title="<b>Superhost Pricing Premium (Average ADR)</b>",
            text_auto='$.2f',
            template="plotly_white"
        )
        fig_sh.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="Avg Price / Night ($)",
            height=350,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_sh, use_container_width=True)
        
    with host_c2:
        # Response Rate Quality Distribution
        quality_counts = df['RESPONSE_RATE_QUALITY'].value_counts().reset_index()
        fig_qual = px.funnel(
            quality_counts,
            y='RESPONSE_RATE_QUALITY',
            x='count',
            title="<b>Host Communication Quality Cohorts</b>",
            color='RESPONSE_RATE_QUALITY',
            color_discrete_sequence=px.colors.sequential.Tealgrn_r
        )
        fig_qual.update_layout(
            showlegend=False,
            height=350,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_qual, use_container_width=True)

# ---------------------------------------------------------
# TAB 4: DATA EXPLORER & METADATA
# ---------------------------------------------------------
with tab_data:
    st.markdown("### 📋 Snowflake Gold Table Viewer (`AIRBNB.GOLD.OBT`)")
    
    col_search, col_download = st.columns([7, 3])
    with col_search:
        search_query = st.text_input("🔍 Quick Search (Host Name, Booking ID, or City)", "")
    with col_download:
        st.markdown("<br>", unsafe_allow_html=True)
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Filtered Gold CSV",
            data=csv_data,
            file_name="snowflake_gold_airbnb_export.csv",
            mime="text/csv"
        )
        
    filtered_view = df.copy()
    if search_query:
        mask = (
            filtered_view['HOST_NAME'].astype(str).str.contains(search_query, case=False, na=False) |
            filtered_view['BOOKING_ID'].astype(str).str.contains(search_query, case=False, na=False) |
            filtered_view['CITY'].astype(str).str.contains(search_query, case=False, na=False)
        )
        filtered_view = filtered_view[mask]
        
    st.dataframe(
        filtered_view,
        use_container_width=True,
        column_config={
            "TOTAL_AMOUNT": st.column_config.NumberColumn("Total ($)", format="$%.2f"),
            "PRICE_PER_NIGHT": st.column_config.NumberColumn("Rate ($)", format="$%.2f"),
            "CLEANING_FEE": st.column_config.NumberColumn("Cleaning ($)", format="$%.2f"),
            "SERVICE_FEE": st.column_config.NumberColumn("Service ($)", format="$%.2f"),
            "IS_SUPERHOST": st.column_config.CheckboxColumn("Superhost?"),
            "BOOKING_DATE": st.column_config.DateColumn("Booking Date", format="YYYY-MM-DD")
        },
        height=450
    )
    
    st.markdown("---")
    st.markdown("""
    #### 🏗️ Medallion Architecture Summary
    - **Bronze Layer (`AIRBNB.BRONZE`)**: Ingested incrementally from AWS S3 via Snowflake Stages.
    - **Silver Layer (`AIRBNB.SILVER`)**: Standardized with Jinja macros (`tag.sql`, `multiply.sql`) and deduplicated via `unique_key` upserts.
    - **Gold Layer (`AIRBNB.GOLD`)**: Denormalized OBT generated dynamically via Jinja array loop + Star Schema Fact & Snapshots (SCD Type-2).
    """)