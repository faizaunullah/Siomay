import streamlit as st
import pandas as pd

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide")

st.title("🥟 Dashboard Laporan Siomay Jawara")
st.markdown("*(Data Otomatis: Omset, Pengeluaran, Uang Setor & Deskripsi)*")

SHEET_ID = "1L1C72W0C8heL5YLahlAliT3K_9gYkcfy9mCAk4rSFXY"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=10)
def load_data():
    return pd.read_excel(EXCEL_URL, sheet_name=None, engine='openpyxl')

try:
    semua_sheet = load_data()
    st.sidebar.header("🎛️ Filter")
    bulan_terpilih = st.sidebar.selectbox("Pilih Bulan:", list(semua_sheet.keys()))
    df_raw = semua_sheet[bulan_terpilih]

    # --- LOGIKA TANGGAL ---
    df_main = df_raw.head(35).copy()
    # Mencari kolom Tanggal secara fleksibel
    col_tgl = [c for c in df_main.columns if 'TANGGAL' in str(c).upper()][0]
    df_main = df_main.dropna(subset=[col_tgl])
    df_main = df_main[df_main[col_tgl].astype(str).str.isnumeric()]
    df_main['Tgl_Int'] = df_main[col_tgl].astype(int)

    min_t, max_t = int(df_main['Tgl_Int'].min()), int(df_main['Tgl_Int'].max())
    rentang = st.sidebar.slider("Rentang Tanggal:", min_t, max_t, (min_t, max_t))

    # --- PROSES DATA UTAMA ---
    # Kita ambil Omset, Pengeluaran (Belanja/Op), dan Rincian
    # Berdasarkan screenshot: Omset(Col B), Pengeluaran(Col D), Rincian(Col E)
    df_final = df_main[(df_main['Tgl_Int'] >= rentang[0]) & (df_main['Tgl_Int'] <= rentang[1])].copy()
    
    # Ambil kolom Omset dan Pengeluaran (pastikan nama kolom sesuai atau gunakan urutan kolom)
    df_final['OMSET_VAL'] = pd.to_numeric(df_final.iloc[:, 1], errors='coerce').fillna(0)
    df_final['PENGELUARAN_VAL'] = pd.to_numeric(df_final.iloc[:, 3], errors='coerce').fillna(0)
    
    # Ambil Deskripsi/Rincian (Biasanya kolom setelah Pengeluaran)
    df_final['DESKRIPSI'] = df_final.iloc[:, 4].fillna("-")

    # HITUNG UANG SETOR
    df_final['UANG_SETOR'] = df_final['OMSET_VAL'] - df_final['PENGELUARAN_VAL']

    # --- TAMPILAN ---
    st.subheader(f"📊 Laporan Harian: Tgl {rentang[0]} - {rentang[1]}")
    
    # Tabel Utama
    tabel_tampil = df_final[['Tgl_Int', 'OMSET_VAL', 'PENGELUARAN_VAL', 'UANG_SETOR', 'DESKRIPSI']].rename(
        columns={
            'Tgl_Int': 'Tanggal',
            'OMSET_VAL': 'Omset (Rp)',
            'PENGELUARAN_VAL': 'Pengeluaran (Rp)',
            'UANG_SETOR': 'Uang Setor (Rp)',
            'DESKRIPSI': 'Keterangan/Deskripsi Belanja'
        }
    )
    
    st.dataframe(tabel_tampil.reset_index(drop=True), use_container_width=True)

    # Ringkasan Bawah
    c1, c2, c3 = st.columns(3)
    total_setor = df_final['UANG_SETOR'].sum()
    c1.metric("Total Omset", f"Rp {df_final['OMSET_VAL'].sum():,.0f}".replace(',', '.'))
    c2.metric("Total Pengeluaran", f"Rp {df_final['PENGELUARAN_VAL'].sum():,.0f}".replace(',', '.'))
    c3.warning(f"**TOTAL UANG SETOR: Rp {total_setor:,.0f}**".replace(',', '.'))

    # --- TABEL STOK (Tetap Ada) ---
    st.markdown("---")
    st.subheader("📦 Stok Barang")
    r_stok = -1
    for r in range(len(df_raw)):
        if "STOK DI BAWA" in str(df_raw.iloc[r, :]).upper():
            r_stok = r
            break
    if r_stok != -1:
        df_s = df_raw.iloc[r_stok+2:r_stok+12, [1, 3, 5, 6]].copy()
        df_s.columns = ["Menu", "Bawa", "Sisa", "Laku"]
        st.dataframe(df_s.dropna(subset=["Menu"]), use_container_width=True)

except Exception as e:
    st.error(f"Ada kendala: {e}. Pastikan format kolom Excel tidak berubah.")
