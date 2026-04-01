import streamlit as st
import pandas as pd

# 1. Konfigurasi Halaman & Judul
st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide")

st.title("🥟 Dashboard Super Lengkap Siomay Jawara")
st.markdown("*(Grafik Omset, Rincian Belanja, Uang Setor, & Stok Barang)*")

# Link Google Sheets (Pastikan ID ini benar)
SHEET_ID = "1L1C72W0C8heL5YLahlAliT3K_9gYkcfy9mCAk4rSFXY"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=10)
def load_data():
    # Mengambil semua sheet sekaligus
    return pd.read_excel(EXCEL_URL, sheet_name=None, engine='openpyxl')

try:
    semua_sheet = load_data()
    
    # --- SIDEBAR FILTER ---
    st.sidebar.header("🎛️ Menu Filter")
    bulan_terpilih = st.sidebar.selectbox("Pilih Bulan:", list(semua_sheet.keys()))
    df_raw = semua_sheet[bulan_terpilih]

    # --- 2. LOGIKA TANGGAL & OMSET (Tabel Atas) ---
    # Kita ambil 31 baris pertama untuk data harian
    df_harian = df_raw.iloc[1:33, [0, 1, 2, 3]].copy() 
    df_harian.columns = ['Tanggal', 'Omset', 'Ket_Harian', 'Pengeluaran']
    
    # Bersihkan data tanggal agar bisa masuk ke Slider
    df_harian['Tgl_Fix'] = pd.to_numeric(df_harian['Tanggal'], errors='coerce')
    df_harian = df_harian.dropna(subset=['Tgl_Fix'])
    
    min_t, max_t = int(df_harian['Tgl_Fix'].min()), int(df_harian['Tgl_Fix'].max())
    rentang = st.sidebar.slider("Pilih Rentang Tanggal:", min_t, max_t, (min_t, max_t))

    # Filter data berdasarkan slider
    df_filt = df_harian[(df_harian['Tgl_Fix'] >= rentang[0]) & (df_harian['Tgl_Fix'] <= rentang[1])].copy()
    df_filt['OMSET_RP'] = pd.to_numeric(df_filt['Omset'], errors='coerce').fillna(0)
    df_filt['Tanggal_Str'] = "Tgl " + df_filt['Tgl_Fix'].astype(int).astype(str)

    # --- 3. TAMPILAN GRAFIK OMSET ---
    st.subheader(f"📈 Grafik Omset Harian (Tgl {rentang[0]} - {rentang[1]})")
    if not df_filt.empty:
        st.line_chart(data=df_filt.set_index('Tanggal_Str')['OMSET_RP'])
    else:
        st.info("Tidak ada data omset untuk rentang ini.")

    st.markdown("---")

    # --- 4. TABEL RINCIAN BELANJA (LPG, KRESEK, TAHU, DLL) ---
    st.subheader(f"💸 Rincian Belanja Barang (LPG, Plastik, Tahu, dll)")
    
    # Mencari baris yang mengandung judul tabel pengeluaran
    target_row = None
    for r in range(len(df_raw)):
        # Mengecek kolom B atau C (indeks 1 atau 2)
        val = str(df_raw.iloc[r, 1]).upper()
        if "PENGELUARAN LAIN" in val or "RINCIAN BELANJA" in val:
            target_row = r
            break

    if target_row is not None:
        # Berdasarkan struktur: Nama barang di kolom B (1), Harga di kolom E (4)
        df_belanja = df_raw.iloc[target_row+2 : target_row+20, [1, 4]].copy() 
        df_belanja.columns = ['Nama Barang', 'Harga']
        
        # Bersihkan data: Hapus baris kosong dan konversi harga
        df_belanja = df_belanja.dropna(subset=['Nama Barang'])
        df_belanja['Harga'] = pd.to_numeric(df_belanja['Harga'], errors='coerce').fillna(0)
        
        # Hanya tampilkan barang yang ada harganya (biar rapi)
        df_belanja_view = df_belanja[df_belanja['Harga'] > 0]

        if not df_belanja_view.empty:
            # Format tampilan ke Rupiah
            df_belanja_view['Harga'] = df_belanja_view['Harga'].apply(lambda x: f"Rp {int(x):,}")
            st.table(df_belanja_view.reset_index(drop=True))
        else:
            st.info("Belum ada rincian belanja (elpiji/tahu) yang diisi di spreadsheet.")
    else:
        st.warning("Tabel 'Pengeluaran Lain' tidak ditemukan di sheet ini.")

    st.markdown("---")

    # --- 5. TABEL LAPORAN UANG SETOR ---
    st.subheader("💰 Laporan Uang Setor (Omset - Pengeluaran)")
    df_filt['PENGELUARAN_RP'] = pd.to_numeric(df_filt['Pengeluaran'], errors='coerce').fillna(0)
    df_filt['SETOR'] = df_filt['OMSET_RP'] - df_filt['PENGELUARAN_RP']
    
    tabel_setor = df_filt[['Tgl_Fix', 'OMSET_RP', 'PENGELUARAN_RP', 'SETOR']].copy()
    tabel_setor.columns = ['Tgl', 'Omset (Rp)', 'Total Belanja', 'Uang Setor']
    
    # Format angka agar mudah dibaca
    for col in ['Omset (Rp)', 'Total Belanja', 'Uang Setor']:
        tabel_setor[col] = tabel_setor[col].apply(lambda x: f"Rp {int(x):,}")
    
    st.dataframe(tabel_setor.reset_index(drop=True), use_container_width=True)

    # --- 6. TABEL STOK BARANG ---
    st.markdown("---")
    st.subheader("📦 Laporan Stok (Bawa vs Laku)")
    
    idx_stok = None
    for r in range(len(df_raw)):
        if "STOK DI BAWA" in str(df_raw.iloc[r, :]).upper():
            idx_stok = r
            break
            
    if idx_stok is not None:
        # Ambil kolom Menu (1), Bawa (3), Sisa (5), Laku (6)
        df_s = df_raw.iloc[idx_stok+2:idx_stok+12, [1, 3, 5, 6]].copy()
        df_s.columns = ["Menu", "Bawa", "Sisa", "Laku"]
        df_s = df_s.dropna(subset=["Menu"])
        st.dataframe(df_s.reset_index(drop=True), use_container_width=True)
    else:
        st.info("Tabel stok belum tersedia di sheet ini.")

except Exception as e:
    st.error(f"Terjadi kendala pembacaan data: {e}")
    st.info("Tips: Pastikan nama kolom atau struktur tabel di spreadsheet tidak berubah.")
