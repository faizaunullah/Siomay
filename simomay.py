import streamlit as st
import pandas as pd

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide")

st.title("🥟 Dashboard Super Lengkap Siomay Jawara")
st.markdown("*(Grafik Omset, Rincian Belanja, Uang Setor, & Stok Barang)*")

# Link Google Sheets
SHEET_ID = "1L1C72W0C8heL5YLahlAliT3K_9gYkcfy9mCAk4rSFXY"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=10)
def load_data():
    # Menggunakan pd.read_excel untuk mengambil semua sheet
    return pd.read_excel(EXCEL_URL, sheet_name=None, engine='openpyxl')

try:
    semua_sheet = load_data()
    
    # --- SIDEBAR FILTER ---
    st.sidebar.header("🎛️ Menu Filter")
    bulan_terpilih = st.sidebar.selectbox("Pilih Bulan:", list(semua_sheet.keys()))
    df_raw = semua_sheet[bulan_terpilih]

    # --- 2. LOGIKA TANGGAL (OMSET) ---
    # Kita ambil 31 baris pertama biasanya untuk omset harian
    df_harian = df_raw.iloc[1:33, [0, 1, 2, 3]].copy() 
    df_harian.columns = ['Tanggal', 'Omset', 'Keterangan', 'Pengeluaran']
    
    # Bersihkan data tanggal
    df_harian['Tgl_Fix'] = pd.to_numeric(df_harian['Tanggal'], errors='coerce')
    df_harian = df_harian.dropna(subset=['Tgl_Fix'])
    
    min_t, max_t = int(df_harian['Tgl_Fix'].min()), int(df_harian['Tgl_Fix'].max())
    rentang = st.sidebar.slider("Pilih Rentang Tanggal:", min_t, max_t, (min_t, max_t))

    # Filter berdasarkan slider
    df_filt = df_harian[(df_harian['Tgl_Fix'] >= rentang[0]) & (df_harian['Tgl_Fix'] <= rentang[1])].copy()
    df_filt['OMSET_RP'] = pd.to_numeric(df_filt['Omset'], errors='coerce').fillna(0)
    df_filt['Tanggal_Str'] = "Tgl " + df_filt['Tgl_Fix'].astype(int).astype(str)

    # --- 3. TAMPILAN GRAFIK OMSET ---
    st.subheader(f"📈 Grafik Omset Harian (Tgl {rentang[0]} - {rentang[1]})")
    if not df_filt.empty:
        st.line_chart(data=df_filt.set_index('Tanggal_Str')['OMSET_RP'])
    else:
        st.info("Tidak ada data untuk menampilkan grafik.")

    st.markdown("---")

    # --- 4. TABEL RINCIAN BELANJA (LPG, KRESEK, TAHU, DLL) ---
    # Logika Baru: Mencari tabel "PENGELUARAN LAIN-LAIN" secara dinamis
    st.subheader(f"💸 Rincian Belanja Barang (LPG, Plastik, Tahu, dll)")
    
    # --- 4. TABEL RINCIAN BELANJA (VERSI FIX) ---
    st.subheader(f"💸 Rincian Belanja Barang (LPG, Plastik, Tahu, dll)")
    
    # Cari baris yang mengandung "PENGELUARAN LAIN"
    target_row = None
    for r in range(len(df_raw)):
        if "PENGELUARAN LAIN" in str(df_raw.iloc[r, 1]).upper() or "PENGELUARAN LAIN" in str(df_raw.iloc[r, 2]).upper():
            target_row = r
            break

    if target_row is not None:
        # Berdasarkan gambar, data mulai 2 baris di bawah judul
        # Kita ambil Kolom B (Barang) dan Kolom E atau F (Harga)
        # Kita gunakan indeks kolom manual sesuai gambar spreadsheetmu
        df_belanja = df_raw.iloc[target_row+2 : target_row+15, [1, 4]].copy() 
        df_belanja.columns = ['Nama Barang', 'Harga']
        
        # Bersihkan data: Hapus baris kosong dan konversi harga ke angka
        df_belanja = df_belanja.dropna(subset=['Nama Barang'])
        df_belanja['Harga'] = pd.to_numeric(df_belanja['Harga'], errors='coerce').fillna(0)
        
        # Hanya tampilkan yang harganya > 0 (supaya baris kosong tidak muncul)
        df_belanja_view = df_belanja[df_belanja['Harga'] > 0]

        if not df_belanja_view.empty:
            # Format tampilan Rupiah
            df_belanja_view['Harga'] = df_belanja_view['Harga'].map(lambda x: f"Rp {x:,.0f}")
            st.table(df_belanja_view.reset_index(drop=True))
        else:
            st.info("Belum ada rincian belanja yang tercatat.")
    else:
        st.warning("Tabel 'Pengeluaran Lain' tidak ditemukan. Pastikan teksnya sesuai di Spreadsheet.")
        
        # Bersihkan data
        df_belanja['Tgl'] = pd.to_numeric(df_belanja['Tgl'], errors='coerce')
        df_belanja['Biaya'] = pd.to_numeric(df_belanja['Biaya'], errors='coerce').fillna(0)
        df_belanja = df_belanja.dropna(subset=['Barang'])
        
        # Filter berdasarkan slider tanggal
        df_belanja_view = df_belanja[(df_belanja['Tgl'] >= rentang[0]) & (df_belanja['Tgl'] <= rentang[1])]
        
        if not df_belanja_view.empty:
            # Format angka biar bagus
            df_belanja_view['Biaya'] = df_belanja_view['Biaya'].map(lambda x: f"Rp {x:,.0f}")
            st.table(df_belanja_view.reset_index(drop=True))
        else:
            st.warning("Data rincian belanja tidak ditemukan untuk rentang tanggal ini.")
    else:
        st.error("Tabel 'Pengeluaran Lain-lain' tidak terdeteksi di spreadsheet.")

    st.markdown("---")

    # --- 5. TABEL UANG SETOR ---
    st.subheader("💰 Laporan Uang Setor")
    df_filt['PENGELUARAN_RP'] = pd.to_numeric(df_filt['Pengeluaran'], errors='coerce').fillna(0)
    df_filt['SETOR'] = df_filt['OMSET_RP'] - df_filt['PENGELUARAN_RP']
    
    tabel_setor = df_filt[['Tgl_Fix', 'OMSET_RP', 'PENGELUARAN_RP', 'SETOR']].copy()
    tabel_setor.columns = ['Tgl', 'Omset (Rp)', 'Total Belanja', 'Uang Setor']
    
    st.dataframe(tabel_setor.reset_index(drop=True), use_container_width=True)

except Exception as e:
    st.error(f"Terjadi kendala pembacaan data: {e}")
    st.info("Pastikan struktur Sheet tidak berubah drastis.")
