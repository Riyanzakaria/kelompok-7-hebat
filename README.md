# kelompok-7-hebat

## Project Information
**Project Name:** Analisis Data Historis Gempa Indonesia untuk Identifikasi Pola dan Risiko Wilayah

---

### 1. Executive Summary

#### 1.1. Project Overview
* **Tujuan Project:** Menentukan provinsi dengan frekuensi gempa tertinggi, mentransformasikan menjadi informasi yang mudah dipahami, yaitu merangking provinsi mana yang paling sering diguncang gempa.
* **Scope Project:** * Melakukan analisis kualitas dan karakteristik data.
    * Perhitungan jumlah gempa per provinsi.
    * Ranking provinsi di Indonesia berdasarkan total kejadian.
    * *Spatial join* titik gempa dengan batas provinsi di Indonesia.
    * *Sampling* populasi menggunakan data raster WorldPop.
* **Expected Outcomes:** * Bar chart jumlah gempa per provinsi.
    * Peta risiko populasi terdampak (*Risk Map*) berdasarkan sebaran gempa dan kepadatan penduduk.
* **Timeline:** 3 bulan (Februari - Mei 2026).

#### 1.2. Stakeholders
* **Project Owner:** Kelompok 7
* **Team Members:**
    * **Data Engineer:** Rindy Cantika A P
    * **Data Analyst:** Kunni Sofa Rahmayani
    * **Project Manager:** Riyan Zakaria Z & Achmad Wildan M
* **End Users:** Masyarakat umum yang membutuhkan informasi risiko gempa di wilayahnya.

---

### 2. Data Source Analysis

#### 2.1. Data Titik Gempa Bumi (USGS)
**Source Details:**
* **Dataset Name:** Gempa Bumi Indonesia (USGS Earthquake Catalog)
* **URL/Access Point:** [USGS Earthquake Search](https://earthquake.usgs.gov/earthquakes/search/)
* **Data Owner:** United States Geological Survey (USGS)
* **Update Frequency:** Real-Time

**Data Analysis:**
* **Format Data:** CSV
* **Jumlah Data:** 5.568 baris
* **Jumlah Kolom:** 22 kolom
* **Time Coverage:** Januari 2023 - Februari 2026
* **Data Quality:**
    * **Completeness:** 98% (terdapat nilai kosong pada kolom *gap* dan *dmin* masing-masing 1 entri).
    * **Accuracy:** Tinggi (data bersumber langsung dari sensor seismograf USGS).
    * **Consistency:** Sangat Baik.
    * **Timeliness:** Sangat baik untuk monitoring secara real-time.

#### 2.2. Data Indonesia-Geospasial
**Source Details:**
* **Dataset Name:** Batas Administrasi Provinsi Indonesia Desember 2019
* **URL/Access Point:** [Indonesia Geospasial](https://www.indonesia-geospasial.com/2020/04/download-shapefile-shp-batas.html)
* **Creator/Publisher:** Direktorat Jenderal Kependudukan dan Pencatatan Sipil (Dukcapil)
* **Last Update:** Desember 2019

**Data Analysis:**
* **Format Data:** Shapefile (.shp)
* **Size & Dimensions:** 84.054 KB (≈84 MB)
* **Data Fields:** `GEOMETRY` (Polygon)
* **Quality Metrics:**
    * **Missing Values:** Tidak ada (Mencakup seluruh provinsi).
    * **Data Types:** Geometry (Polygon).
    * **Consistency:** Struktur polygon konsisten, format standar GIS, kompatibel untuk *spatial join*.
    * **Documentation Quality:** Baik.

#### 2.3. Data WorldPop.org
**Source Details:**
* **Dataset Name:** Indonesia Population Density 1km Resolution
* **URL/Access Point:** [WorldPop Geodata](https://hub.worldpop.org/geodata/summary?id=73824)
* **Data Owner:** Worldpop, University of Southampton
* **Last Update:** 2025

**Data Analysis:**
* **Format Data:** GeoTIFF (.tif)
* **Size & Dimensions:** 5.548 KB (≈5,4 MB)
* **Data Fields:** Pixel value (estimasi jumlah penduduk per piksel 1×1 km).
* **Metadata:** CRS (Coordinate Reference System), Resolusi spasial, Extent geografis, NoData value.
* **Quality Metrics:**
    * **Missing Values:** Tidak ada.
    * **Data Types:** Numeric raster grid (nilai kontinu kepadatan penduduk).
    * **Consistency:** Grid resolusi konsisten (1 km × 1 km).
    * **Documentation Quality:** Baik.

---

### 3. Data Flow Mapping

#### Data Integration Architecture
1.  **Ingestion:** Penarikan data mentah dari USGS (CSV), Indonesia-Geospasial (SHP), dan WorldPop (TIF).
2.  **Processing:** Pembersihan data (handling null values) dan transformasi koordinat.
3.  **Spatial Analysis:** Melakukan *spatial join* antara titik gempa dengan poligon provinsi dan ekstraksi nilai populasi.
4.  **Output:** Pembuatan Bar Chart untuk ranking frekuensi dan Peta Risiko (Risk Map) menggunakan perangkat lunak GIS atau library Python.
