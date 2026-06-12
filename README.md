# kelompok-7-hebat

# Analisis Data Historis Gempa Indonesia untuk Identifikasi Pola dan Risiko Wilayah

## Kontributor

| Nama Lengkap | NIM | Peran |
| ------------ | --- | ----- |
| ACHMAD WILDAN M. | 244311032 | Data Engineer |
| KUNNI SOFA R. | 244311046 | Data Analyst |
| RINDY CANTIKA A.P.| 244311057 | Data Analyst |
| RIYAN ZAKARIA Z. | 244311058 | Project Manager |

---

# Deskripsi Proyek

Proyek ini menganalisis data historis gempa bumi di Indonesia menggunakan data dari USGS Earthquake Catalog, data batas administrasi provinsi/kabupaten, serta data kepadatan penduduk WorldPop/BPS. Data diolah melalui proses spatial join antara titik koordinat gempa dengan wilayah administrasi untuk menghitung frekuensi kejadian gempa per wilayah. Hasil analisis disajikan dalam bentuk visualisasi yang mudah dipahami, yaitu ranking wilayah dengan frekuensi gempa tertinggi dan peta risiko populasi terdampak. Selain itu, sistem menggunakan pemodelan Machine Learning untuk memprediksi kerusakan infrastruktur berdasarkan data historis.

---

# Manfaat Data / Use Case

- **Tujuan Proyek :** Proyek ini bertujuan untuk menentukan wilayah dengan frekuensi gempa tertinggi di Indonesia dengan membangun pipeline data yang mengotomatisasi proses pengumpulan, pengolahan spasial, dan visualisasi data gempa bumi, serta memprediksi risiko kerusakan infrastruktur bangunan secara *real-time*.
- **Manfaat :** Manfaat dari proyek ini antara lain memberikan informasi berbasis data mengenai wilayah rawan gempa untuk mendukung kebijakan mitigasi bencana, menjadi referensi bagi penelitian lanjutan di bidang kebencanaan dan tata ruang wilayah, meningkatkan kesadaran masyarakat terhadap risiko gempa di provinsi tempat tinggal mereka, serta memberikan pengalaman praktis dalam penerapan teknik data engineering dan analisis geospasial.

---

# Serving Analisis

Menyajikan metrik KPI utama (Total Kejadian, Rata-rata Magnitudo, Total Rumah Rusak Berat, dan Korban Jiwa). Menampilkan Peta Geospasial Interaktif dan grafik distribusi wilayah dengan antarmuka Premium bergaya *Glassmorphism* berbasis Streamlit pada Tab Business Intelligence Overview.

---

# Serving Machine Learning

Menyediakan simulator risiko cerdas menggunakan algoritma *Multi-Output Random Forest Regressor*. Pengguna cukup memilih wilayah (*Dropdown* pintar) untuk mengekstrak parameter demografi dan spasial secara otomatis, lalu memasukkan fisis gempa (Magnitudo, Kedalaman). Sistem memberikan estimasi 4 metrik dampak sekaligus (Rumah Hancur, Korban Jiwa, Luka, Faskes) secara instan beserta status peringatan dini risiko (Aman, Waspada, Siaga Darurat).

---

# Pipeline

## Extract (Pengambilan Data)

- **Sumber Data**
  * Batas Kabupaten Kota Desember 2019 Dukcapil - https://www.indonesia-geospasial.com/2020/04/download-shapefile-shp-batas.html
  * Data Titik Gempa (USGS) - https://earthquake.usgs.gov/earthquakes/search/
  * Data Dampak Bencana Gempa (BNPB) - https://data.bnpb.go.id/dataset/data-bencana-indonesia
  * Data Populasi Administrasi Indonesia - https://data.humdata.org/dataset/cod-ps-idn
- **Metode Pengambilan :**
  * Metode 1: Mengunduh dan membaca data mentah berformat `.csv` (untuk rekaman data gempa USGS dan basis data dampak bencana historis BNPB).
  * Metode 2: Mengunduh dan membaca data spasial berformat `.shp` (Shapefile) untuk batas wilayah administrasi kabupaten/kota menggunakan library GeoPandas.
  * Metode 3: Mengunduh dan membaca data demografi kependudukan berformat `.xlsx` (Excel) dari HumData / BPS.

---

# Transform (Pembersihan & Transformasi)

- **Pembersihan :**
  * Membersihkan data dari nilai yang kosong (*missing values*) serta menyelaraskan format penamaan wilayah agar konsisten di semua dataset untuk kebutuhan proses *join*.
    + Langkah 1: Menghapus baris yang tidak memiliki nilai esensial seperti `mag`, `latitude`, `longitude`, dan `time` pada data gempa.
    + Langkah 2: Mengubah zona waktu dari format UTC menjadi WIB untuk konsistensi temporal di seluruh dataset.
    + Langkah 3: Menstandarisasi penamaan wilayah (menghapus kata 'KABUPATEN ', 'KOTA ', 'KAB. ') agar memudahkan pemetaan dengan data Dukcapil dan BPS.
    + Langkah 4: Menghapus data anomali atau data residu dengan nama wilayah bernilai 'NONE', 'NAN', atau kosong.
- **Transformasi :**
  * Transformasi 1: Membangun Radius Guncangan Spasial (Buffer 75 km) menggunakan GeoPandas dari setiap titik koordinat episentrum gempa.
  * Transformasi 2: Melakukan *Spatial Join* (`sjoin`) untuk mengetahui irisan (interseksi) antara radius guncangan spasial gempa dengan poligon peta batas administrasi Dukcapil.
  * Transformasi 3: Melakukan agregasi dan kompilasi metrik kerusakan dari data BNPB serta menyuntikkan data populasi BPS ke dalam matriks data terdampak akhir (*fact_ultimate_impact*).

---

# Load (Pemindahan ke Target)

- **Target :**
  * **Skema Database:**
    + Sistem berbasis Cloud Database PostgreSQL (di-hosting via Aiven Cloud Infrastructure).
    + Tabel penyimpanan utama: `fact_ultimate_impact`
- **Proses Load :**
  * Mengonfigurasi dan membangun koneksi aman (*connection string*) menggunakan SQLAlchemy.
  * Memindahkan DataFrame komposit gabungan ke dalam tabel PostgreSQL menggunakan metode `to_sql(if_exists='replace')`.
  * Sebagai *caching layer*, data akhir juga disimpan secara lokal dalam file CSV (`data/processed/gempa_clean.csv`) agar Streamlit dapat merender dasbor seketika tanpa perlu menembak kueri berulang kali ke *cloud database*.

---

# Arsitektur / Workflow ETL

- **Alur Modular :** Proyek mengadopsi struktur *Arsitektur Menengah (Standard Clean Layout)* yang memisahkan antara `data/` (mentah dan yang diproses), lapisan inti logika pemrosesan ETL dan ML di `src/`, dan lapisan representasi visual (frontend) pada `app.py`.
- **Teknologi yang Digunakan :**
  * ETL: Python, Pandas, GeoPandas, Shapely.
  * Machine Learning: Scikit-Learn, Joblib.
  * Database: PostgreSQL (via Aiven Cloud), SQLAlchemy, Python-Dotenv.
  * Visualisasi: Streamlit, Matplotlib, Seaborn.

---

# Kode Program

- **Struktur Kode :**
  * `.env` & `requirements.txt`: Manajemen lingkungan, kredensial basis data, dan library.
  * `src/database.py`: Modul penghubung koneksi SQLAlchemy.
  * `src/model.py`: Engine utama, memuat fungsi komplit *Extract, Transform, Load*, serta pemodelan.
  * `app.py`: Antarmuka berbasis Streamlit dengan struktur *Multi-Tab*.
- **Machine Learning :**
  * Algoritma *Multi-Output Random Forest Regressor* digunakan menggantikan Regresi Linear murni untuk memprediksi **4 variabel sekaligus** (Rumah Hancur, Korban Meninggal, Luka/Sakit, dan Faskes Rusak). Parameter prediktor diperluas dengan *Geospatial Intelligence* (`mag`, `depth`, `latitude`, `longitude`, dan `Populasi_Daerah`). Model juga menerapkan teknik **Sample Weights** (pembobotan) untuk mengatasi anomali *Zero-Inflated Data* agar kejadian gempa merusak tidak diabaikan algoritma.

---

# Link Proyek :

- ETL Pipeline : Berada terpusat di fungsi `run_etl_pipeline()` dalam `src/model.py`
- Machine Learning : Berada terpusat di fungsi `train_model()` dalam `src/model.py`
- Streamlit : Berada di `app.py`
