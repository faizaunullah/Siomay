import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Dashboard Siomay Faiz", layout="wide")

st.title("📊 Dashboard Bisnis Siomay Faiz")

# GANTI DENGAN LINK CSV HASIL PUBLISH TO WEB KAMU
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQpueaMsFLP82So1rul7EpBis9ucMiV_ibctS0j8VaABIbX9R0AjVPYVjuEy97wIPg0Hbqh8eIV4U8/pub?output=csv"

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        
        # 1. Cari baris yang mengandung header 'TANGGAL'
        if 'TANGGAL' not in df.columns:
            for i in range(len(df)):
                if "TANGGAL" in df.iloc[i].values:
                    df.columns = df.iloc[i]
                    df = df.iloc[i+1:].reset_index(drop=True)
                    break
        
        # 2. Bersihkan nama kolom dari spasi atau karakter aneh
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # 3. Hapus kolom 'UNNAMED' atau kolom kosong
        df = df.loc[:, ~df.columns.str.contains('UNNAMED')]
        
        # 4. Konversi TANGGAL (Paling Krusial)
        if 'TANGGAL' in df.columns:
            # Ubah jadi datetime, yang gagal jadi NaT (Not a Time)
            df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce')
            # Hapus baris yang tanggalnya kosong/error
            df = df.dropna(subset=['TANGGAL'])
        
        # 5. Konversi Angka (Omset, Laba, dll)
        for col in ['OMSET', 'LABA BERSIH', 'TOTAL PENGELUARAN']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[Rp,.\s]', '', regex=True), errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Gagal memproses data: {e}")
        return pd.DataFrame()

data = load_data()

if not data.empty and 'TANGGAL' in data.columns:
    # Urutkan berdasarkan tanggal terbaru
    data = data.sort_values('TANGGAL')

    # --- SIDEBAR FILTER ---
    st.sidebar.header("📅 Filter Waktu")
    
    # Ambil tanggal minimal dan maksimal yang VALID
    min_date = data['TANGGAL'].min().date()
    max_date = data['TANGGAL'].max().date()

    # Kontrol input tanggal agar tidak error jika data kosong
    try:
        date_range = st.sidebar.date_input(
            "Pilih Rentang Tanggal",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            mask = (data['TANGGAL'].dt.date >= start_date) & (data['TANGGAL'].dt.date <= end_date)
            filtered_df = data.loc[mask]
        else:
            filtered_df = data
            
    except:
        filtered_df = data

    # --- TAMPILAN UTAMA ---
    if not filtered_df.empty:
        # Metrik
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("💰 Total Omset", f"Rp {filtered_df['OMSET'].sum():,.0f}")
        with c2: st.metric("💸 Pengeluaran", f"Rp {filtered_df['TOTAL PENGELUARAN'].sum():,.0f}")
        with c3: st.metric("📈 Laba Bersih", f"Rp {filtered_df['LABA BERSIH'].sum():,.0f}")

        # Grafik
        st.subheader("📈 Tren Penghasilan")
        fig = px.line(filtered_df, x='TANGGAL', y='OMSET', markers=True, title="Grafik Omset Harian")
        st.plotly_chart(fig, use_container_width=True)

        # Tabel
        st.subheader("📋 Rincian Data")
        st.dataframe(filtered_df, use_container_width=True)

        # Download
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📩 Download Data Ini", data=csv, file_name="laporan_siomay.csv")
    else:
        st.warning("Data tidak tersedia untuk rentang waktu ini.")
else:
    st.info("Menunggu data dari Google Sheets... Pastikan kolom 'TANGGAL' sudah ada isinya.")
