import streamlit as st
import pandas as pd
import joblib
import os
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# CONFIGURATION & PAGE SETTING
# ==========================================
st.set_page_config(page_title="Earthquake Risk BI & ML", layout="wide", page_icon="🌍")

# Custom CSS untuk mempercantik tampilan UI dari kode pertama
st.markdown("""
    <style>
    .main-title { font-size:38px !important; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .sub-title { font-size:16px !important; color: #4B5563; margin-bottom: 30px; }
    .metric-box { background-color: #F3F4F6; padding: 20px; border-radius: 10px; border-left: 5px solid #3B82F6; }
    </style>
""", unsafe_allow_html=True)

st.title("🌍 Sistem ETL Pipeline, Machine Learning & BI Dashboard Gempa Bumi")
st.markdown("Dashboard interaktif untuk memantau historis bencana dan mensimulasikan risiko dampak gempa menggunakan *Random Forest Regressor*.")

# Konfigurasi Path
BASE_DIR = os.path.dirname(__file__)
DATA_PROC_DIR = os.path.join(BASE_DIR, 'data', 'processed', 'gempa_clean.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'src', 'model_earthquake.pkl')

@st.cache_data
def load_cached_data():
    if os.path.exists(DATA_PROC_DIR):
        df_loaded = pd.read_csv(DATA_PROC_DIR)
        # Standardisasi nama kolom jika ada perbedaan
        if 'Kabupaten_Terdampak' in df_loaded.columns:
            df_loaded = df_loaded.rename(columns={'Kabupaten_Terdampak': 'Daerah_Terdampak'})
        return df_loaded
    return pd.DataFrame()

df = load_cached_data()

# ==========================================
# SIDEBAR FILTER (BUSINESS INTELLIGENCE CONTROL) - Diambil dari Kode Pertama
# ==========================================
if not df.empty:
    st.sidebar.header("🕹️ BI Filter & Control")

    # Filter Rentang Magnitudo
    min_mag, max_mag = float(df['mag'].min()), float(df['mag'].max())
    selected_mag = st.sidebar.slider(
        "Pilih Rentang Magnitudo (Mw)", 
        min_value=min_mag, max_value=max_mag, 
        value=(4.5, max_mag), step=0.1
    )

    # Filter Berdasarkan Daerah Terdampak (Multi-select)
    all_regions = sorted(df['Daerah_Terdampak'].dropna().unique())
    if 'NONE' in all_regions: 
        all_regions.remove('NONE')

    selected_regions = st.sidebar.multiselect(
        "Pilih Wilayah Terdampak", 
        options=all_regions, 
        default=all_regions[:5] if len(all_regions) > 5 else all_regions
    )

    # Aplikasikan Filter ke Dataset untuk Tab BI Overview
    df_filtered = df[
        (df['mag'] >= selected_mag[0]) & 
        (df['mag'] <= selected_mag[1]) & 
        (df['Daerah_Terdampak'].isin(selected_regions))
    ]
else:
    df_filtered = pd.DataFrame()


# TABS NAVIGATION
tab1, tab2 = st.tabs(["📊 Business Intelligence Overview", "🤖 Simulator Risiko ML"])

# ==========================================
# TAB 1: BUSINESS INTELLIGENCE OVERVIEW (INTEGRATED FROM CODE 1)
# ==========================================
with tab1:
    st.header("Analisis Deskriptif Historis")
    if not df.empty:
        # Ekstrak dan Tampilkan Rentang Tahun
        if 'date' in df.columns:
            df_date = pd.to_datetime(df['date'], errors='coerce')
            if not df_date.isna().all():
                min_year = int(df_date.dt.year.min())
                max_year = int(df_date.dt.year.max())
                st.info(f"📅 **Rentang Data Historis Gempa:** Tahun {min_year} - {max_year}")
        
        st.subheader("📌 Key Performance Indicators (KPI)")
        
        # Hitung Metrik Agregat Utama berdasarkan data yang sudah difilter
        total_events = df_filtered['id'].nunique() if 'id' in df_filtered.columns else len(df_filtered)
        
        # Penanganan safety jika kolom populasi/pengungsi bernilai null atau tidak ada
        total_impacted_pop = df_filtered.groupby('Daerah_Terdampak')['Populasi_Daerah'].first().sum() if 'Populasi_Daerah' in df_filtered.columns else 0
        total_damaged_houses = df_filtered['Rumah Rusak Berat'].sum() if 'Rumah Rusak Berat' in df_filtered.columns else 0
        total_refugees = df_filtered['menderita_mengungsi'].sum() if 'menderita_mengungsi' in df_filtered.columns else 0
        total_meninggal = df_filtered['Meninggal'].sum() if 'Meninggal' in df_filtered.columns else 0
        
        # Tampilkan KPI Cards (Modifikasi gabungan kolom visualisasi metrik utama)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Kejadian Gempa", f"{total_events:,} Kejadian")
        col2.metric("Populasi Berisiko (Jiwa)", f"{int(total_impacted_pop):,}")
        col3.metric("Total Rumah Rusak Berat", f"{int(total_damaged_houses):,} Unit")
        col4.metric("Total Korban Jiwa", f"{int(total_meninggal):,} Jiwa")
        
        st.markdown("---")
        
        # VISUALISASI UTAMA INTERAKTIF (Plotly Express Integration)
        col_map, col_chart = st.columns([2, 1])
        
        with col_map:
            st.subheader("🗺️ Sebaran Geospasial Titik Gempa")
            if not df_filtered.empty:
                fig_map = px.scatter_mapbox(
                    df_filtered, 
                    lat="latitude", 
                    lon="longitude", 
                    color="mag" if "mag" in df_filtered.columns else None, 
                    size="mag" if "mag" in df_filtered.columns else None,
                    hover_name="Daerah_Terdampak" if "Daerah_Terdampak" in df_filtered.columns else None,
                    hover_data=["depth", "Rumah Rusak Berat"] if "depth" in df_filtered.columns else None,
                    color_continuous_scale=px.colors.sequential.YlOrRd,
                    size_max=15, 
                    zoom=4,
                    mapbox_style="carto-positron"
                )
                fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.warning("Tidak ada data spasial yang cocok dengan filter.")
            
        with col_chart:
            st.subheader("🏢 Kerusakan Infrastruktur per Wilayah")
            if not df_filtered.empty:
                # Menyiapkan kolom breakdown tingkat kerusakan jika ada di csv
                available_cols = ['Rumah Rusak Berat']
                if 'Rumah Rusak Sedang' in df_filtered.columns: available_cols.append('Rumah Rusak Sedang')
                if 'Rumah Rusak Ringan' in df_filtered.columns: available_cols.append('Rumah Rusak Ringan')
                
                df_bar = df_filtered.groupby('Daerah_Terdampak')[available_cols].sum().reset_index()
                df_bar = df_bar.sort_values(by='Rumah Rusak Berat', ascending=True).tail(10)
                
                fig_bar = px.bar(
                    df_bar, 
                    y="Daerah_Terdampak", 
                    x=available_cols,
                    title="Top 10 Daerah dengan Kerusakan Rumah Tertinggi",
                    orientation='h',
                    barmode="stack",
                    color_discrete_sequence=["#EF4444", "#F97316", "#FBBF24"]
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.warning("Tidak ada data grafik yang cocok dengan filter.")
        
        st.markdown("---")
        st.subheader("📋 Eksplorasi Data Transformed (Fact Table)")
        # Tampilkan kolom esensial yang sesuai dengan filter dinamis
        display_cols = [c for c in ['id', 'date', 'mag', 'depth', 'Daerah_Terdampak', 'Populasi_Daerah', 'Rumah Rusak Berat', 'Meninggal', 'menderita_mengungsi'] if c in df_filtered.columns]
        st.dataframe(df_filtered[display_cols], use_container_width=True)
    else:
        st.warning("⚠️ Data caching belum tersedia. Silakan jalankan `python src/model.py` untuk menarik data dari PostgreSQL dan melakukan *caching* ke direktori data/processed/.")

# ==========================================
# TAB 2: SIMULATOR RISIKO ML (RETAINED FROM CODE 2)
# ==========================================
with tab2:
    st.header("Simulator Risiko Kerusakan Infrastruktur")
    st.markdown("Masukkan parameter fisis gempa dan demografi untuk memprediksi jumlah **Rumah Rusak Berat**.")
    
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        
        with st.form("ml_simulator"):
            col1, col2 = st.columns(2)
            with col1:
                mag = st.slider("Kekuatan Gempa (Magnitudo)", min_value=1.0, max_value=10.0, value=5.5, step=0.1)
                depth = st.slider("Kedalaman Gempa (km)", min_value=1.0, max_value=700.0, value=15.0, step=1.0)
            with col2:
                daftar_wilayah = sorted(df['Daerah_Terdampak'].dropna().unique()) if not df.empty else []
                wilayah = st.selectbox("Pilih Titik Wilayah Pusat Gempa", daftar_wilayah)
                
            submit_button = st.form_submit_button(label="🔮 Prediksi Risiko")
            
        if submit_button and not df.empty:
            wilayah_data = df[df['Daerah_Terdampak'] == wilayah].iloc[0]
            lat = wilayah_data['latitude']
            lon = wilayah_data['longitude']
            pop = wilayah_data['Populasi_Daerah'] if 'Populasi_Daerah' in df.columns else 250000
            
            st.info(f"📍 **Sistem pintar mendeteksi:** Koordinat {lat:.4f}, {lon:.4f} dengan kepadatan {int(pop):,} jiwa di {wilayah.title()}.")

            input_data = pd.DataFrame({
                'mag': [mag], 
                'depth': [depth], 
                'latitude': [lat],
                'longitude': [lon],
                'Populasi_Daerah': [pop]
            })
            
            prediksi = model.predict(input_data)[0]
            pred_rumah = max(0, int(prediksi[0]))
            pred_meninggal = max(0, int(prediksi[1]))
            pred_luka = max(0, int(prediksi[2]))
            pred_faskes = max(0, int(prediksi[3]))
            
            st.markdown("---")
            st.subheader("🚨 Hasil Simulasi Dampak Bencana")
            
            col_res1, col_res2, col_res3, col_res4 = st.columns(4)
            col_res1.metric("🏠 Rumah Rusak", f"{pred_rumah:,} unit")
            col_res2.metric("💀 Meninggal", f"{pred_meninggal:,} jiwa")
            col_res3.metric("🤕 Luka/Sakit", f"{pred_luka:,} jiwa")
            col_res4.metric("🏥 Faskes Rusak", f"{pred_faskes:,} unit")
            
            st.markdown("---")
            st.subheader("📊 Kesimpulan Status Tanggap Darurat")
            if pred_rumah < 10 and pred_meninggal == 0 and pred_luka < 10:
                st.success("🟢 **AMAN (RESIKO RENDAH)** - Guncangan diperkirakan tidak menimbulkan kerusakan infrastruktur masif atau korban jiwa.")
            elif pred_rumah < 50 and pred_meninggal == 0:
                st.warning("🟡 **WASPADA (RESIKO SEDANG)** - Potensi kerusakan infrastruktur menengah. Diperlukan pengecekan lapangan.")
            else:
                st.error("🔴 **SIAGA DARURAT (RESIKO TINGGI)** - Peringatan potensi jatuhnya korban jiwa dan hancurnya fasilitas kesehatan/pendidikan. Siapkan tim SAR!")
    else:
        st.warning("⚠️ Model ML (`model_earthquake.pkl`) belum ditemukan. Silakan jalankan `python src/model.py` untuk melatih dan menyimpan model.")