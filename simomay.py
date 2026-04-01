import streamlit as st
import pandas as pd

# 1. Konfigurasi Halaman (Wajib Paling Atas)
st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide")

st.title("🥟 Dashboard Ultimate Siomay Jawara")
st.markdown("*(Ringkas, Lengkap, dan Terpadu: Pantau Omset, Semua Belanja, Setoran, dan Stok)*")

# Link Spreadsheet Terbarumu
SHEET_ID = "1U8Wu-iBqii4Mj_wPXmaX6722phs-LywC"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=10)
def load_data():
    return pd.read_excel(EXCEL_URL, sheet_name=None, engine='openpyxl')

try:
    semua_sheet = load_data()
    
    # --- SIDEBAR FILTER ---
    st.sidebar.header("🎛️ Menu Filter")
    bulan_terpilih = st.sidebar.selectbox("Pilih Bulan:", list(semua_sheet.keys()))
    df_raw = semua_sheet[bulan_terpilih]

    # --- 2. TARIK DATA TABEL UTAMA (KIRI) ---
    # Mengambil 5 kolom pertama: Tanggal, Omset, Produksi, Belanja Op, Rincian
    df_main = df_raw.iloc[1:40, 0:5].copy()
    df_main.columns = ['Tanggal', 'Omset', 'Biaya Produksi', 'Belanja Operasional', 'Rincian Utama']
    
    # Bersihkan Data
    df_main['Tanggal'] = pd.to_numeric(df_main['Tanggal'], errors='coerce')
    df_main = df_main.dropna(subset=['Tanggal'])
    df_main['Tanggal'] = df_main['Tanggal'].astype(int)
    
    df_main['Omset'] = pd.to_numeric(df_main['Omset'], errors='coerce').fillna(0)
    df_main['Biaya Produksi'] = pd.to_numeric(df_main['Biaya Produksi'], errors='coerce').fillna(0)
    df_main['Belanja Operasional'] = pd.to_numeric(df_main['Belanja Operasional'], errors='coerce').fillna(0)
    df_main['Rincian Utama'] = df_main['Rincian Utama'].fillna("-")
    
    # Hitung Uang Setor (Omset - (Produksi + Operasional))
    df_main['Uang Setor'] = df_main['Omset'] - (df_main['Biaya Produksi'] + df_main['Belanja Operasional'])

    # Filter Tanggal
    min_t, max_t = int(df_main['Tanggal'].min()), int(df_main['Tanggal'].max())
    rentang = st.sidebar.slider("Pilih Rentang Tanggal:", min_t, max_t, (min_t, max_t))
    df_main_filter = df_main[(df_main['Tanggal'] >= rentang[0]) & (df_main['Tanggal'] <= rentang[1])]

    # --- 3. TARIK SEMUA TABEL RINCIAN (KANAN) ---
    # Radar ini akan mencari semua tabel yang punya kolom "KETERANGAN" di Excel
    semua_rincian = []
    kolom_ditemukan = [] 
    
    for r in range(20):
        for c in range(1, len(df_raw.columns) - 1):
            val = str(df_raw.iloc[r, c]).strip().upper()
            if "KETERANGAN" in val and c not in kolom_ditemukan:
                kolom_ditemukan.append(c)
                
                # Cari nama tabel (misal "PENGELUARAN LAIN" atau "PRODUKSI")
                nama_tabel = "Rincian Belanja"
                if r > 0:
                    atas = str(df_raw.iloc[r-1, c-1]).strip()
                    if atas and atas.lower() != 'nan':
                        nama_tabel = atas
                
                # Ambil datanya
                df_temp = df_raw.iloc[r+1:150, [c-1, c, c+1]].copy()
                df_temp.columns = ['Tanggal', 'Barang Dibeli', 'Nominal']
                df_temp = df_temp.dropna(subset=['Barang Dibeli'])
                
                # Bersihkan Teks
                df_temp['Barang Dibeli'] = df_temp['Barang Dibeli'].astype(str).str.strip()
                kata_buang = ['', 'NAN', 'NONE', 'KETERANGAN', 'KETERANGAN BARANG', 'TANGGAL', 'NOMINAL']
                df_temp = df_temp[~df_temp['Barang Dibeli'].str.upper().isin(kata_buang)]
                
                df_temp['Tanggal'] = pd.to_numeric(df_temp['Tanggal'], errors='coerce')
                df_temp['Nominal'] = pd.to_numeric(df_temp['Nominal'], errors='coerce').fillna(0)
                df_temp = df_temp.dropna(subset=['Tanggal'])
                
                if not df_temp.empty:
                    df_temp['Kategori Tabel'] = nama_tabel
                    semua_rincian.append(df_temp)

    # Gabungkan semua tabel rincian yang ditemukan
    if semua_rincian:
        df_rincian_gabung = pd.concat(semua_rincian, ignore_index=True)
        df_rincian_gabung = df_rincian_gabung[(df_rincian_gabung['Tanggal'] >= rentang[0]) & (df_rincian_gabung['Tanggal'] <= rentang[1])]
        df_rincian_gabung = df_rincian_gabung[df_rincian_gabung['Nominal'] > 0]
    else:
        df_rincian_gabung = pd.DataFrame()

    # --- 4. KOTAK RINGKASAN ATAS ---
    st.subheader(f"💵 Ringkasan Keuangan (Tgl {rentang[0]} - {rentang[1]})")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Omset", f"Rp {df_main_filter['Omset'].sum():,.0f}".replace(',', '.'))
    c2.metric("Biaya Produksi", f"Rp {df_main_filter['Biaya Produksi'].sum():,.0f}".replace(',', '.'))
    c3.metric("Belanja Operasional", f"Rp {df_main_filter['Belanja Operasional'].sum():,.0f}".replace(',', '.'))
    c4.error(f"**UANG SETOR: Rp {df_main_filter['Uang Setor'].sum():,.0f}**".replace(',', '.'))
    
    st.markdown("---")

    # --- 5. TAMPILAN TABS (AGAR RINGKAS & LENGKAP) ---
    tab1, tab2, tab3 = st.tabs(["📊 Laporan Utama & Setor", "🛍️ Daftar Rincian Belanja", "📦 Laporan Stok"])
    
    with tab1:
        st.write("### Grafik Omset Harian")
        grafik_data = df_main_filter.copy()
        grafik_data['Tgl'] = "Tgl " + grafik_data['Tanggal'].astype(str)
        st.line_chart(data=grafik_data.set_index('Tgl')['Omset'])
        
        st.write("### Tabel Setoran Harian")
        st.dataframe(df_main_filter.rename(columns={'Biaya Produksi': 'Produksi (Rp)', 'Belanja Operasional': 'Operasional (Rp)', 'Omset': 'Omset (Rp)', 'Uang Setor': 'Setor (Rp)'}).reset_index(drop=True), use_container_width=True)

    with tab2:
        st.write("### Semua Catatan Pembelian Barang")
        st.write("*(Diambil otomatis dari semua tabel rincian di sebelah kanan Spreadsheet Anda)*")
        if not df_rincian_gabung.empty:
            st.dataframe(df_rincian_gabung[['Tanggal', 'Kategori Tabel', 'Barang Dibeli', 'Nominal']].rename(columns={'Nominal': 'Harga (Rp)'}).reset_index(drop=True), use_container_width=True)
        else:
            st.info("Tidak ada catatan pembelian barang pada rentang tanggal ini.")

    with tab3:
        st.write("### Catatan Stok Barang")
        idx_stok = -1
        for r in range(len(df_raw)):
            if "STOK DI BAWA" in str(df_raw.iloc[r, :]).upper():
                idx_stok = r
                break
        if idx_stok != -1:
            df_s = df_raw.iloc[idx_stok+2:idx_stok+12, [1, 3, 5, 6]].copy()
            df_s.columns = ["Menu", "Bawa", "Sisa", "Laku"]
            st.dataframe(df_s.dropna(subset=["Menu"]).reset_index(drop=True), use_container_width=True)
        else:
            st.warning("Tabel stok tidak ditemukan.")

except Exception as e:
    st.error(f"Terjadi kendala saat membaca Spreadsheet: {e}")
