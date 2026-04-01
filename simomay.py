import streamlit as st
import pandas as pd
import plotly.express as px

# Konfigurasi halaman
st.set_page_config(page_title="Dashboard Bisnis Siomay Faiz", layout="wide")

st.title("📊 Sistem Monitoring Bisnis Siomay")
st.write("Pantau performa harian dan perkembangan bisnismu di sini.")

# Masukkan link CSV dari 'Publish to Web' Google Sheets
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQpueaMsFLP82So1rul7EpBis9ucMiV_ibctS0j8VaABIbX9R0AjVPYVjuEy97wIPg0Hbqh8eIV4U8/pub?output=csv"

@st.cache_data
def load_data():
    df = pd.read_csv(SHEET_URL)
    # Pastikan kolom tanggal terbaca sebagai format tanggal
    if 'Tanggal' in df.columns:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])
    return df

try:
    data = load_data()

    # --- BAGIAN GRAFIK ---
    st.subheader("📈 Tren Penghasilan")
    if 'Tanggal' in data.columns and 'Penghasilan' in data.columns:
        fig = px.line(data, x='Tanggal', y='Penghasilan', title='Naik Turun Penghasilan',
                      markers=True, line_shape='linear')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Pastikan kolom 'Tanggal' dan 'Penghasilan' ada di spreadsheet.")

    # --- BAGIAN RINGKASAN DATA ---
    col1, col2, col3 = st.columns(3)
    with col1:
        total_omzet = data['Penghasilan'].sum() if 'Penghasilan' in data.columns else 0
        st.metric("Total Penghasilan", f"Rp {total_omzet:,.0f}")
    
    # --- BAGIAN TABEL TERINCI ---
    st.subheader("📋 Rincian Data Lengkap")
    st.dataframe(data, use_container_width=True)

    # --- FITUR DOWNLOAD ---
    st.subheader("📥 Download Laporan")
    csv = data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Data Sebagai CSV",
        data=csv,
        file_name='laporan_bisnis_siomay.csv',
        mime='text/csv',
    )

except Exception as e:
    st.error(f"Gagal memuat data. Pastikan link spreadsheet sudah benar dan di-publish ke web. Error: {e}")
