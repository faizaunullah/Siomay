import streamlit as st
import pandas as pd

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide")

st.title("🥟 Dashboard Ultimate Siomay Jawara")
st.markdown("*(Versi 23.0: Perbaikan Radar Stok & Rincian Belanja Maret)*")

# Link Spreadsheet (Pastikan ID ini benar)
SHEET_ID = "1L1C72W0C8heL5YLahlAliT3K_9gYkcfy9mCAk4rSFXY"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=5)
def load_data():
    return pd.read_excel(EXCEL_URL, sheet_name=None, engine='openpyxl')

try:
    semua_sheet = load_data()
    
    # --- SIDEBAR ---
    st.sidebar.header("🎛️ Menu Filter")
    bulan_terpilih = st.sidebar.selectbox("Pilih Bulan:", list(semua_sheet.keys()))
    df_raw = semua_sheet[bulan_terpilih]

    # ---------------------------------------------------------
    # 1. PENCARIAN TABEL UTAMA (OMSET & SETOR)
    # ---------------------------------------------------------
    r_omset, c_omset = -1, -1
    for r in range(15):
        for c in range(len(df_raw.columns)):
            if "OMSET" in str(df_raw.iloc[r, c]).upper():
                r_omset, c_omset = r, c
                break
        if r_omset != -1: break

    if c_omset != -1:
        # Ambil data harian (31 hari)
        df_main = df_raw.iloc[r_omset+1:r_omset+35, [c_omset-1, c_omset, c_omset+1, c_omset+2]].copy()
        df_main.columns = ['Tanggal', 'Omset', 'Produksi', 'Operasional']
        
        df_main['Tanggal'] = pd.to_numeric(df_main['Tanggal'], errors='coerce')
        df_main = df_main.dropna(subset=['Tanggal'])
        df_main['Tanggal'] = df_main['Tanggal'].astype(int)
        
        for col in ['Omset', 'Produksi', 'Operasional']:
            df_main[col] = pd.to_numeric(df_main[col], errors='coerce').fillna(0)
        
        df_main['Uang Setor'] = df_main['Omset'] - (df_main['Produksi'] + df_main['Operasional'])
        
        min_t, max_t = int(df_main['Tanggal'].min()), int(df_main['Tanggal'].max())
        rentang = st.sidebar.slider("Pilih Rentang Tanggal:", min_t, max_t, (min_t, max_t))
        df_main_filter = df_main[(df_main['Tanggal'] >= rentang[0]) & (df_main['Tanggal'] <= rentang[1])]
    else:
        st.error("Gagal menemukan tabel Omset. Pastikan ada tulisan 'OMSET' di Excel.")
        st.stop()

    # ---------------------------------------------------------
    # 2. PENCARIAN RINCIAN BELANJA (LPG, KRESEK, DLL)
    # ---------------------------------------------------------
    semua_belanja = []
    # Mencari kata kunci rincian di seluruh sheet
    for r in range(50):
        for c in range(len(df_raw.columns)):
            teks = str(df_raw.iloc[r, c]).upper()
            if "KETERANGAN" in teks or "RINCIAN" in teks:
                # Ambil 3 kolom: Tgl, Ket, Harga
                df_b = df_raw.iloc[r+1:150, [c-1, c, c+1]].copy()
                df_b.columns = ['Tgl', 'Barang', 'Harga']
                df_b = df_b.dropna(subset=['Barang'])
                df_b['Tgl'] = pd.to_numeric(df_b['Tgl'], errors='coerce')
                df_b['Harga'] = pd.to_numeric(df_b['Harga'], errors='coerce').fillna(0)
                df_b = df_b[df_b['Harga'] > 0]
                if not df_b.empty:
                    semua_belanja.append(df_b)

    df_belanja_gabung = pd.concat(semua_belanja).drop_duplicates() if semua_belanja else pd.DataFrame()
    if not df_belanja_gabung.empty:
        df_belanja_gabung = df_belanja_gabung[(df_belanja_gabung['Tgl'] >= rentang[0]) & (df_belanja_gabung['Tgl'] <= rentang[1])]

    # ---------------------------------------------------------
    # 3. TAMPILAN DASHBOARD (TABS)
    # ---------------------------------------------------------
    st.subheader(f"💵 Keuangan: {bulan_terpilih} (Tgl {rentang[0]}-{rentang[1]})")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Omset", f"Rp {df_main_filter['Omset'].sum():,.0f}".replace(',', '.'))
    c2.metric("Total Produksi", f"Rp {df_main_filter['Produksi'].sum():,.0f}".replace(',', '.'))
    c3.metric("Total Operasional", f"Rp {df_main_filter['Operasional'].sum():,.0f}".replace(',', '.'))
    c4.error(f"**SETORAN: Rp {df_main_filter['Uang Setor'].sum():,.0f}**".replace(',', '.'))

    tab1, tab2, tab3 = st.tabs(["📊 Laporan & Grafik", "🛍️ Rincian LPG/Kresek", "📦 Stok Barang"])

    with tab1:
        st.line_chart(data=df_main_filter.set_index('Tanggal')['Omset'])
        st.dataframe(df_main_filter.reset_index(drop=True), use_container_width=True)

    with tab2:
        if not df_belanja_gabung.empty:
            st.write("### Daftar Pembelian Barang")
            st.dataframe(df_belanja_gabung.reset_index(drop=True), use_container_width=True)
            st.info(f"Total Rincian Belanja: Rp {df_belanja_gabung['Harga'].sum():,.0f}".replace(',', '.'))
        else:
            st.info("Belum ada rincian belanja (LPG/Kresek) yang terbaca.")

    with tab3:
        # --- PERBAIKAN RADAR STOK ---
        st.write("### Laporan Stok")
        r_stok, c_stok = -1, -1
        # Cari kata kunci yang pasti ada di tabel stok
        for r in range(len(df_raw)):
            if r > 100: break
            row_str = " ".join(df_raw.iloc[r, :].astype(str).upper())
            if "STOK DI BAWA" in row_str or "PENTOL" in row_str:
                r_stok = r
                # Temukan kolom mana yang berisi 'PENTOL'
                for c in range(len(df_raw.columns)):
                    if "PENTOL" in str(df_raw.iloc[r, c]).upper() or "STOK DI BAWA" in str(df_raw.iloc[r, c]).upper():
                        c_stok = c
                        break
                break
        
        if r_stok != -1:
            # Ambil blok data stok (Nama, Bawa, Sisa, Laku)
            # Biasanya Nama ada di c_stok, Bawa di c_stok+2, dsb. Kita ambil range lebar.
            df_stok_raw = df_raw.iloc[r_stok:r_stok+15, c_stok-1:c_stok+6].copy()
            st.write("Ditemukan tabel stok, sedang memproses...")
            st.dataframe(df_stok_raw.dropna(how='all').reset_index(drop=True), use_container_width=True)
        else:
            st.warning("Tabel Stok tidak ditemukan. Pastikan ada tulisan 'PENTOL' atau 'STOK DI BAWA' di Excel.")

except Exception as e:
    st.error(f"Koneksi Gagal: {e}")
