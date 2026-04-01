import streamlit as st
import pandas as pd
import numpy as np

# Konfigurasi halaman
st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide")

st.title("🥟 Dashboard Lengkap Siomay Jawara Malang")
st.markdown("*(Data otomatis ditarik dari Google Sheets. Gunakan menu di kiri untuk memfilter)*")

# ID Spreadsheet kamu
SHEET_ID = "1L1C72W0C8heL5YLahlAliT3K_9gYkcfy9mCAk4rSFXY"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=15)
def load_data():
    return pd.read_excel(EXCEL_URL, sheet_name=None, engine='openpyxl')

try:
    semua_sheet = load_data()
    
    # --- MENU FILTER DI SAMPING ---
    st.sidebar.header("🎛️ Filter Data Laporan")
    daftar_bulan = list(semua_sheet.keys())
    bulan_terpilih = st.sidebar.selectbox("Pilih Bulan:", daftar_bulan)
    
    df_raw = semua_sheet[bulan_terpilih]
    
    # --- 1. RINGKASAN KEUANGAN ---
    total_omset_sebulan = pd.to_numeric(df_raw.iloc[1, 1], errors='coerce')
    total_produksi = pd.to_numeric(df_raw.iloc[1, 2], errors='coerce') 
    total_operasional = pd.to_numeric(df_raw.iloc[1, 3], errors='coerce')
    
    st.subheader(f"💰 Ringkasan Keuangan ({bulan_terpilih})")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Omset 1 Bulan", f"Rp {total_omset_sebulan:,.0f}".replace(',', '.'))
    col2.metric("Total Biaya Produksi", f"Rp {total_produksi:,.0f}".replace(',', '.'))
    col3.metric("Total Pengeluaran Keseluruhan", f"Rp {total_operasional:,.0f}".replace(',', '.'))
    
    st.markdown("---")
    
    # --- 2. DATA PEMASUKAN (UNTUK FILTER TANGGAL) ---
    df_harian = df_raw.head(35).copy()
    rentang_tgl = (1, 31) # Default
    
    if ' TANGGAL' in df_harian.columns:
        df_harian = df_harian.dropna(subset=[' TANGGAL'])
        df_harian = df_harian[df_harian[' TANGGAL'].astype(str).str.isnumeric() == True]
        df_harian['Tgl_Angka'] = df_harian[' TANGGAL'].astype(int)
        
        min_tgl = int(df_harian['Tgl_Angka'].min())
        max_tgl = int(df_harian['Tgl_Angka'].max())
        rentang_tgl = st.sidebar.slider("Pilih Rentang Tanggal:", min_tgl, max_tgl, (min_tgl, max_tgl))
        
        df_filter = df_harian[(df_harian['Tgl_Angka'] >= rentang_tgl[0]) & (df_harian['Tgl_Angka'] <= rentang_tgl[1])].copy()
        
        st.subheader(f"📈 Laporan Pemasukan (Tgl {rentang_tgl[0]} - {rentang_tgl[1]})")
        if 'OMSET' in df_filter.columns:
            df_filter['OMSET'] = pd.to_numeric(df_filter['OMSET'], errors='coerce').fillna(0)
            df_omset = df_filter[df_filter['OMSET'] > 0].copy()
            if not df_omset.empty:
                df_omset['Tanggal_Tampil'] = "Tgl " + df_omset['Tgl_Angka'].astype(str)
                st.line_chart(data=df_omset.set_index('Tanggal_Tampil')['OMSET'])
                st.dataframe(df_omset[['Tanggal_Tampil', 'OMSET']].rename(columns={'Tanggal_Tampil': 'Tanggal'}), use_container_width=True)

    # --- 3. TABEL RINCIAN PENGELUARAN LAIN ---
    st.markdown("---")
    st.subheader(f"💸 Rincian Pengeluaran Barang (LPG, Kresek, dll)")
    
    # MENCARI KATA KUNCI "PENGELUARAN LAIN"
    target_row, target_col = -1, -1
    for r in range(20):
        for c in range(len(df_raw.columns)):
            val = str(df_raw.iloc[r, c]).strip().upper()
            if "PENGELUARAN LAIN" in val:
                target_row, target_col = r, c
                break
        if target_row != -1: break

    # Jika ketemu judul "PENGELUARAN LAIN", cari kolom "KETERANGAN" di bawahnya
    if target_row != -1:
        found_ket_col = -1
        # Cari di sekitar kolom judul tersebut (3 kolom ke kanan)
        for c_search in range(target_col, min(target_col + 3, len(df_raw.columns))):
            for r_search in range(target_row, target_row + 5):
                teks = str(df_raw.iloc[r_search, c_search]).strip().upper()
                if "KETERANGAN" in teks:
                    found_ket_col = c_search
                    row_header_peng = r_search
                    break
            if found_ket_col != -1: break
        
        if found_ket_col != -1:
            # Ambil data: Kolom Tgl (kiri), Ket (tengah), Nominal (kanan)
            df_peng = df_raw.iloc[row_header_peng+1:150, [found_ket_col-1, found_ket_col, found_ket_col+1]].copy()
            df_peng.columns = ['Tgl', 'Item', 'Biaya']
            
            # Bersihkan data
            df_peng['Item'] = df_peng['Item'].astype(str).str.strip()
            df_peng['Biaya'] = pd.to_numeric(df_peng['Biaya'], errors='coerce')
            df_peng['Tgl'] = pd.to_numeric(df_peng['Tgl'], errors='coerce')
            
            # Hapus yang kosong atau judul tabel yang terbawa
            df_peng = df_peng.dropna(subset=['Item', 'Biaya'])
            df_peng = df_peng[~df_peng['Item'].str.upper().isin(['', 'NAN', 'KETERANGAN', 'KETERANGAN BARANG', 'PENGELUARAN LAIN', 'NOMINAL'])]
            
            # Filter Tanggal
            df_peng_filtered = df_peng[(df_peng['Tgl'] >= rentang_tgl[0]) & (df_peng['Tgl'] <= rentang_tgl[1])]
            
            if not df_peng_filtered.empty:
                df_peng_filtered['Tgl'] = df_peng_filtered['Tgl'].astype(int)
                st.dataframe(df_peng_filtered.reset_index(drop=True), use_container_width=True)
                total_peng = df_peng_filtered['Biaya'].sum()
                st.warning(f"**Total Pengeluaran di tabel ini: Rp {total_peng:,.0f}**".replace(',', '.'))
            else:
                st.info("Tidak ada data pengeluaran di rentang tanggal ini.")
        else:
            st.info("Kolom 'KETERANGAN' di bawah judul 'PENGELUARAN LAIN' tidak ditemukan.")
    else:
        st.error("Judul 'PENGELUARAN LAIN' tidak ditemukan di Spreadsheet.")

except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
