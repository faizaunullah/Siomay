import streamlit as st
import pandas as pd

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide")

st.title("🥟 Dashboard Super Lengkap Siomay Jawara")
st.markdown("*(Grafik Omset, Rincian Belanja LPG/Plastik, Uang Setor, & Stok Barang)*")

# Link Google Sheets
SHEET_ID = "1L1C72W0C8heL5YLahlAliT3K_9gYkcfy9mCAk4rSFXY"
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

    # --- 2. LOGIKA TANGGAL & DATA UTAMA ---
    df_harian = df_raw.head(35).copy()
    col_tgl = [c for c in df_harian.columns if 'TANGGAL' in str(c).upper()][0]
    df_harian = df_harian.dropna(subset=[col_tgl])
    df_harian = df_harian[df_harian[col_tgl].astype(str).str.isnumeric()]
    df_harian['Tgl_Fix'] = df_harian[col_tgl].astype(int)

    min_t, max_t = int(df_harian['Tgl_Fix'].min()), int(df_harian['Tgl_Fix'].max())
    rentang = st.sidebar.slider("Pilih Rentang Tanggal:", min_t, max_t, (min_t, max_t))

    df_filt = df_harian[(df_harian['Tgl_Fix'] >= rentang[0]) & (df_harian['Tgl_Fix'] <= rentang[1])].copy()
    df_filt['OMSET_RP'] = pd.to_numeric(df_filt.iloc[:, 1], errors='coerce').fillna(0)
    df_filt['Tanggal_Str'] = "Tgl " + df_filt['Tgl_Fix'].astype(str)

    # --- 3. GRAFIK OMSET ---
    st.subheader(f"📈 Grafik Omset Harian (Tgl {rentang[0]} - {rentang[1]})")
    if not df_filt.empty:
        st.line_chart(data=df_filt.set_index('Tanggal_Str')['OMSET_RP'])
    else:
        st.info("Tidak ada data untuk menampilkan grafik.")

    st.markdown("---")

    # --- 4. TABEL UANG SETOR (DENGAN RINCIAN LANGSUNG) ---
    st.subheader("💰 Laporan Uang Setor & Rincian Belanja")
    
    # Mengambil pengeluaran (Kolom 3) dan Deskripsi Langsung (Kolom 4/5)
    df_filt['PENGELUARAN_RP'] = pd.to_numeric(df_filt.iloc[:, 3], errors='coerce').fillna(0)
    df_filt['SETOR'] = df_filt['OMSET_RP'] - df_filt['PENGELUARAN_RP']
    
    # Mengambil kolom RINCIAN di sebelah pengeluaran (di Excel biasanya kolom E / index 4)
    df_filt['DESKRIPSI_BELANJA'] = df_filt.iloc[:, 4].astype(str).replace('nan', '-').replace('None', '-')

    tabel_setor = df_filt[['Tgl_Fix', 'OMSET_RP', 'PENGELUARAN_RP', 'SETOR', 'DESKRIPSI_BELANJA']].rename(
        columns={'Tgl_Fix':'Tgl', 'OMSET_RP':'Omset (Rp)', 'PENGELUARAN_RP':'Total Belanja', 'SETOR':'Uang Setor', 'DESKRIPSI_BELANJA':'Rincian Belanja (LPG/Kresek/dll)'}
    )
    st.dataframe(tabel_setor.reset_index(drop=True), use_container_width=True)

    # Total Ringkasan
    c1, c2 = st.columns(2)
    c1.info(f"**Total Pengeluaran/Belanja (Tgl {rentang[0]}-{rentang[1]}): Rp {df_filt['PENGELUARAN_RP'].sum():,.0f}**".replace(',', '.'))
    c2.warning(f"**Total Uang Setoran Bersih (Tgl {rentang[0]}-{rentang[1]}): Rp {df_filt['SETOR'].sum():,.0f}**".replace(',', '.'))

    # --- 5. EKSTRA: TABEL KHUSUS RINCIAN BARANG SAJA ---
    st.markdown("---")
    st.subheader("📝 Daftar Barang yang Dibeli")
    
    # Saring hanya hari-hari yang ada pengeluarannya
    df_barang = df_filt[df_filt['PENGELUARAN_RP'] > 0][['Tgl_Fix', 'DESKRIPSI_BELANJA', 'PENGELUARAN_RP']]
    df_barang.columns = ['Tanggal', 'Barang yang Dibeli', 'Harga (Rp)']
    
    if not df_barang.empty:
        st.table(df_barang.reset_index(drop=True)) # Menggunakan st.table agar teks tidak terpotong
    else:
        st.success("Tidak ada barang yang dibeli pada rentang tanggal ini.")

    # --- 6. TABEL STOK BARANG ---
    st.markdown("---")
    st.subheader("📦 Laporan Stok")
    idx_stok = -1
    for r in range(len(df_raw)):
        if "STOK DI BAWA" in str(df_raw.iloc[r, :]).upper():
            idx_stok = r
            break
    if idx_stok != -1:
        df_s = df_raw.iloc[idx_stok+2:idx_stok+12, [1, 3, 5, 6]].copy()
        df_s.columns = ["Menu", "Bawa", "Sisa", "Laku"]
        st.dataframe(df_s.dropna(subset=["Menu"]).reset_index(drop=True), use_container_width=True)

except Exception as e:
    st.error(f"Terjadi kendala: {e}")
