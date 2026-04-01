import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide")

st.title("🥟 Dashboard Super Lengkap Siomay Jawara")
st.markdown("*(Grafik Omset, Rincian Belanja LPG/Plastik, Uang Setor, & Stok Barang)*")

SHEET_ID = "1L1C72W0C8heL5YLahlAliT3K_9gYkcfy9mCAk4rSFXY"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=10)
def load_data():
    return pd.read_excel(EXCEL_URL, sheet_name=None, engine='openpyxl')

try:
    semua_sheet = load_data()
    
    st.sidebar.header("🎛️ Menu Filter")
    bulan_terpilih = st.sidebar.selectbox("Pilih Bulan:", list(semua_sheet.keys()))
    df_raw = semua_sheet[bulan_terpilih]

    # --- 1. AMBIL DATA OMSET HARIAN (TABEL KIRI) ---
    df_harian = df_raw.head(35).copy()
    
    # Mencari kolom secara akurat berdasarkan namanya
    col_tgl = [c for c in df_harian.columns if 'TANGGAL' in str(c).upper()][0]
    col_omset = [c for c in df_harian.columns if 'OMSET' in str(c).upper()][0]
    
    df_harian = df_harian.dropna(subset=[col_tgl])
    df_harian = df_harian[df_harian[col_tgl].astype(str).str.isnumeric()]
    
    df_main = pd.DataFrame()
    df_main['Tanggal'] = df_harian[col_tgl].astype(int)
    df_main['Omset'] = pd.to_numeric(df_harian[col_omset], errors='coerce').fillna(0)

    min_t, max_t = int(df_main['Tanggal'].min()), int(df_main['Tanggal'].max())
    rentang = st.sidebar.slider("Pilih Rentang Tanggal:", min_t, max_t, (min_t, max_t))

    # --- 2. AMBIL DATA PENGELUARAN LAIN (TABEL KANAN) ---
    r_start, c_start = -1, -1
    for r in range(25):
        for c in range(len(df_raw.columns)):
            if "PENGELUARAN LAIN" in str(df_raw.iloc[r, c]).upper():
                r_start, c_start = r, c
                break
        if r_start != -1: break

    df_peng_agg = pd.DataFrame(columns=['Tanggal', 'Total Belanja', 'Rincian Belanja'])
    
    if r_start != -1:
        # Ambil 3 kolom: Tanggal, Keterangan, Nominal
        df_peng = df_raw.iloc[r_start+2:150, [c_start, c_start+1, c_start+2]].copy()
        df_peng.columns = ['Tanggal', 'Keterangan', 'Nominal']
        df_peng = df_peng.dropna(subset=['Keterangan'])
        df_peng['Tanggal'] = pd.to_numeric(df_peng['Tanggal'], errors='coerce')
        df_peng['Nominal'] = pd.to_numeric(df_peng['Nominal'], errors='coerce').fillna(0)
        df_peng = df_peng[df_peng['Tanggal'] > 0]
        
        # JAHIT DATA: Menggabungkan rincian belanja di hari yang sama (Contoh: "LPG, Kresek")
        if not df_peng.empty:
            df_peng_agg = df_peng.groupby('Tanggal').agg({
                'Nominal': 'sum',
                'Keterangan': lambda x: ', '.join(x.astype(str))
            }).reset_index()
            df_peng_agg.columns = ['Tanggal', 'Total Belanja', 'Rincian Belanja']

    # --- 3. GABUNGKAN OMSET DAN PENGELUARAN ---
    df_final = pd.merge(df_main, df_peng_agg, on='Tanggal', how='left')
    df_final['Total Belanja'] = df_final['Total Belanja'].fillna(0)
    df_final['Rincian Belanja'] = df_final['Rincian Belanja'].fillna("-")
    
    # Hitung Uang Setor Otomatis
    df_final['Uang Setor'] = df_final['Omset'] - df_final['Total Belanja']
    
    # Filter Slider Tanggal
    df_final = df_final[(df_final['Tanggal'] >= rentang[0]) & (df_final['Tanggal'] <= rentang[1])]
    
    # --- 4. TAMPILAN GRAFIK ---
    st.subheader(f"📈 Grafik Omset Harian (Tgl {rentang[0]} - {rentang[1]})")
    df_grafik = df_final.copy()
    df_grafik['Tgl_Str'] = "Tgl " + df_grafik['Tanggal'].astype(str)
    st.line_chart(data=df_grafik.set_index('Tgl_Str')['Omset'])
    
    st.markdown("---")

    # --- 5. TAMPILAN TABEL UANG SETOR & RINCIAN ---
    st.subheader("💰 Laporan Uang Setor & Rincian Belanja")
    
    tabel_tampil = df_final[['Tanggal', 'Omset', 'Total Belanja', 'Uang Setor', 'Rincian Belanja']].copy()
    tabel_tampil.columns = ['Tanggal', 'Omset (Rp)', 'Total Belanja (Rp)', 'Uang Setor (Rp)', 'Daftar Barang Dibeli']
    
    st.dataframe(tabel_tampil.reset_index(drop=True), use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Omset", f"Rp {df_final['Omset'].sum():,.0f}".replace(',', '.'))
    c2.metric("Total Pengeluaran", f"Rp {df_final['Total Belanja'].sum():,.0f}".replace(',', '.'))
    c3.warning(f"**💰 TOTAL SETOR: Rp {df_final['Uang Setor'].sum():,.0f}**".replace(',', '.'))

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
