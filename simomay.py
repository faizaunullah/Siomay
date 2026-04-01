import streamlit as st
import pandas as pd

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide", page_icon="🥟")

st.title("🥟 Dashboard Super Lengkap Siomay Jawara")
st.markdown("---")

# Link Google Sheets (Export as XLSX agar mudah dibaca Pandas)
SHEET_ID = "1L1C72W0C8heL5YLahlAliT3K_9gYkcfy9mCAk4rSFXY"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=10)
def load_data():
    # Membaca seluruh sheet yang ada di file
    return pd.read_excel(EXCEL_URL, sheet_name=None, engine='openpyxl')

try:
    semua_sheet = load_data()
    
    # --- SIDEBAR FILTER ---
    st.sidebar.header("🎛️ Menu Filter")
    # Memilih bulan berdasarkan nama Sheet
    bulan_list = [s for s in semua_sheet.keys() if "Sheet" not in s] # Filter nama sheet yg valid
    bulan_terpilih = st.sidebar.selectbox("Pilih Bulan:", bulan_list)
    df_raw = semua_sheet[bulan_terpilih]

    # --- 2. PENGOLAHAN DATA OMSET (Tabel Atas) ---
    # Mengambil data harian (biasanya baris 2 sampai 32)
    df_harian = df_raw.iloc[1:33, [0, 1, 3]].copy() # Kolom Tgl, Omset, Total Pengeluaran
    df_harian.columns = ['Tanggal', 'Omset', 'Pengeluaran']
    
    # Bersihkan Tanggal
    df_harian['Tgl_Int'] = pd.to_numeric(df_harian['Tanggal'], errors='coerce')
    df_harian = df_harian.dropna(subset=['Tgl_Int'])
    
    # Slider Tanggal di Sidebar
    min_t = int(df_harian['Tgl_Int'].min())
    max_t = int(df_harian['Tgl_Int'].max())
    rentang = st.sidebar.slider("Pilih Rentang Tanggal:", min_t, max_t, (min_t, max_t))

    # Filter data berdasarkan slider
    df_filt = df_harian[(df_harian['Tgl_Int'] >= rentang[0]) & (df_harian['Tgl_Int'] <= rentang[1])].copy()
    df_filt['OMSET_VAL'] = pd.to_numeric(df_filt['Omset'], errors='coerce').fillna(0)
    df_filt['Tgl_Str'] = "Tgl " + df_filt['Tgl_Int'].astype(int).astype(str)

    # --- 3. GRAFIK OMSET ---
    st.subheader(f"📈 Tren Omset Harian ({bulan_terpilih})")
    if not df_filt.empty:
        st.line_chart(data=df_filt.set_index('Tgl_Str')['OMSET_VAL'])
    else:
        st.info("Data tidak tersedia untuk grafik.")

    # --- 4. TABEL RINCIAN BELANJA (LPG, TAHU, KRESEK) ---
    st.markdown("---")
    st.subheader("💸 Rincian Belanja Barang (LPG, Plastik, Tahu, dll)")
    
    # Cari baris judul "PENGELUARAN LAIN" secara dinamis
    row_lain = None
    for r in range(len(df_raw)):
        row_str = " ".join([str(x).upper() for x in df_raw.iloc[r, :].values])
        if "PENGELUARAN LAIN" in row_str:
            row_lain = r
            break
    
    if row_lain is not None:
        # Ambil area di bawah judul tersebut
        df_temp = df_raw.iloc[row_lain+2 : row_lain+20, :].copy()
        
        belanja_list = []
        for _, row in df_temp.iterrows():
            nama_item = row.iloc[1] # Kolom B (Index 1)
            # Cek harga di Kolom E atau F (Index 4 atau 5) karena sering merged
            harga_item = row.iloc[4] if pd.notna(row.iloc[4]) and row.iloc[4] != 0 else row.iloc[5]
            
            # Validasi: Nama harus teks (bukan angka/No) dan Harga harus ada
            if pd.notna(nama_item) and not str(nama_item).isdigit():
                harga_clean = pd.to_numeric(harga_item, errors='coerce')
                if harga_clean > 0:
                    belanja_list.append({"Barang": nama_item, "Biaya": harga_clean})
        
        if belanja_list:
            df_belanja_final = pd.DataFrame(belanja_list)
            # Format Rupiah untuk tampilan
            df_belanja_disp = df_belanja_final.copy()
            df_belanja_disp['Biaya'] = df_belanja_disp['Biaya'].apply(lambda x: f"Rp {int(x):,}")
            st.table(df_belanja_disp)
        else:
            st.warning("Data rincian belanja (elpiji/tahu) kosong di sheet ini.")
    else:
        st.error("Teks 'PENGELUARAN LAIN-LAIN' tidak ditemukan di spreadsheet.")

    # --- 5. TABEL UANG SETOR ---
    st.markdown("---")
    st.subheader("💰 Laporan Uang Setor")
    
    df_filt['PENGELUARAN_VAL'] = pd.to_numeric(df_filt['Pengeluaran'], errors='coerce').fillna(0)
    df_filt['SETOR_VAL'] = df_filt['OMSET_VAL'] - df_filt['PENGELUARAN_VAL']
    
    tabel_setor = df_filt[['Tgl_Int', 'OMSET_VAL', 'PENGELUARAN_VAL', 'SETOR_VAL']].copy()
    tabel_setor.columns = ['Tgl', 'Omset', 'Total Belanja', 'Uang Setor']
    
    # Format ribuan agar rapi
    for col in ['Omset', 'Total Belanja', 'Uang Setor']:
        tabel_setor[col] = tabel_setor[col].apply(lambda x: f"Rp {int(x):,}")
    
    st.dataframe(tabel_setor.reset_index(drop=True), use_container_width=True)

    # --- 6. TABEL STOK BARANG ---
    st.markdown("---")
    st.subheader("📦 Laporan Stok (Bawa vs Laku)")
    
    row_stok = None
    for r in range(len(df_raw)):
        if "STOK DI BAWA" in str(df_raw.iloc[r, :].values).upper():
            row_stok = r
            break
            
    if row_stok is not None:
        # Mengambil kolom Menu, Bawa, Sisa, Laku
        df_s = df_raw.iloc[row_stok+2:row_stok+12, [1, 3, 5, 6]].copy()
        df_s.columns = ["Menu", "Bawa", "Sisa", "Laku"]
        df_s = df_s.dropna(subset=["Menu"])
        st.dataframe(df_s.reset_index(drop=True), use_container_width=True)
    else:
        st.info("Tabel stok tidak ditemukan.")

except Exception as e:
    st.error(f"Waduh, ada masalah teknis: {e}")
    st.info("Saran: Cek apakah nama Sheet sudah benar dan file Google Sheets sudah di-share 'Anyone with the link'.")
