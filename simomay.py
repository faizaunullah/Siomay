import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Siomay Faiz", layout="wide")

st.title("📊 Dashboard Bisnis Siomay Faiz")

# Masukkan link CSV hasil publish to web kamu di sini (Gunakan tanda petik!)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQpueaMsFLP82So1rul7EpBis9ucMiV_ibctS0j8VaABIbX9R0AjVPYVjuEy97wIPg0Hbqh8eIV4U8/pub?output=csv"

@st.cache_data
def load_data():
    # skipfooter=0 disesuaikan jika ada baris kosong di bawah spreadsheet
    df = pd.read_csv(SHEET_URL)
    
    # hapus kolom yang namanya mengandung 'Unnamed' agar tabel bersih
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Pastikan kolom TANGGAL terbaca sebagai tanggal
    if 'TANGGAL' in df.columns:
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce')
        df = df.dropna(subset=['TANGGAL']) # Hapus baris jika tanggalnya kosong
    return df

try:
    data = load_data()

    # --- FITUR FILTER (PER BULAN/HARI) ---
    st.sidebar.header("Filter Data")
    min_date = data['TANGGAL'].min()
    max_date = data['TANGGAL'].max()
    
    start_date, end_date = st.sidebar.date_input(
        "Pilih Rentang Waktu",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # Filter data berdasarkan pilihan user
    mask = (data['TANGGAL'] >= pd.Timestamp(start_date)) & (data['TANGGAL'] <= pd.Timestamp(end_date))
    filtered_data = data.loc[mask]

    # --- RINGKASAN METRIK ---
    total_omset = filtered_data['OMSET'].sum() if 'OMSET' in filtered_data.columns else 0
    total_laba = filtered_data['LABA BERSIH'].sum() if 'LABA BERSIH' in filtered_data.columns else 0
    
    col1, col2 = st.columns(2)
    col1.metric("Total Omset (Periode Terpilih)", f"Rp {total_omset:,.0f}")
    col2.metric("Total Laba Bersih", f"Rp {total_laba:,.0f}")

    # --- GRAFIK ---
    st.subheader("📈 Tren Penghasilan")
    if not filtered_data.empty:
        # Kita pakai OMSET untuk grafiknya
        fig = px.line(filtered_data, x='TANGGAL', y='OMSET', 
                      title='Grafik Naik Turun Omset', markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Tidak ada data pada rentang tanggal tersebut.")

    # --- TABEL ---
    st.subheader("📋 Data Terperinci")
    st.dataframe(filtered_data, use_container_width=True)

    # --- DOWNLOAD ---
    csv = filtered_data.to_csv(index=False).encode('utf-8')
    st.download_button("Download Laporan (CSV)", data=csv, file_name='laporan_siomay.csv')

except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
