import streamlit as st
import pandas as pd

# Konfigurasi halaman
st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide")

st.title("🥟 Dashboard Lengkap Siomay Jawara Malang")
st.markdown("*(Data otomatis ditarik dari Google Sheets. Filter tersedia di samping kiri)*")

SHEET_ID = "1L1C72W0C8heL5YLahlAliT3K_9gYkcfy9mCAk4rSFXY"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=15)
def load_data():
    return pd.read_excel(EXCEL_URL, sheet_name=None, engine='openpyxl')

try:
    semua_sheet = load_data()
    
    # --- MENU FILTER ---
    st.sidebar.header("🎛️ Filter Data")
    daftar_bulan = list(semua_sheet.keys())
    bulan_terpilih = st.sidebar.selectbox("Pilih Bulan:", daftar_bulan)
    
    df_raw = semua_sheet[bulan_terpilih]
    
    # --- 1. RINGKASAN KEUANGAN ---
    total_omset = pd.to_numeric(df_raw.iloc[1, 1], errors='coerce')
    total_produksi = pd.to_numeric(df_raw.iloc[1, 2], errors='coerce') 
    total_operasional = pd.to_numeric(df_raw.iloc[1, 3], errors='coerce')
    
    st.subheader(f"💰 Ringkasan Keuangan ({bulan_terpilih})")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Omset", f"Rp {total_omset:,.0f}".replace(',', '.'))
    c2.metric("Total Produksi", f"Rp {total_produksi:,.0f}".replace(',', '.'))
    c3.metric("Total Pengeluaran", f"Rp {total_operasional:,.0f}".replace(',', '.'))
    
    # --- 2. LOGIKA RENTANG TANGGAL ---
    # Kita ambil default 1-31 jika tabel utama tidak terbaca
    rentang_tgl = (1, 31)
    df_harian = df_raw.head(35).copy()
    if ' TANGGAL' in df_harian.columns:
        df_harian = df_harian.dropna(subset=[' TANGGAL'])
        df_harian = df_harian[df_harian[' TANGGAL'].astype(str).str.isnumeric()]
        if not df_harian.empty:
            min_t = int(df_harian[' TANGGAL'].min())
            max_t = int(df_harian[' TANGGAL'].max())
            rentang_tgl = st.sidebar.slider("Rentang Tanggal:", min_t, max_t, (min_t, max_t))

    st.markdown("---")

    # --- 3. TABEL PENGELUARAN LAIN (KATA KUNCI: PENGELUARAN LAIN) ---
    st.subheader(f"💸 Rincian Pengeluaran Barang (Tgl {rentang_tgl[0]} - {rentang_tgl[1]})")
    
    # MENCARI KOORDINAT TABEL "PENGELUARAN LAIN"
    target_row, target_col = -1, -1
    for r in range(20):
        for c in range(len(df_raw.columns)):
            isi_sel = str(df_raw.iloc[r, c]).strip().upper()
            if "PENGELUARAN LAIN" in isi_sel:
                target_row = r
                target_col = c
                break
        if target_row != -1: break

    if target_row != -1:
        # Biasanya kolom Tanggal ada di kolom yang sama dengan judul, 
        # Keterangan di kolom sebelahnya, dan Nominal di sebelahnya lagi.
        # Kita ambil area di bawah judul (baris + 2 untuk melewati header)
        df_peng = df_raw.iloc[target_row+2:200, [target_col, target_col+1, target_col+2]].copy()
        df_peng.columns = ['Tgl', 'Item', 'Harga']
        
        # Bersihkan data
        df_peng = df_peng.dropna(subset=['Item'])
        df_peng['Tgl'] = pd.to_numeric(df_peng['Tgl'], errors='coerce')
        df_peng['Harga'] = pd.to_numeric(df_peng['Harga'], errors='coerce').fillna(0)
        
        # Filter Tanggal
        df_peng_final = df_peng[(df_peng['Tgl'] >= rentang_tgl[0]) & (df_peng['Tgl'] <= rentang_tgl[1])]
        df_peng_final = df_peng_final[df_peng_final['Harga'] > 0] # Hanya tampilkan yang ada harganya
        
        if not df_peng_final.empty:
            df_peng_final['Tgl'] = df_peng_final['Tgl'].astype(int).astype(str)
            st.dataframe(df_peng_final.rename(columns={'Tgl': 'Tanggal', 'Item': 'Keterangan Barang', 'Harga': 'Nominal (Rp)'}), use_container_width=True)
            
            total_rincian = df_peng_final['Harga'].sum()
            st.warning(f"**Total biaya untuk rincian di atas: Rp {total_rincian:,.0f}**".replace(',', '.'))
        else:
            st.info("Tidak ada rincian pengeluaran untuk tanggal yang dipilih.")
    else:
        st.error("❌ Judul 'PENGELUARAN LAIN' tidak ditemukan di Spreadsheet. Pastikan tulisannya sama persis.")

    # --- 4. DATA STOK ---
    st.markdown("---")
    st.subheader(f"📦 Stok Barang ({bulan_terpilih})")
    idx_stok = df_raw[df_raw.astype(str).apply(lambda x: x.str.contains('STOK DI BAWA', case=False, na=False)).any(axis=1)].index
    if len(idx_stok) > 0:
        df_s = df_raw.iloc[idx_stok[0]+2 : idx_stok[0]+12, [1, 3, 5, 6]].copy()
        df_s.columns = ["Menu", "Bawa", "Sisa", "Laku"]
        st.dataframe(df_s.dropna(subset=["Menu"]), use_container_width=True)

except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
