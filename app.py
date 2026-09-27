import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px

# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="iBox Retail Analytics",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS Professional Apple UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
        background-color: #f5f5f7 !important;
        color: #1d1d1f;
    }

    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 96%;
    }
    
    .app-header {
        background: linear-gradient(135deg, #ffffff 0%, #fbfbfd 100%);
        border-radius: 20px;
        padding: 24px 32px;
        border: 1px solid rgba(0, 0, 0, 0.06);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .app-title {
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.6px;
        color: #1d1d1f;
        margin: 0;
    }
    
    .app-subtitle {
        font-size: 13px;
        font-weight: 500;
        color: #86868b;
        margin-top: 4px;
    }

    .kpi-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px 24px;
        border: 1px solid #e5e5ea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        transition: all 0.2s ease-in-out;
    }
    
    .kpi-card:hover {
        box-shadow: 0 6px 20px rgba(0,0,0,0.05);
        border-color: #0071e3;
    }
    
    .kpi-label {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #86868b;
        margin-bottom: 6px;
    }
    
    .kpi-value {
        font-size: 24px;
        font-weight: 700;
        color: #0071e3;
        letter-spacing: -0.8px;
    }

    .kpi-subtext {
        font-size: 12px;
        font-weight: 400;
        color: #86868b;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #e3e3e8;
        padding: 5px;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 38px;
        border-radius: 8px;
        padding: 0px 18px;
        font-weight: 500;
        font-size: 13px;
        color: #424245;
        border: none !important;
        background-color: transparent;
    }

    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #0071e3 !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        font-weight: 600;
    }

    section[data-testid="stSidebar"] {
        background-color: #fbfbfd;
        border-right: 1px solid #e5e5ea;
    }
</style>
""", unsafe_allow_html=True)

# 3. Header Banner
st.markdown("""
<div class="app-header">
    <div>
        <h1 class="app-title"> iBox Executive Retail Analytics</h1>
        <div class="app-subtitle">Interactive Daily Sales, Achievement & Store Performance Dashboard</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 4. Sidebar Upload
uploaded_file = st.sidebar.file_uploader("📂 Upload File Excel iBox", type=["xlsx", "xls"])

if uploaded_file is not None:
    # OPTIMISASI PEMBACAAN DATA DENGAN CALAMINE (Jauh lebih cepat)
    @st.cache_data(show_spinner=False)
    def load_data_fast(file):
        try:
            df = pd.read_excel(file, engine='calamine')
        except Exception:
            df = pd.read_excel(file)
        df.columns = df.columns.str.strip()
        return df

    with st.spinner("⚡ Mengunggah & Mengolah Data (Optimized Engine)..."):
        raw_df = load_data_fast(uploaded_file)
        
        con = duckdb.connect(database=':memory:')
        con.register('daily_sales', raw_df)
        
        cols_info = con.execute("PRAGMA table_info('daily_sales')").fetchall()
        cols = {c[1].lower().replace(" ", "_").replace("/", "_"): c[1] for c in cols_info}
        
        tsh_col = cols.get('tsh', 'tsh')
        site_col = cols.get('site_desc', 'site_desc')
        qty_col = next((cols[c] for c in ['quantity', 'qty'] if c in cols), 'quantity')
        rev_col = next((cols[c] for c in ['total_nett_amount_exc_tax', 'total_nett_am_exc_tax', 'total_nett_am_2', 'total_nett_am', 'price'] if c in cols), 'total_nett_amount_exc_tax')
        cat_col = next((cols[c] for c in ['cat', 'category', 'category_name', 'cat_name', 'kategori'] if c in cols), None)
        
        rofo_col = cols.get('acc_rofo', 'acc_rofo')
        if rofo_col not in cols and len(cols_info) >= 29:
            rofo_col = cols_info[28][1]
            
        brand_col = cols.get('brand_name', 'brand_name')

    # Sidebar Parameters
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### ⚙️ Column Parameters")
    st.sidebar.caption(f"**Value:** `{rev_col}`")
    if cat_col:
        st.sidebar.caption(f"**Category:** `{cat_col}`")
    st.sidebar.caption(f"**ACC ROFO:** `{rofo_col}`")

    # 5. Global Filters Sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 🔍 Time Filters")
    
    order_dates = [str(r[0]) for r in con.execute(f"SELECT DISTINCT \"{cols['order_date']}\" FROM daily_sales WHERE \"{cols['order_date']}\" IS NOT NULL ORDER BY 1").fetchall()] if 'order_date' in cols else []
    weeks = [str(r[0]) for r in con.execute(f"SELECT DISTINCT \"{cols['week']}\" FROM daily_sales WHERE \"{cols['week']}\" IS NOT NULL ORDER BY 1").fetchall()] if 'week' in cols else []
    months = [str(r[0]) for r in con.execute(f"SELECT DISTINCT \"{cols['month']}\" FROM daily_sales WHERE \"{cols['month']}\" IS NOT NULL ORDER BY 1").fetchall()] if 'month' in cols else []
    years = [str(r[0]) for r in con.execute(f"SELECT DISTINCT \"{cols['year']}\" FROM daily_sales WHERE \"{cols['year']}\" IS NOT NULL ORDER BY 1").fetchall()] if 'year' in cols else []

    sel_date = st.sidebar.multiselect("Order Date", options=order_dates, default=[])
    sel_week = st.sidebar.multiselect("Week", options=weeks, default=[])
    sel_month = st.sidebar.multiselect("Month", options=months, default=[])
    sel_year = st.sidebar.multiselect("Year", options=years, default=[])

    where_clauses = [f"\"{tsh_col}\" IS NOT NULL AND CAST(\"{tsh_col}\" AS VARCHAR) NOT IN ('#N/A', 'nan', '')"]
    if sel_date: where_clauses.append(f"CAST(\"{cols['order_date']}\" AS VARCHAR) IN ({','.join([repr(x) for x in sel_date])})")
    if sel_week: where_clauses.append(f"CAST(\"{cols['week']}\" AS VARCHAR) IN ({','.join([repr(x) for x in sel_week])})")
    if sel_month: where_clauses.append(f"CAST(\"{cols['month']}\" AS VARCHAR) IN ({','.join([repr(x) for x in sel_month])})")
    if sel_year: where_clauses.append(f"CAST(\"{cols['year']}\" AS VARCHAR) IN ({','.join([repr(x) for x in sel_year])})")

    base_where = " WHERE " + " AND ".join(where_clauses)

    # 6. Top Executive KPI Cards Summary
    q_kpi = f"SELECT SUM(\"{qty_col}\") as Total_Qty, SUM(\"{rev_col}\") as Total_Val FROM daily_sales {base_where}"
    res_kpi = con.execute(q_kpi).fetchone()
    grand_qty = res_kpi[0] if res_kpi and res_kpi[0] else 0
    grand_val = res_kpi[1] if res_kpi and res_kpi[1] else 0

    q_stores = f"SELECT COUNT(DISTINCT \"{site_col}\") FROM daily_sales {base_where}"
    active_stores = con.execute(q_stores).fetchone()[0]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Volume Sold</div>
            <div class="kpi-value">{grand_qty:,.0f} <span class="kpi-subtext">Units</span></div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Net Revenue (Exc. Tax)</div>
            <div class="kpi-value">Rp {grand_val:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Active Store Network</div>
            <div class="kpi-value">{active_stores} <span class="kpi-subtext">Outlets</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # 7. Executive Visual Chart Section
    show_charts = st.checkbox("📊 Tampilkan Graphic Analytics Summary", value=True)
    if show_charts:
        q_tsh_summary = f"""
            SELECT \"{tsh_col}\" as TSH, SUM(\"{qty_col}\") as Total_Qty, SUM(\"{rev_col}\") as Total_Val
            FROM daily_sales {base_where}
            GROUP BY \"{tsh_col}\"
            ORDER BY Total_Val DESC
        """
        df_tsh_summary = con.execute(q_tsh_summary).df()
        
        col_chart1, col_chart2 = st.columns([1, 1])
        
        with col_chart1:
            fig_pie = px.pie(
                df_tsh_summary, 
                values='Total_Val', 
                names='TSH', 
                hole=0.5,
                title="<b>Revenue Share per TSH Group</b>",
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=280)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_chart2:
            fig_bar = px.bar(
                df_tsh_summary, 
                x='TSH', 
                y='Total_Val', 
                text_auto='.2s',
                title="<b>Revenue Comparison by TSH</b>",
                color='Total_Val',
                color_continuous_scale='Blues'
            )
            fig_bar.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=280, coloraxis_showscale=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")

    # 8. Tampilan 4 Tab utama
    tab1, tab2, tab3, tab4 = st.tabs(["All Categories", "ACC ROFO", "Boltech", "Operator (Brand)"])

    def render_grouped_tsh_table(extra_sql=""):
        full_where = base_where + (f" AND {extra_sql}" if extra_sql else "")
        
        q = f"""
            SELECT \"{tsh_col}\" as TSH, \"{site_col}\" as Store, SUM(\"{qty_col}\") as Qty, SUM(\"{rev_col}\") as Value
            FROM daily_sales {full_where}
            GROUP BY \"{tsh_col}\", \"{site_col}\"
            ORDER BY TSH, Value DESC
        """
        df_raw = con.execute(q).df()
        
        if df_raw.empty:
            st.info("Tidak ada data yang sesuai dengan kriteria filter.")
            return

        tsh_list = df_raw['TSH'].unique()
        
        for tsh_name in tsh_list:
            df_tsh = df_raw[df_raw['TSH'] == tsh_name]
            total_qty = df_tsh['Qty'].sum()
            total_val = df_tsh['Value'].sum()

            with st.expander(f"👤 **TSH: {tsh_name}** &nbsp;•&nbsp; Total Units: **{total_qty:,.0f}** &nbsp;•&nbsp; Total Revenue: **Rp {total_val:,.0f}**", expanded=True):
                df_store = df_tsh[['Store', 'Qty', 'Value']].copy()
                
                total_row = pd.DataFrame([{'Store': 'TOTAL', 'Qty': total_qty, 'Value': total_val}])
                df_store = pd.concat([df_store, total_row], ignore_index=True)

                df_store['Qty'] = df_store['Qty'].apply(lambda x: f"{x:,.0f}")
                df_store['Value'] = df_store['Value'].apply(lambda x: f"Rp {x:,.0f}")
                df_store.rename(columns={'Store': 'Store Name', 'Qty': 'Unit Sold (Qty)', 'Value': 'Revenue (Value)'}, inplace=True)
                
                st.dataframe(df_store, use_container_width=True, hide_index=True)

    def render_interleaved_pivot_table(query_sql, group_col_name, include_total_acc=False):
        df_data = con.execute(query_sql).df()
        if df_data.empty:
            st.info("Tidak ada data yang sesuai dengan kriteria filter.")
            return

        tsh_list = df_data['TSH'].unique()
        
        for tsh_name in tsh_list:
            df_sub = df_data[df_data['TSH'] == tsh_name]
            tsh_total_qty = df_sub['Qty'].sum()
            tsh_total_val = df_sub['Value'].sum()
            
            piv_qty = df_sub.pivot_table(index='Store', columns=group_col_name, values='Qty', aggfunc='sum', fill_value=0)
            piv_val = df_sub.pivot_table(index='Store', columns=group_col_name, values='Value', aggfunc='sum', fill_value=0)
            
            categories = sorted(list(set(piv_qty.columns).union(set(piv_val.columns))))
            
            df_combined = pd.DataFrame(index=piv_qty.index)
            
            for cat in categories:
                col_qty_name = f"{cat} (Qty)"
                col_val_name = f"{cat} (Value)"
                df_combined[col_qty_name] = piv_qty[cat] if cat in piv_qty.columns else 0
                df_combined[col_val_name] = piv_val[cat] if cat in piv_val.columns else 0
                
            if include_total_acc:
                df_combined['Total ACC (Qty)'] = piv_qty.sum(axis=1)
                df_combined['Total ACC (Value)'] = piv_val.sum(axis=1)
                
            total_series = df_combined.sum(axis=0)
            total_series.name = 'TOTAL'
            
            df_final = pd.concat([df_combined, pd.DataFrame([total_series])])
            df_final = df_final.reset_index().rename(columns={'index': 'Store Name'})
            
            for col in df_final.columns:
                if 'Value' in col:
                    df_final[col] = df_final[col].apply(lambda x: f"Rp {x:,.0f}")
                elif 'Qty' in col:
                    df_final[col] = df_final[col].apply(lambda x: f"{x:,.0f}")

            with st.expander(f"👤 **TSH: {tsh_name}** &nbsp;•&nbsp; Total Units: **{tsh_total_qty:,.0f}** &nbsp;•&nbsp; Total Revenue: **Rp {tsh_total_val:,.0f}**", expanded=True):
                st.dataframe(df_final, use_container_width=True, hide_index=True)

    # TAB 1: ALL CATEGORIES
    with tab1:
        st.caption("Overall Sales Performance across All Product Categories")
        if cat_col:
            q_cats = f"SELECT DISTINCT TRIM(CAST(\"{cat_col}\" AS VARCHAR)) FROM daily_sales WHERE \"{cat_col}\" IS NOT NULL AND TRIM(CAST(\"{cat_col}\" AS VARCHAR)) NOT IN ('#N/A', 'nan', 'None', '') ORDER BY 1"
            all_cats = [str(r[0]) for r in con.execute(q_cats).fetchall()]
            
            sel_cat = st.multiselect("Filter Specific Category", options=all_cats, default=[])
            cat_where = f"CAST(\"{cat_col}\" AS VARCHAR) IN ({','.join([repr(x) for x in sel_cat])})" if sel_cat else "1=1"
        else:
            cat_where = "1=1"

        render_grouped_tsh_table(cat_where)

    # TAB 2: ACC ROFO
    with tab2:
        st.caption("Detailed Breakdown for Accessories (Excludes Boltech & Operator)")
        rofo_where = f"""
            {base_where} 
            AND \"{rofo_col}\" IS NOT NULL 
            AND LOWER(CAST(\"{rofo_col}\" AS VARCHAR)) NOT IN ('none', 'nan', '#n/a', '')
            AND LOWER(CAST(\"{rofo_col}\" AS VARCHAR)) NOT LIKE '%boltech%'
            AND LOWER(CAST(\"{rofo_col}\" AS VARCHAR)) NOT LIKE '%operator%'
        """
        q_rofo = f"""
            SELECT \"{tsh_col}\" as TSH, \"{site_col}\" as Store, \"{rofo_col}\" as Rofo_Cat, SUM(\"{qty_col}\") as Qty, SUM(\"{rev_col}\") as Value
            FROM daily_sales {rofo_where}
            GROUP BY \"{tsh_col}\", \"{site_col}\", \"{rofo_col}\"
            ORDER BY TSH, Store
        """
        render_interleaved_pivot_table(q_rofo, 'Rofo_Cat', include_total_acc=True)

    # TAB 3: BOLTECH
    with tab3:
        st.caption("Boltech Warranty & Protection Services Performance")
        boltech_where = f"(LOWER(CAST(\"{rofo_col}\" AS VARCHAR)) LIKE '%boltech%' OR LOWER(CAST(\"{brand_col}\" AS VARCHAR)) LIKE '%boltech%')"
        render_grouped_tsh_table(boltech_where)

    # TAB 4: OPERATOR
    with tab4:
        st.caption("Operator Connectivity Package Sales Breakdown by Telco Provider")
        opr_where = f"{base_where} AND (LOWER(CAST(\"{rofo_col}\" AS VARCHAR)) LIKE '%operator%' OR LOWER(CAST(\"{cat_col}\" AS VARCHAR)) LIKE '%opr%')"
        q_opr = f"""
            SELECT \"{tsh_col}\" as TSH, \"{site_col}\" as Store, \"{brand_col}\" as Brand, SUM(\"{qty_col}\") as Qty, SUM(\"{rev_col}\") as Value
            FROM daily_sales {opr_where}
            GROUP BY \"{tsh_col}\", \"{site_col}\", \"{brand_col}\"
            ORDER BY TSH, Store
        """
        render_interleaved_pivot_table(q_opr, 'Brand', include_total_acc=False)

else:
    st.info("💡 Silakan upload file Excel daily sales iBox pada sidebar sebelah kiri untuk menampilkan analisis dashboard.")