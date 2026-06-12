import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import joblib
import warnings
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error

# Custom imports
from database import get_engine, fetch_data

warnings.filterwarnings('ignore')

# Setup direktori
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
DATA_PROC_DIR = os.path.join(BASE_DIR, 'data', 'processed')
os.makedirs(DATA_RAW_DIR, exist_ok=True)
os.makedirs(DATA_PROC_DIR, exist_ok=True)

# ==========================================
# 1. ETL PIPELINE (Extract, Transform, Load)
# ==========================================
def extract_data():
    """Fungsi ini dipertahankan sebagai dokumentasi pipeline Extract data mentah."""
    print("=== 1. Memulai Extract Data ===")
    FILE_GEMPA = os.path.join(DATA_RAW_DIR, 'gempa_usgs_raw.csv')
    FILE_BNPB = os.path.join(DATA_RAW_DIR, 'demografi_bnpb_raw.csv')
    FILE_POP = os.path.join(DATA_RAW_DIR, 'populasi_raw.xlsx') 
    FILE_SHAPEFILE = os.path.join(DATA_RAW_DIR, 'batas_wilayah_raw.shp')

    try:
        df_gempa = pd.read_csv(FILE_GEMPA)
        df_bnpb = pd.read_csv(FILE_BNPB)
        df_pop = pd.read_excel(FILE_POP, sheet_name=0)
        print("Memuat Shapefile Peta Kabupaten/Kota...")
        gdf_batas = gpd.read_file(FILE_SHAPEFILE)

        print(f"Berhasil: Gempa ({len(df_gempa)}), BNPB ({len(df_bnpb)}), Populasi ({len(df_pop)}), Peta ({len(gdf_batas)})")
        return df_gempa, df_bnpb, df_pop, gdf_batas
    except Exception as e:
        print(f"ERROR EKSTRAKSI: {e}\nPastikan dataset mentah sudah ada di folder data/raw/")
        return None, None, None, None

def transform_data(df_gempa, df_bnpb, df_pop, gdf_batas):
    """Fungsi ini dipertahankan sebagai dokumentasi pipeline Transform data spasial."""
    print("=== 2. Memulai Transform Data ===")
    
    if 'time' in df_gempa.columns:
        df_gempa = df_gempa.dropna(subset=['mag', 'latitude', 'longitude', 'time'])
        df_gempa['date'] = (pd.to_datetime(df_gempa['time']) + pd.Timedelta(hours=7)).dt.date
    
    if 'Tanggal / Waktu Kejadian' in df_bnpb.columns:
        df_bnpb['date'] = pd.to_datetime(df_bnpb['Tanggal / Waktu Kejadian']).dt.date
    
    df_gempa_risk = df_gempa[df_gempa['mag'] >= 4.0].copy()

    def clean_wilayah(text):
        t = str(text).upper().strip()
        t = t.replace('KABUPATEN ', '').replace('KOTA ', '').replace('KAB. ', '')
        return t.strip()

    col_kab_pop = 'ADM2_EN' if 'ADM2_EN' in df_pop.columns else df_pop.columns[0]
    col_tot_pop = 'BTOTL_2020' if 'BTOTL_2020' in df_pop.columns else df_pop.columns[1]
    
    df_pop['Kab_Match'] = df_pop[col_kab_pop].apply(clean_wilayah)
    dict_populasi = dict(zip(df_pop['Kab_Match'], df_pop[col_tot_pop]))

    print("Membangun Radius Guncangan (Buffer 75 km)...")
    geometry = [Point(xy) for xy in zip(df_gempa_risk['longitude'], df_gempa_risk['latitude'])]
    gdf_gempa = gpd.GeoDataFrame(df_gempa_risk, geometry=geometry, crs="EPSG:4326")
    gdf_gempa = gdf_gempa.to_crs(epsg=3857)
    gdf_gempa['geometry'] = gdf_gempa.geometry.buffer(75000)
    gdf_gempa = gdf_gempa.to_crs(epsg=4326)

    print("Melakukan Spatial Join...")
    gdf_batas = gdf_batas.to_crs(epsg=4326)
    gdf_terdampak = gpd.sjoin(gdf_gempa, gdf_batas, how="inner", predicate="intersects")

    possible_cols = ['KAB_KOTA', 'WADMKK', 'KABUPATEN', 'NAMA_KAB', 'KABKOT', 'KAB']
    kolom_shp = next((col for col in possible_cols if col in gdf_terdampak.columns), None)
    if kolom_shp is None:
        raise ValueError("Nama kolom Kabupaten tidak ditemukan di Shapefile.")

    gdf_terdampak['Kab_Match'] = gdf_terdampak[kolom_shp].apply(clean_wilayah)
    gdf_terdampak = gdf_terdampak[(~gdf_terdampak['Kab_Match'].isin(['NONE', 'NAN', ''])) & (gdf_terdampak['Kab_Match'].notna())]
    gdf_terdampak['Populasi_Daerah'] = gdf_terdampak['Kab_Match'].map(dict_populasi).fillna(0)

    cols_kerusakan = [
        'Meninggal', 'Hilang', 'Luka / Sakit', 'menderita_mengungsi',
        'Rumah Rusak Berat', 'Rumah Rusak Sedang', 'Rumah Rusak Ringan', 'Rumah Terendam',
        'Satuan Pendidikan Rusak', 'Rumah Ibadat Rusak', 'Fasilitas Pelayanan Kesehatan Rusak',
        'Kantor Rusak', 'Jembatan Rusak'
    ]
    cols_kerusakan = [c for c in cols_kerusakan if c in df_bnpb.columns]
    
    col_kab_bnpb = 'Kabupaten' if 'Kabupaten' in df_bnpb.columns else df_bnpb.columns[0]
    df_bnpb['Kab_Match'] = df_bnpb[col_kab_bnpb].apply(clean_wilayah)
    df_bnpb_agg = df_bnpb.groupby(['date', 'Kab_Match'])[cols_kerusakan].sum().reset_index()

    print("Menggabungkan seluruh dimensi...")
    df_final = pd.merge(gdf_terdampak, df_bnpb_agg, on=['date', 'Kab_Match'], how='left')
    df_final[cols_kerusakan] = df_final[cols_kerusakan].fillna(0)

    cols_groupby = ['id', 'date', 'mag', 'depth', 'latitude', 'longitude', 'Kab_Match', 'Populasi_Daerah']
    cols_groupby = [c for c in cols_groupby if c in df_final.columns]
    
    df_ultimate = df_final.groupby(cols_groupby)[cols_kerusakan].sum().reset_index()
    df_ultimate = df_ultimate.rename(columns={'Kab_Match': 'Daerah_Terdampak'})
    df_ultimate = df_ultimate[df_ultimate['Daerah_Terdampak'] != 'NONE']

    print("Transformasi Selesai!")
    return df_ultimate

def load_data_to_db(df):
    """Fungsi ini memuat DataFrame yang sudah ditransformasi ke Database Aiven."""
    print("=== 3. Memulai Load Data ke PostgreSQL (Aiven) ===")
    engine = get_engine()
    df.to_sql('fact_ultimate_impact', engine, if_exists='replace', index=False)
    print("✅ PIPELINE ETL BERHASIL! Data tersimpan di Cloud Database PostgreSQL.")

def run_etl_pipeline():
    """Fungsi ini menjalankan keseluruhan alur Extract, Transform, dan Load."""
    df_gempa, df_bnpb, df_pop, gdf_batas = extract_data()
    if all(v is not None for v in [df_gempa, df_bnpb, df_pop, gdf_batas]):
        df_transformed = transform_data(df_gempa, df_bnpb, df_pop, gdf_batas)
        load_data_to_db(df_transformed)
        return True
    return False

def fast_load_clean_csv_to_db():
    """Fungsi alternatif untuk langsung memuat data bersih (fact_ultimate_impact (2).csv) ke Database Aiven."""
    print("=== Memuat Data Bersih Lokal ke PostgreSQL (Aiven) ===")
    file_path = os.path.join(BASE_DIR, 'fact_ultimate_impact (2).csv')
    
    if not os.path.exists(file_path):
        print(f"File {file_path} tidak ditemukan!")
        return False
        
    print(f"Membaca file lokal: {file_path}")
    df = pd.read_csv(file_path)
    engine = get_engine()
    
    print("Mengunggah data ke tabel 'fact_ultimate_impact'...")
    df.to_sql('fact_ultimate_impact', engine, if_exists='replace', index=False)
    print(f"✅ Berhasil memuat {len(df)} baris data ke Cloud Database PostgreSQL.")
    return True

# ==========================================
# 2. MACHINE LEARNING PIPELINE
# ==========================================
def clean_ml_data(df):
    """Pembersihan data lanjutan untuk pemodelan ML (handling missing features)"""
    target_cols = ['Rumah Rusak Berat', 'Meninggal', 'Luka / Sakit', 'Fasilitas Pelayanan Kesehatan Rusak']
    # Memastikan tidak ada nilai kosong di fitur input maupun target
    kolom_wajib = ['mag', 'depth', 'latitude', 'longitude', 'Populasi_Daerah'] + target_cols
    # Jika ada target_cols yang belum ada (misal dari CSV lama), tangani agar tidak error:
    for col in target_cols:
        if col not in df.columns:
            df[col] = 0
            
    df = df.dropna(subset=kolom_wajib)
    return df

def train_model():
    print("\n=== Pipeline Machine Learning ===")
    try:
        df = fetch_data()
    except Exception as e:
        print(f"Gagal mengambil data dari database: {e}")
        return

    print(f"Jumlah data awal ditarik dari DB: {len(df)}")
    
    df_clean = clean_ml_data(df)
    print(f"Jumlah data valid setelah disaring: {len(df_clean)}")
    
    # Caching data ke folder processed untuk Streamlit BI Dashboard
    clean_csv_path = os.path.join(DATA_PROC_DIR, 'gempa_clean.csv')
    df_clean.to_csv(clean_csv_path, index=False)
    print(f"Data caching berhasil disimpan ke {clean_csv_path}")

    # Variabel Independen (X) SEKARANG TERMASUK KOORDINAT GEOSPASIAL
    X = df_clean[['mag', 'depth', 'latitude', 'longitude', 'Populasi_Daerah']]
    
    # [MULTI-OUTPUT REGRESSION] Target Y kini terdiri dari 4 variabel bencana!
    y = df_clean[['Rumah Rusak Berat', 'Meninggal', 'Luka / Sakit', 'Fasilitas Pelayanan Kesehatan Rusak']]

    # Splitting Data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Data Training: {len(X_train)} baris | Data Testing: {len(X_test)} baris")

    # [SOLUSI ZERO-INFLATED]: Memberikan bobot (weight) besar pada kejadian gempa yang mematikan/merusak
    import numpy as np
    bobot_latih = np.where((y_train['Rumah Rusak Berat'] > 0) | (y_train['Meninggal'] > 0), 200, 1)

    # Modeling - MultiOutput RandomForest
    print("Melatih model Multi-Output Random Forest Regressor...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train, sample_weight=bobot_latih)

    # Evaluasi (Hanya contoh metrik rata-rata)
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    print("Model Multi-Output berhasil dilatih.")
    print(f"Akurasi R-Squared (R2 Score): {r2:.4f}")
    print(f"Mean Squared Error (MSE): {mse:.4f}")

    # Serialize object
    model_path = os.path.join(os.path.dirname(__file__), 'model_earthquake.pkl')
    joblib.dump(model, model_path)
    print(f"Model ML berhasil disimpan ke {model_path}")

if __name__ == "__main__":
    print("Menjalankan pipeline...")
    # Karena data fact_ultimate_impact sudah berada di Aiven, 
    # kita langsung lompat ke proses penarikan data dan pemodelan ML.
    # Fungsi Extract, Transform, Load di atas tetap dipertahankan utuh untuk dokumentasi arsitektur.
    
    train_model()
