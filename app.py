import streamlit as st
import pandas as pd
import duckdb
import os

# 1. Konfigurasi Halaman & Design System Apple White
st.set_page_config(
    page_title="iBox Sales & Achievement Dashboard 2026",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling White Apple Clean Mode
st.markdown("""
    <style>
    .stApp {
        background-color: #f5f5f7;
        color: #1d1d1f;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", sans-serif;
    }
    
    /* Header Container */
    .apple-header {
        background: #ffffff;
        border: 1px solid #d2d2d7;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.03);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* Sidebar Information Boxes */
    .info-box-green {
        background-color: #e8f5e9;
        border-left: 4px solid #2e7d32;
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 12px;
        font-size: 12px;
        color: #1b5e20;
    }
    
    .info-box-blue {
        background-color: #e8eaf6;
        border-left: 4px solid #3f51b5;
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 12px;
        font-size: 12px;
        color: #1a237e;
    }
    
    /* Tab Navigation Style */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #d2d2d7;
        padding-bottom: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 8px;
        color: #1d1d1f;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
        border: 1px solid #e5e5ea;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #d32f2f !important;
        border-color: #d32f2f !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar White Background */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e5ea;
    }
    
    /* Expander / Group Header Styling */
    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        border-radius: 10px !important;
        border: 1px solid #e5e5ea !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Executive Header dengan Logo 3D
st.markdown("""
    <div class="apple-header">
        <div>
            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #1d1d1f; letter-spacing: -0.5px;">
                📱 iBox Sales & Achievement Dashboard 2026
            </h1>
            <p style="margin: 4px 0 0 0; color: #86868b; font-size: 14px;">
                Regional Store Performance & Multi-Category Sales Breakdown
            </p>
        </div>
        <div>
            <img src="https://img.icons8.com/3d-fluency/94/apple-logo.png" width="65" alt="Apple 3D Logo">
        </div>
    </div>
""", unsafe_allow_html=True)

# 3. Sidebar Controls & Instructions
st.sidebar.markdown("""
    <div class="info-box-green">
        📌 <b>Value memakai kolom:</b><br><code>total_nett_amount_exc_tax</code>
    </div>
    <div class="info-box-blue">
        📌 <b>Category memakai kolom:</b><br><code>CAT</code>
    </div>
    <div class="info-box-blue">
        📌 <b>ACC ROFO memakai:</b><br><code>ACC ROFO</code>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 🔍 Global Time Filters")

uploaded_file = st.sidebar.file_uploader("Upload POS Data (Optional)", type=["xlsx", "xls", "parquet"])

data_source = None
if uploaded_file is not None:
    data_source = uploaded_file
elif os.path.exists("data_dashboard.parquet"):
    data_source = "data_dashboard.parquet"
elif os.path.exists("Data Dashboard.xlsx"):
    data_source = "Data Dashboard.xlsx"

@st.cache_data(ttl=3600, show_spinner="Memuat Dataset Dashboard...")
def load_data(source):
    try:
        if isinstance(source, str) and source.endswith(".parquet"):
            df = pd.read_parquet(source)
        else:
            df = pd.read_excel(source, engine="calamine")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error membaca file data: {e}")
        return None

if data_source is not None:
    raw_df = load_data(data_source)
    
    if raw_df is not None:
        con = duckdb.connect(database=':memory:')
        con.register("pos_data", raw_df)
        
        # Deteksi Kolom Tanggal/Waktu
        cols_map = {c.lower(): c for c in raw_df.columns}
        
        date_col = cols_map.get("order date", cols_map.get("date", cols_map.get("order_date", None)))
        week_col = cols_map.get("week", None)
        month_col = cols_map.get("month", None)
        year_col = cols_map.get("year", None)
        tsh_col = cols_map.get("tsh", cols_map.get("tsh name", cols_map.get("tsh_name", raw_df.columns[0])))
        store_col = cols_map.get("store", cols_map.get("store_name", raw_df.columns[1]))
        val_col = cols_map.get("total_nett_amount_exc_tax", cols_map.get("value", raw_df.columns[-1]))
        cat_col = cols_map.get("cat", cols_map.get("category", raw_df.columns[2]))
        rofo_col = cols_map.get("acc rofo", cols_map.get("acc_rofo", cat_col))
        qty_col = cols_map.get("qty", cols_map.get("quantity", "1"))
        
        # Filters Sidebar UI
        selected_weeks = st.sidebar.multiselect("WEEK", options=sorted(raw_df[week_col].dropna().unique()) if week_col else [])
        selected_months = st.sidebar.multiselect("MONTH", options=sorted(raw_df[month_col].dropna().unique()) if month_col else [], default=["September"] if month_col and "September" in raw_df[month_col].values else [])
        selected_years = st.sidebar.multiselect("YEAR", options=sorted(raw_df[year_col].dropna().unique()) if year_col else [])
        
        # Build Filter Clause
        where_conds = ["1=1"]
        if selected_weeks and week_col:
            w_str = "', '".join([str(x) for x in selected_weeks])
            where_conds.append(f"\"{week_col}\" IN ('{w_str}')")
        if selected_months and month_col:
            m_str = "', '".join([str(x) for x in selected_months])
            where_conds.append(f"\"{month_col}\" IN ('{m_str}')")
        if selected_years and year_col:
            y_str = "', '".join([str(x) for x in selected_years])
            where_conds.append(f"\"{year_col}\" IN ('{y_str}')")
            
        where_clause = "WHERE " + " AND ".join(where_conds)

        # 4. TAB NAVIGATION TEPAT SEPERTI SEMULA
        tab1, tab2, tab3, tab4 = st.tabs([
            "Tab 1: All Categories", 
            "Tab 2: ACC ROFO (Pivot AC)", 
            "Tab 3: Boltech", 
            "Tab 4: Operator (Brand)"
        ])

        def render_pivot_view(title, category_filter_clause=""):
            st.markdown(f"### {title}")
            
            full_where = f"{where_clause} {category_filter_clause}"
            
            # Grouping berdasarkan TSH
            tsh_list = con.query(f"SELECT DISTINCT \"{tsh_col}\" FROM pos_data {full_where} WHERE \"{tsh_col}\" IS NOT NULL").fetchall()
            
            for tsh in tsh_list:
                tsh_name = tsh[0]
                tsh_where = f"{full_where} AND \"{tsh_col}\" = '{tsh_name}'"
                
                # Metric per TSH Header
                total_tsh_qty = con.query(f"SELECT SUM(TRY_CAST(\"{qty_col}\" AS DOUBLE)) FROM pos_data {tsh_where}").fetchone()[0] or 0
                total_tsh_val = con.query(f"SELECT SUM(TRY_CAST(\"{val_col}\" AS DOUBLE)) FROM pos_data {tsh_where}").fetchone()[0] or 0
                
                expander_label = f"👤 TSH: {tsh_name} | Total Qty: {total_tsh_qty:,.0f} | Total Value: Rp {total_tsh_val:,.0f}"
                
                with st.expander(expander_label, expanded=True):
                    # Query Pivot per Store
                    pivot_df = con.query(f"""
                        SELECT 
                            "{store_col}" as Store,
                            SUM(CASE WHEN "{rofo_col}" LIKE '%3rd Party%' THEN TRY_CAST("{qty_col}" AS DOUBLE) ELSE 0 END) as "3rd Party (Qty)",
                            SUM(CASE WHEN "{rofo_col}" LIKE '%Apple%' THEN TRY_CAST("{qty_col}" AS DOUBLE) ELSE 0 END) as "Apple (Qty)",
                            SUM(CASE WHEN "{rofo_col}" LIKE '%Boltech%' THEN TRY_CAST("{qty_col}" AS DOUBLE) ELSE 0 END) as "Boltech (Qty)",
                            SUM(CASE WHEN "{rofo_col}" LIKE '%Lifestyle%' THEN TRY_CAST("{qty_col}" AS DOUBLE) ELSE 0 END) as "Lifestyle (Qty)",
                            SUM(CASE WHEN "{rofo_col}" LIKE '%Operator%' THEN TRY_CAST("{qty_col}" AS DOUBLE) ELSE 0 END) as "Operator (Qty)",
                            SUM(CASE WHEN "{rofo_col}" LIKE '%Private Label%' THEN TRY_CAST("{qty_col}" AS DOUBLE) ELSE 0 END) as "Private Label (Qty)",
                            SUM(CASE WHEN "{rofo_col}" LIKE '%3rd Party%' THEN TRY_CAST("{val_col}" AS DOUBLE) ELSE 0 END) as "3rd Party (Value)",
                            SUM(CASE WHEN "{rofo_col}" LIKE '%Apple%' THEN TRY_CAST("{val_col}" AS DOUBLE) ELSE 0 END) as "Apple (Value)"
                        FROM pos_data
                        {tsh_where}
                        GROUP BY "{store_col}"
                    """).df()
                    
                    if not pivot_df.empty:
                        # Add Total Row
                        total_row = pd.DataFrame([{
                            "Store": "TOTAL",
                            "3rd Party (Qty)": pivot_df["3rd Party (Qty)"].sum(),
                            "Apple (Qty)": pivot_df["Apple (Qty)"].sum(),
                            "Boltech (Qty)": pivot_df["Boltech (Qty)"].sum(),
                            "Lifestyle (Qty)": pivot_df["Lifestyle (Qty)"].sum(),
                            "Operator (Qty)": pivot_df["Operator (Qty)"].sum(),
                            "Private Label (Qty)": pivot_df["Private Label (Qty)"].sum(),
                            "3rd Party (Value)": pivot_df["3rd Party (Value)"].sum(),
                            "Apple (Value)": pivot_df["Apple (Value)"].sum(),
                        }])
                        pivot_df = pd.concat([pivot_df, total_row], ignore_index=True)
                        
                        # Format Rupiah
                        pivot_df["3rd Party (Value)"] = pivot_df["3rd Party (Value)"].apply(lambda x: f"Rp {x:,.0f}")
                        pivot_df["Apple (Value)"] = pivot_df["Apple (Value)"].apply(lambda x: f"Rp {x:,.0f}")
                        
                        st.dataframe(pivot_df, use_container_width=True)
                    else:
                        st.info("Tidak ada data untuk TSH ini.")

        with tab1:
            render_pivot_view("Data All Categories Breakdown")

        with tab2:
            render_pivot_view("Data ACC ROFO Breakdown (Kolom AC)")

        with tab3:
            render_pivot_view("Data Boltech Performance", category_filter_clause=f"AND \"{cat_col}\" LIKE '%Boltech%'")

        with tab4:
            render_pivot_view("Data Operator (Brand) Performance", category_filter_clause=f"AND \"{cat_col}\" LIKE '%Operator%'")

else:
    st.warning("⚠️ File data belum terdeteksi. Silakan upload file Excel/Parquet di sidebar.")