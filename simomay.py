import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Siomay Faiz", layout="wide")

st.title("📊 Dashboard Bisnis Siomay Faiz")

# GANTI DENGAN LINK CSV KAMU
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQpueaMsFLP82So1rul7EpBis9ucMiV_ibctS0j8VaABIbX9R0AjVPYVjuEy97wIPg0Hbqh8eIV4U8/pub?output=csv"

@st.cache_data
def load_data():
    # Membaca data
    df = pd.read_csv(SHEET_URL)
    
    # --- PEMBERSIHAN OTOMATIS ---
    # Jika baris pertama isinya bukan kolom yang benar, kita geser sampai ketemu 'TANGGAL'
    if 'TANGGAL' not in df.columns:
        for i in range(len(df)):
            if "TANGGAL" in df.iloc[i].values:
                df.columns = df.iloc[i] # Jadikan baris ini sebagai Header
                df = df.iloc[i+1:].reset_index(drop=True)
                break
    
    # Hapus kolom kosong (Unnamed)
    df = df.loc[:, df.columns.notna()]
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Pastikan Nama Kolom Bersih dari spasi
    df.columns = df.columns.str.strip()

    # Konversi Tanggal
    if 'TANGGAL' in df.columns:
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce')
        df = df.dropna(subset=['TANGGAL'])
    
    # Konversi Angka (Omset & Laba) agar bisa dijumlahkan
    for col in ['OMSET', 'LABA BERSIH', 'TOTAL PENGELUARAN']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('Rp', ''), errors='coerce').fillna(0)
            
    return df

try:
    data = load_data()

    if 'TANGGAL' in data.columns:
        # --- SIDEBAR FILTER ---
        st.sidebar.header("📅 Filter Waktu")
        min_d = data['TANGGAL'].min().date()
        max_d = data['TANGGAL'].max().date()
        
        start_date, end_date = st.sidebar.date_input(
            "Pilih Rentang Tanggal",
            value=[min_d, max_d],
            min_value=min_d,
            max_value=max_d
        )

        # Filter Data
        mask = (data['TANGGAL'].dt.date >= start_date) & (data['TANGGAL'].dt.date <= end_date)
        filtered_df = data.loc[mask].sort_values('TANGGAL')

        # --- METRIK UTAMA ---
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Total Omset", f"Rp {filtered_df['OMSET'].sum():,.0f}")
        c2.metric("💸 Pengeluaran", f"Rp {filtered_df['TOTAL PENGELUARAN'].sum():,.0f}")
        c3.metric("📈 Laba Bersih", f"Rp {filtered_df['LABA BERSIH'].sum():,.0f}")

        # --- GRAFIK ---
        st.subheader("📈 Tren Omset Harian")
        fig = px.area(filtered_df, x='TANGGAL', y='OMSET', text='OMSET',
                      title="Grafik Pendapatan Siomay")
        st.plotly_chart(fig, use_container_width=True)

        # --- TABEL & DOWNLOAD ---
        st.subheader("📋 Rincian Tabel")
        st.dataframe(filtered_df, use_container_width=True)
        
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📩 Download Data Terpilih", data=csv, file_name="laporan_faiz.csv")
    else:
        st.error("Kolom 'TANGGAL' tidak ditemukan. Pastikan di spreadsheet ada tulisan TANGGAL (huruf besar semua).")

except Exception as e:
    st.error(f"Terjadi masalah teknis: {e}")
