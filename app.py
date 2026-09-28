import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import os

# 1. Konfigurasi Halaman & Branding Apple Premium
st.set_page_config(
    page_title="iBox Retail Analytics",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apple Premium Dark Aesthetic Styling (CSS)
st.markdown("""
    <style>
    /* Dark Background & Apple Typography */
    .stApp {
        background-color: #000000;
        color: #f5f5f7;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", sans-serif;
    }
    
    /* Executive Header Card */
    .apple-header {
        background: linear-gradient(135deg, #1c1c1e 0%, #0d0d0d 100%);
        border: 1px solid #2c2c2e;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
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
        margin-bottom: 10px;
    }

    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: 700 !important;
        color: #f5f5f7 !important;
    }
    
    div[data-testid="metric-container"] {
        background-color: #1c1c1e;
        border: 1px solid #2c2c2e;
        border-radius: 14px;
        padding: 16px;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #161617;
        border-right: 1px solid #2c2c2e;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Executive Header Tampilan
st.markdown("""
    <div class="apple-header">
        <span class="apple-badge">iBox Regional Executive Dashboard</span>
        <h1 style="margin:0; font-size: 30px; font-weight: 700; color: #ffffff;">
            📱 Retail Sales & Performance Analytics
        </h1>
        <p style="margin: 6px 0 0 0; color: #86868b; font-size: 14px;">
            Real-time multi-store monitoring across Apple ecosystem categories (iPhone • Mac • iPad • Watch • Accessories)
        </p>
    </div>
""", unsafe_allow_html=True)

# 3. Sidebar Data Management
st.sidebar.markdown("### ⚙️ Data Source & Controls")

uploaded_file = st.sidebar.file_uploader("Upload POS Data (Optional)", type=["xlsx", "xls"])

data_source = None

if uploaded_file is not None:
    data_source = uploaded_file
    st.sidebar.success("✅ File Manual Di-upload")
elif os.path.exists("Data Dashboard.xlsx"):
    data_source = "Data Dashboard.xlsx"
    st.sidebar.info("📁 Dataset Bawaan: Data Dashboard.xlsx")
elif os.path.exists("Data Dashboard.xls"):
    data_source = "Data Dashboard.xls"
    st.sidebar.info("📁 Dataset Bawaan: Data Dashboard.xls")

# 4. Fast Load dengan Calamine Engine & Caching
@st.cache_data(ttl=3600, show_spinner="Memuat Dataset Excel...")
def load_data_fast(source):
    try:
        df = pd.read_excel(source, engine="calamine")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error membaca file Excel: {e}")
        return None

if data_source is not None:
    raw_df = load_data_fast(data_source)
        
    if raw_df is not None:
        duckdb.register("pos_data", raw_df)
        
        cols = [c.lower() for c in raw_df.columns]
        
        # Sidebar Filters
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔍 Filters")
        
        store_col = raw_df.columns[cols.index("store")] if "store" in cols else raw_df.columns[0]
        cat_col = raw_df.columns[cols.index("category")] if "category" in cols else (raw_df.columns[1] if len(raw_df.columns) > 1 else raw_df.columns[0])
        
        stores = [r[0] for r in duckdb.query(f"SELECT DISTINCT \"{store_col}\" FROM pos_data WHERE \"{store_col}\" IS NOT NULL").fetchall()]
        categories = [r[0] for r in duckdb.query(f"SELECT DISTINCT \"{cat_col}\" FROM pos_data WHERE \"{cat_col}\" IS NOT NULL").fetchall()]
        
        selected_stores = st.sidebar.multiselect("Pilih Store / Toko", options=stores, default=stores)
        selected_categories = st.sidebar.multiselect("Pilih Kategori Produk", options=categories, default=categories)
        
        # SQL Filter
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
        
        # 5. Executive KPI Summary Cards
        total_rev = duckdb.query(f"SELECT SUM(TRY_CAST(\"{rev_col}\" AS DOUBLE)) FROM pos_data {where_clause}").fetchone()[0] or 0
        total_qty = duckdb.query(f"SELECT SUM(TRY_CAST(\"{qty_col}\" AS DOUBLE)) FROM pos_data {where_clause}").fetchone()[0] or 0
        total_rows = duckdb.query(f"SELECT COUNT(*) FROM pos_data {where_clause}").fetchone()[0] or 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Total Sales", f"Rp {total_rev:,.0f}")
        col2.metric("📦 Units Sold", f"{total_qty:,.0f} Pcs")
        col3.metric("🏪 Active Stores", f"{len(selected_stores)} Toko")
        col4.metric("🧾 Total Rows", f"{total_rows:,.0f}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 6. Visualizations
        tab1, tab2, tab3 = st.tabs(["🏪 Store Ranking", "📱 Category Breakdown", "📄 Data Inspector"])
        
        with tab1:
            st.markdown("#### 🏪 Kinerja Penjualan per Store")
            store_df = duckdb.query(f"""
                SELECT "{store_col}" as Store, SUM(TRY_CAST("{rev_col}" AS DOUBLE)) as Revenue
                FROM pos_data
                {where_clause}
                GROUP BY "{store_col}"
                ORDER BY Revenue DESC
            """).df()
            
            fig_store = px.bar(
                store_df,
                x="Store",
                y="Revenue",
                text_auto=".2s",
                color="Revenue",
                color_continuous_scale=["#1c1c1e", "#0071e3", "#2997ff"],
                template="plotly_dark"
            )
            fig_store.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="-apple-system, sans-serif", color="#f5f5f7"),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#2c2c2e")
            )
            st.plotly_chart(fig_store, use_container_width=True)
            
        with tab2:
            st.markdown("#### 📱 Proporsi Penjualan per Kategori Produk")
            cat_df = duckdb.query(f"""
                SELECT "{cat_col}" as Category, SUM(TRY_CAST("{rev_col}" AS DOUBLE)) as Revenue
                FROM pos_data
                {where_clause}
                GROUP BY "{cat_col}"
                ORDER BY Revenue DESC
            """).df()
            
            fig_cat = px.pie(
                cat_df,
                names="Category",
                values="Revenue",
                hole=0.55,
                color_discrete_sequence=["#0071e3", "#2997ff", "#64d2ff", "#30d158", "#ff9f0a", "#bf5af2"],
                template="plotly_dark"
            )
            fig_cat.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="-apple-system, sans-serif", color="#f5f5f7")
            )
            st.plotly_chart(fig_cat, use_container_width=True)
            
        with tab3:
            st.markdown("#### 📄 Inspection Data (First 300 Rows)")
            preview_df = duckdb.query(f"SELECT * FROM pos_data {where_clause} LIMIT 300").df()
            st.dataframe(preview_df, use_container_width=True)
            
else:
    st.warning("⚠️ File 'Data Dashboard.xlsx' belum terdeteksi.")