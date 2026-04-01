import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide")
st.title("🥟 Dashboard Ultimate Siomay Jawara")
st.markdown("*(Menampilkan Seluruh Data dari Spreadsheet: Omset, Pengeluaran, Setoran, dan Stok)*")

# Link Spreadsheet
SHEET_ID = "1U8Wu-iBqii4Mj_wPXmaX6722phs-LywC"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=10)
def load_data():
    return pd.read_excel(EXCEL_URL, sheet_name=None, engine='openpyxl')

try:
    semua_sheet = load_data()
    st.sidebar.header("🎛️ Menu Filter")
    bulan_terpilih = st.sidebar.selectbox("Pilih Bulan:", list(semua_sheet.keys()))
    df_raw = semua_sheet[bulan_terpilih]

    # --- 1. MEMBACA TABEL UTAMA FULL 11 KOLOM ---
    r_header = -1
    for r in range(15):
        row_str = " ".join([str(x).upper() for x in df_raw.iloc[r, 0:6]])
        if "TANGGAL" in row_str and "OMSET" in row_str:
            r_header = r
            break
            
    if r_header != -1:
        # Ambil 31 baris (maksimal jumlah hari) dan 11 kolom
        df_main = df_raw.iloc[r_header+1 : r_header+32, 0:11].copy()
        
        # Ganti nama kolom sesuai Excel
        df_main.columns = [
            'Tanggal', 'Omset', 'Dr Produksi', 'Belanja / Op', '% Pengeluaran', 
            'Gaji', 'Laba Bersih', '% Laba', 'Setor UANG', 'Rincian (Modal & Laba)', 'Selisih Uang'
        ]
        
        # BERSihkan Tanggal: Hapus baris yang tanggalnya NaN atau bukan angka
        df_main['Tanggal'] = pd.to_numeric(df_main['Tanggal'], errors='coerce')
        df_main = df_main.dropna(subset=['Tanggal'])
        df_main['Tanggal'] = df_main['Tanggal'].astype(int)
        
        # Konversi Kolom Angka (NaN jadi 0)
        cols_num = ['Omset', 'Dr Produksi', 'Belanja / Op', 'Gaji', 'Laba Bersih', 'Setor UANG', 'Selisih Uang']
        for col in cols_num:
            df_main[col] = pd.to_numeric(df_main[col], errors='coerce').fillna(0)
            
        # Bersihkan Kolom Teks (NaN jadi "-")
        df_main['Rincian (Modal & Laba)'] = df_main['Rincian (Modal & Laba)'].astype(str).replace('nan', '-').replace('None', '-')
        df_main['% Pengeluaran'] = df_main['% Pengeluaran'].astype(str).replace('nan', '-').replace('None', '-')
        df_main['% Laba'] = df_main['% Laba'].astype(str).replace('nan', '-').replace('None', '-')
        
        min_t, max_t = int(df_main['Tanggal'].min()), int(df_main['Tanggal'].max())
        rentang = st.sidebar.slider("Pilih Rentang Tanggal:", min_t, max_t, (min_t, max_t))
        
        df_main_filter = df_main[(df_main['Tanggal'] >= rentang[0]) & (df_main['Tanggal'] <= rentang[1])]

        st.subheader(f"💵 Ringkasan Keuangan (Tgl {rentang[0]} - {rentang[1]})")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Omset", f"Rp {df_main_filter['Omset'].sum():,.0f}".replace(',', '.'))
        c2.metric("Total Pengeluaran (Prod + Op)", f"Rp {(df_main_filter['Dr Produksi'].sum() + df_main_filter['Belanja / Op'].sum()):,.0f}".replace(',', '.'))
        c3.metric("Total Laba Bersih", f"Rp {df_main_filter['Laba Bersih'].sum():,.0f}".replace(',', '.'))
        c4.error(f"**TOTAL UANG SETOR: Rp {df_main_filter['Setor UANG'].sum():,.0f}**".replace(',', '.'))

        st.markdown("---")
        st.subheader("📊 Tabel Laporan Utama Lengkap")
        # Menampilkan tanpa index agar rapi
        st.dataframe(df_main_filter.reset_index(drop=True), use_container_width=True)

    else:
        st.error("❌ Format Tabel Utama tidak ditemukan.")
        st.stop()

    # --- 2. MEMBACA TABEL PENGELUARAN LAIN ---
    st.markdown("---")
    st.subheader(f"🛍️ Rincian Pengeluaran Lain (LPG/Tahu) (Tgl {rentang[0]} - {rentang[1]})")
    
    r_peng, c_peng = -1, -1
    for r in range(25):
        for c in range(5, len(df_raw.columns)): 
            if "PENGELUARAN LAIN" in str(df_raw.iloc[r, c]).upper():
                r_peng, c_peng = r, c
                break
        if r_peng != -1: break

    if r_peng != -1:
        df_peng = df_raw.iloc[r_peng+2:150, [c_peng, c_peng+1, c_peng+2]].copy()
        df_peng.columns = ['Tanggal', 'Keterangan Barang', 'Nominal']
        
        # BERSihkan Data
        df_peng['Keterangan Barang'] = df_peng['Keterangan Barang'].astype(str).str.strip()
        kata_buang = ['', 'NAN', 'NONE', 'KETERANGAN', 'TANGGAL', 'NOMINAL']
        df_peng = df_peng[~df_peng['Keterangan Barang'].str.upper().isin(kata_buang)]
        
        df_peng['Tanggal'] = pd.to_numeric(df_peng['Tanggal'], errors='coerce')
        df_peng['Nominal'] = pd.to_numeric(df_peng['Nominal'], errors='coerce').fillna(0)
        df_peng = df_peng.dropna(subset=['Tanggal'])
        
        df_peng_filter = df_peng[(df_peng['Tanggal'] >= rentang[0]) & (df_peng['Tanggal'] <= rentang[1])]
        df_peng_filter = df_peng_filter[df_peng_filter['Nominal'] > 0]
        
        if not df_peng_filter.empty:
            df_peng_filter['Tanggal'] = df_peng_filter['Tanggal'].astype(int)
            st.dataframe(df_peng_filter.reset_index(drop=True), use_container_width=True)
            st.info(f"Total Nominal Pengeluaran Lain: Rp {df_peng_filter['Nominal'].sum():,.0f}".replace(',', '.'))
        else:
            st.success("Tidak ada rincian belanja tercatat di rentang tanggal ini.")
    else:
        st.warning("Tabel 'PENGELUARAN LAIN' tidak ditemukan.")

    # --- 3. MEMBACA TABEL STOK BARANG ---
    st.markdown("---")
    st.subheader("📦 Tabel Stok Bawa Harian/Bulanan")
    
    r_stok, c_stok = -1, -1
    for r in range(150):
        for c in range(len(df_raw.columns)):
            teks = str(df_raw.iloc[r, c]).upper()
            if "STOK DI BAWA" in teks or "PENTOL" in teks:
                r_stok, c_stok = r, c
                break
        if r_stok != -1: break

    if r_stok != -1:
        df_stok = df_raw.iloc[r_stok:r_stok+15, max(0, c_stok-2):min(len(df_raw.columns), c_stok+5)].copy()
        # Bersihkan baris yang sepenuhnya NaN
        df_stok = df_stok.dropna(how='all')
        # Isi NaN di sel dengan string kosong agar rapi
        df_stok = df_stok.fillna("")
        st.dataframe(df_stok.reset_index(drop=True), use_container_width=True)
    else:
        st.warning("Tabel Stok tidak ditemukan di bulan ini.")

except Exception as e:
    st.error(f"Terjadi Kesalahan: {e}. Pastikan Link Spreadsheet dapat diakses.")
