import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import os

# 1. Konfigurasi Halaman & Branding Apple Light Mode
st.set_page_config(
    page_title="iBox Retail Sales Analytics",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Apple Light Mode & SF Pro Custom CSS
st.markdown("""
    <style>
    /* Clean White Background & Official Apple Typography */
    .stApp {
        background-color: #f5f5f7;
        color: #1d1d1f;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif;
    }
    
    /* Header Card Premium White */
    .apple-header-card {
        background: #ffffff;
        border: 1px solid #d2d2d7;
        border-radius: 18px;
        padding: 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .apple-badge {
        background-color: #0071e3;
        color: #ffffff;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 8px;
    }

    /* Metric Cards - Minimalist Apple Style */
    div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 700 !important;
        color: #1d1d1f !important;
        letter-spacing: -0.5px;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #86868b !important;
        font-weight: 500 !important;
        font-size: 13px !important;
    }
    
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e5e5ea;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.03);
        transition: all 0.2s ease-in-out;
    }
    
    div[data-testid="metric-container"]:hover {
        border-color: #0071e3;
        box-shadow: 0 4px 16px rgba(0, 113, 227, 0.12);
        transform: translateY(-2px);
    }
    
    /* Sidebar Clean Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e5ea;
    }
    
    /* Custom Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 10px;
        color: #1d1d1f;
        padding: 8px 16px;
        border: 1px solid #e5e5ea;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0071e3 !important;
        color: #ffffff !important;
        border-color: #0071e3 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Header Dashboard dengan Logo Apple 3D
st.markdown("""
    <div class="apple-header-card">
        <div style="flex-grow: 1;">
            <span class="apple-badge">iBox Regional Executive Dashboard</span>
            <h1 style="margin: 0; font-size: 32px; font-weight: 700; color: #1d1d1f; letter-spacing: -0.8px;">
                Retail Sales & Performance Analytics
            </h1>
            <p style="margin: 6px 0 0 0; color: #86868b; font-size: 15px; font-weight: 400;">
                Real-time multi-store monitoring across Apple ecosystem categories (iPhone • Mac • iPad • Watch • Accessories)
            </p>
        </div>
        <div style="margin-left: 20px;">
            <img src="https://img.icons8.com/3d-fluency/94/apple-logo.png" width="70" alt="Apple 3D Logo" style="filter: drop-shadow(0px 8px 16px rgba(0,0,0,0.15));">
        </div>
    </div>
""", unsafe_allow_html=True)

# 4. Sidebar Data Management
st.sidebar.markdown("### ⚙️ Control Panel")

uploaded_file = st.sidebar.file_uploader("Upload Data POS (Opsional)", type=["xlsx", "xls", "parquet"])

data_source = None
if uploaded_file is not None:
    data_source = uploaded_file
    st.sidebar.success("✅ File Manual Terdeteksi")
elif os.path.exists("data_dashboard.parquet"):
    data_source = "data_dashboard.parquet"
    st.sidebar.info("📁 Dataset Parquet (Ultra Fast)")
elif os.path.exists("Data Dashboard.xlsx"):
    data_source = "Data Dashboard.xlsx"
    st.sidebar.info("📁 Dataset: Data Dashboard.xlsx")

# 5. Load Data Fast Function
@st.cache_data(ttl=3600, show_spinner="Memproses data...")
def load_data(source):
    try:
        if isinstance(source, str) and source.endswith(".parquet"):
            df = pd.read_parquet(source)
        else:
            df = pd.read_excel(source, engine="calamine")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Gagal memuat dataset: {e}")
        return None

if data_source is not None:
    raw_df = load_data(data_source)
    
    if raw_df is not None:
        con = duckdb.connect(database=':memory:')
        con.register("pos_data", raw_df)
        
        cols = [c.lower() for c in raw_df.columns]
        
        # Sidebar Filters
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔍 Filter Data")
        
        store_col = raw_df.columns[cols.index("store")] if "store" in cols else raw_df.columns[0]
        cat_col = raw_df.columns[cols.index("category")] if "category" in cols else (raw_df.columns[1] if len(raw_df.columns) > 1 else raw_df.columns[0])
        
        stores = [r[0] for r in con.query(f"SELECT DISTINCT \"{store_col}\" FROM pos_data WHERE \"{store_col}\" IS NOT NULL").fetchall()]
        categories = [r[0] for r in con.query(f"SELECT DISTINCT \"{cat_col}\" FROM pos_data WHERE \"{cat_col}\" IS NOT NULL").fetchall()]
        
        selected_stores = st.sidebar.multiselect("Pilih Store / Toko", options=stores, default=stores)
        selected_categories = st.sidebar.multiselect("Pilih Kategori Produk", options=categories, default=categories)
        
        # SQL Where Conditions
        where_conditions = ["1=1"]
        if selected_stores:
            s_list = "', '".join([str(s).replace("'", "''") for s in selected_stores])
            where_conditions.append(f"\"{store_col}\" IN ('{s_list}')")
        if selected_categories:
            c_list = "', '".join([str(c).replace("'", "''") for c in selected_categories])
            where_conditions.append(f"\"{cat_col}\" IN ('{c_list}')")
            
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        rev_candidates = [c for c in raw_df.columns if "rev" in c.lower() or "sales" in c.lower() or "total" in c.lower() or "amount" in c.lower()]
        qty_candidates = [c for c in raw_df.columns if "qty" in c.lower() or "quantity" in c.lower() or "unit" in c.lower()]
        
        rev_col = rev_candidates[0] if rev_candidates else raw_df.columns[-1]
        qty_col = qty_candidates[0] if qty_candidates else raw_df.columns[-2]
        
        # Executive KPI Cards
        total_rev = con.query(f"SELECT SUM(TRY_CAST(\"{rev_col}\" AS DOUBLE)) FROM pos_data {where_clause}").fetchone()[0] or 0
        total_qty = con.query(f"SELECT SUM(TRY_CAST(\"{qty_col}\" AS DOUBLE)) FROM pos_data {where_clause}").fetchone()[0] or 0
        total_rows = con.query(f"SELECT COUNT(*) FROM pos_data {where_clause}").fetchone()[0] or 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Revenue", f"Rp {total_rev:,.0f}")
        col2.metric("Units Sold", f"{total_qty:,.0f} Pcs")
        col3.metric("Active Stores", f"{len(selected_stores)} Toko")
        col4.metric("Total Transaksi/Rows", f"{total_rows:,.0f}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Apple Light Mode Clean Visualizations
        tab1, tab2, tab3 = st.tabs(["🏪 Kinerja Store", "📱 Breakdown Kategori", "📄 Raw Data Inspector"])
        
        with tab1:
            st.markdown("<h4 style='color: #1d1d1f; font-weight: 600;'>Kinerja Penjualan per Store</h4>", unsafe_allow_html=True)
            store_df = con.query(f"""
                SELECT "{store_col}" as Store, SUM(TRY_CAST("{rev_col}" AS DOUBLE)) as Revenue
                FROM pos_data
                {where_clause}
                GROUP BY "{store_col}"
                ORDER BY Revenue DESC
            """).df()
            
            fig_store = px.bar(
                store_df, x="Store", y="Revenue", text_auto=".2s",
                color="Revenue", color_continuous_scale=["#e5e5ea", "#0071e3", "#003666"],
                template="plotly_white"
            )
            fig_store.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="-apple-system, sans-serif", color="#1d1d1f"),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#e5e5ea")
            )
            st.plotly_chart(fig_store, use_container_width=True)
            
        with tab2:
            st.markdown("<h4 style='color: #1d1d1f; font-weight: 600;'>Proporsi Penjualan Kategori Produk</h4>", unsafe_allow_html=True)
            cat_df = con.query(f"""
                SELECT "{cat_col}" as Category, SUM(TRY_CAST("{rev_col}" AS DOUBLE)) as Revenue
                FROM pos_data
                {where_clause}
                GROUP BY "{cat_col}"
                ORDER BY Revenue DESC
            """).df()
            
            fig_cat = px.pie(
                cat_df, names="Category", values="Revenue", hole=0.55,
                color_discrete_sequence=["#0071e3", "#34c759", "#ff9500", "#af52de", "#5856d6", "#ff2d55"],
                template="plotly_white"
            )
            fig_cat.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="-apple-system, sans-serif", color="#1d1d1f")
            )
            st.plotly_chart(fig_cat, use_container_width=True)
            
        with tab3:
            st.markdown("<h4 style='color: #1d1d1f; font-weight: 600;'>Data Inspector (Pratinjau 200 Baris Pertama)</h4>", unsafe_allow_html=True)
            preview_df = con.query(f"SELECT * FROM pos_data {where_clause} LIMIT 200").df()
            st.dataframe(preview_df, use_container_width=True)
else:
    st.warning("⚠️ Dataset belum terdeteksi.")