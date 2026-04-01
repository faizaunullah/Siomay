import streamlit as st
import pandas as pd

# 1. Setting Halaman
st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide")

st.title("🥟 Dashboard Laporan Siomay Jawara")
st.markdown("*(Laporan Omset, Stok, & Rincian Belanja LPG/Plastik)*")

# Link Google Sheets
SHEET_ID = "1L1C72W0C8heL5YLahlAliT3K_9gYkcfy9mCAk4rSFXY"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=10)
def load_data():
    return pd.read_excel(EXCEL_URL, sheet_name=None, engine='openpyxl')

try:
    semua_sheet = load_data()
    
    # --- SIDEBAR ---
    st.sidebar.header("🎛️ Menu Filter")
    bulan_terpilih = st.sidebar.selectbox("Pilih Bulan:", list(semua_sheet.keys()))
    df_raw = semua_sheet[bulan_terpilih]

    # --- 2. LOGIKA TANGGAL & OMSET UTAMA ---
    df_harian = df_raw.head(35).copy()
    col_tgl = [c for c in df_harian.columns if 'TANGGAL' in str(c).upper()][0]
    df_harian = df_harian.dropna(subset=[col_tgl])
    df_harian = df_harian[df_harian[col_tgl].astype(str).str.isnumeric()]
    df_harian['Tgl_Fix'] = df_harian[col_tgl].astype(int)

    min_t, max_t = int(df_harian['Tgl_Fix'].min()), int(df_harian['Tgl_Fix'].max())
    rentang = st.sidebar.slider("Pilih Rentang Tanggal:", min_t, max_t, (min_t, max_t))

    # --- 3. TABEL RINCIAN BELANJA (LPG, KRESEK, PLASTIK) ---
    st.subheader(f"💸 Rincian Belanja Operasional (LPG, Plastik, dll)")
    
    # Mencari titik koordinat tabel "PENGELUARAN LAIN"
    r_start, c_start = -1, -1
    for r in range(20):
        for c in range(len(df_raw.columns)):
            if "PENGELUARAN LAIN" in str(df_raw.iloc[r, c]).upper():
                r_start, c_start = r, c
                break
        if r_start != -1: break

    if r_start != -1:
        # Ambil 3 kolom: Tanggal, Keterangan, Nominal
        df_belanja = df_raw.iloc[r_start+2:150, [c_start, c_start+1, c_start+2]].copy()
        df_belanja.columns = ['Tgl', 'Keterangan', 'Harga']
        
        # Bersihkan data belanja
        df_belanja = df_belanja.dropna(subset=['Keterangan'])
        df_belanja['Tgl'] = pd.to_numeric(df_belanja['Tgl'], errors='coerce')
        df_belanja['Harga'] = pd.to_numeric(df_belanja['Harga'], errors='coerce').fillna(0)
        
        # Filter berdasarkan slider tanggal
        df_belanja_filt = df_belanja[(df_belanja['Tgl'] >= rentang[0]) & (df_belanja['Tgl'] <= rentang[1])]
        df_belanja_filt = df_belanja_filt[df_belanja_filt['Harga'] > 0]

        if not df_belanja_filt.empty:
            st.dataframe(df_belanja_filt.rename(columns={'Tgl':'Tgl'}), use_container_width=True)
            total_belanja_periode = df_belanja_filt['Harga'].sum()
            st.info(f"**Total Belanja di periode ini: Rp {total_belanja_periode:,.0f}**".replace(',', '.'))
        else:
            st.success("Belum ada catatan belanja (LPG/Plastik) di tanggal ini.")
    else:
        st.error("Tabel 'PENGELUARAN LAIN' tidak ditemukan di Excel.")

    st.markdown("---")

    # --- 4. TABEL UANG SETOR (OMSET - BELANJA) ---
    st.subheader("💰 Laporan Uang Setor")
    
    df_setor = df_harian[(df_harian['Tgl_Fix'] >= rentang[0]) & (df_harian['Tgl_Fix'] <= rentang[1])].copy()
    df_setor['OMSET_RP'] = pd.to_numeric(df_setor.iloc[:, 1], errors='coerce').fillna(0)
    df_setor['PENGELUARAN_RP'] = pd.to_numeric(df_setor.iloc[:, 3], errors='coerce').fillna(0)
    df_setor['SETOR'] = df_setor['OMSET_RP'] - df_setor['PENGELUARAN_RP']

    tabel_setor = df_setor[['Tgl_Fix', 'OMSET_RP', 'PENGELUARAN_RP', 'SETOR']].rename(
        columns={'Tgl_Fix':'Tanggal', 'OMSET_RP':'Omset', 'PENGELUARAN_RP':'Total Belanja', 'SETOR':'Uang Setor'}
    )
    st.dataframe(tabel_setor.reset_index(drop=True), use_container_width=True)

    # --- 5. TABEL STOK (PENCARIAN DINAMIS) ---
    st.markdown("---")
    st.subheader("📦 Laporan Stok Barang")
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
