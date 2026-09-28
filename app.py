import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import os

# 1. Konfigurasi Halaman & Tampilan
st.set_page_config(
    page_title="iBox Retail Sales Analytics",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apple Dark Aesthetic Styling
st.markdown("""
    <style>
    .main {
        background-color: #0d0d0d;
        color: #f5f5f7;
    }
    stMetric {
        background-color: #1c1c1e;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #2c2c2e;
    }
    .stSelectbox, .stSlider {
        color: #f5f5f7;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🍎 iBox Retail Sales Analytics Dashboard")
st.caption("Regional Store Performance & Multi-Category Sales Analytics")

# 2. Sidebar & Sumber Data
st.sidebar.header("⚙️ Data & Filter Settings")

uploaded_file = st.sidebar.file_uploader("Upload File Excel POS (Opsional)", type=["xlsx", "xls"])

data_source = None

# Prioritas 1: File yang di-upload manual
if uploaded_file is not None:
    data_source = uploaded_file
    st.sidebar.success("Menggunakan file Excel yang di-upload.")
# Prioritas 2: File default 'Data Dashboard.xlsx' di repository
elif os.path.exists("Data Dashboard.xlsx"):
    data_source = "Data Dashboard.xlsx"
    st.sidebar.info("Menggunakan data default: 'Data Dashboard.xlsx'")
elif os.path.exists("Data Dashboard.xls"):
    data_source = "Data Dashboard.xls"
    st.sidebar.info("Menggunakan data default: 'Data Dashboard.xls'")

# 3. Fungsi Load & Process Data dengan Caching (Optimasi Memori)
@st.cache_data(ttl=3600, show_spinner="Memuat dan memproses data Excel...")
def load_data(source):
    try:
        # Menggunakan engine 'calamine' untuk membaca file Excel ukuran besar dengan cepat
        df = pd.read_excel(source, engine="calamine")
        
        # Bersihkan nama kolom (hilangkan spasi berlebih)
        df.columns = df.columns.str.strip()
        
        return df
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        return None

if data_source is not None:
    raw_df = load_data(data_source)
    
    if raw_df is not None:
        # Registrasi DataFrame ke DuckDB
        duckdb.register("pos_data", raw_df)
        
        # --- SIDEBAR FILTERS ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔍 Filter Data")
        
        # Ambil daftar filter unik dari dataset menggunakan DuckDB
        stores = [row[0] for row in duckdb.query("SELECT DISTINCT Store FROM pos_data WHERE Store IS NOT NULL").fetchall()]
        categories = [row[0] for row in duckdb.query("SELECT DISTINCT Category FROM pos_data WHERE Category IS NOT NULL").fetchall()]
        
        selected_stores = st.sidebar.multiselect("Pilih Store / Toko", options=stores, default=stores)
        selected_categories = st.sidebar.multiselect("Pilih Kategori Produk", options=categories, default=categories)
        
        # Query Data Terfilter
        where_clause = "WHERE 1=1"
        if selected_stores:
            store_list = "', '".join(selected_stores)
            where_clause += f" AND Store IN ('{store_list}')"
        if selected_categories:
            cat_list = "', '".join(selected_categories)
            where_clause += f" AND Category IN ('{cat_list}')"
            
        filtered_query = f"""
            SELECT * FROM pos_data
            {where_clause}
        """
        filtered_df = duckdb.query(filtered_query).df()
        
        # --- METRIK UTAMA (KPI) ---
        st.markdown("### 📊 Ringkasan Eksekutif")
        col1, col2, col3, col4 = st.columns(4)
        
        total_revenue = duckdb.query(f"SELECT SUM(Revenue) FROM pos_data {where_clause}").fetchone()[0] or 0
        total_qty = duckdb.query(f"SELECT SUM(Qty) FROM pos_data {where_clause}").fetchone()[0] or 0
        total_tx = duckdb.query(f"SELECT COUNT(DISTINCT Transaction_ID) FROM pos_data {where_clause}").fetchone()[0] or 0
        avg_basket = (total_revenue / total_tx) if total_tx > 0 else 0
        
        col1.metric("Total Sales Revenue", f"Rp {total_revenue:,.0f}")
        col2.metric("Total Unit Terjual (Qty)", f"{total_qty:,.0f} Pcs")
        col3.metric("Total Transaksi", f"{total_tx:,.0f}")
        col4.metric("Avg Basket Size", f"Rp {avg_basket:,.0f}")
        
        st.markdown("---")
        
        # --- VISUALISASI ---
        st.markdown("### 📈 Visualisasi Kinerja Penjualan")
        
        tab1, tab2, tab3 = st.tabs(["Store Ranking", "Category Distribution", "Raw Data View"])
        
        with tab1:
            st.subheader("Penjualan Berdasarkan Store")
            store_sales = duckdb.query(f"""
                SELECT Store, SUM(Revenue) as Total_Revenue, SUM(Qty) as Total_Qty 
                FROM pos_data 
                {where_clause}
                GROUP BY Store 
                ORDER BY Total_Revenue DESC
            """).df()
            
            fig_store = px.bar(
                store_sales, 
                x="Store", 
                y="Total_Revenue", 
                color="Total_Revenue",
                text_auto='.2s',
                title="Ranking Penjualan Toko (Revenue)",
                template="plotly_dark",
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig_store, use_container_width=True)
            
        with tab2:
            st.subheader("Distribusi Kategori Produk")
            cat_sales = duckdb.query(f"""
                SELECT Category, SUM(Revenue) as Total_Revenue 
                FROM pos_data 
                {where_clause}
                GROUP BY Category 
                ORDER BY Total_Revenue DESC
            """).df()
            
            fig_cat = px.pie(
                cat_sales, 
                names="Category", 
                values="Total_Revenue", 
                title="Proporsi Penjualan per Kategori",
                template="plotly_dark",
                hole=0.4
            )
            st.plotly_chart(fig_cat, use_container_width=True)
            
        with tab3:
            st.subheader("Preview Data Pivot / Mentah")
            st.dataframe(filtered_df.head(500), use_container_width=True)

else:
    st.warning("⚠️ File 'Data Dashboard.xlsx' tidak ditemukan dan belum ada file yang di-upload.")
    st.info("Silakan salin file 'Data Dashboard.xlsx' ke folder proyek lalu jalankan `git push`.")