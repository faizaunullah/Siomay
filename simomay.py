import streamlit as st
import pandas as pd

# Konfigurasi halaman agar lebih lebar
st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide")

st.title("🥟 Dashboard Lengkap Siomay Jawara Malang")
st.markdown("*(Data otomatis ditarik dari Google Sheets Baru. Gunakan menu di sebelah kiri untuk memfilter data)*")

# LINK BARU YANG KAMU BERIKAN
SHEET_ID = "1L1C72W0C8heL5YLahlAliT3K_9gYkcfy9mCAk4rSFXY"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=15) # Refresh otomatis setiap 15 detik
def load_data():
    # Membaca seluruh tab/sheet menggunakan engine openpyxl
    return pd.read_excel(EXCEL_URL, sheet_name=None, engine='openpyxl')

try:
    semua_sheet = load_data()
    
    # --- MENU FILTER DI SAMPING (SIDEBAR) ---
    st.sidebar.header("🎛️ Filter Data Laporan")
    daftar_bulan = list(semua_sheet.keys())
    bulan_terpilih = st.sidebar.selectbox("Pilih Bulan:", daftar_bulan)
    
    df_raw = semua_sheet[bulan_terpilih]
    
    # --- 1. RINGKASAN KEUANGAN BULANAN ---
    # Mengambil total dari baris ke-2 (index 1) di Excel
    total_omset_sebulan = pd.to_numeric(df_raw.iloc[1, 1], errors='coerce')
    total_produksi = pd.to_numeric(df_raw.iloc[1, 2], errors='coerce') 
    total_operasional = pd.to_numeric(df_raw.iloc[1, 3], errors='coerce') # Termasuk LPG/Belanja Lain
    
    st.subheader(f"💰 Ringkasan Keuangan ({bulan_terpilih})")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Omset 1 Bulan", f"Rp {total_omset_sebulan:,.0f}".replace(',', '.'))
    col2.metric("Total Biaya Produksi", f"Rp {total_produksi:,.0f}".replace(',', '.'))
    col3.metric("Total Pengeluaran Lain/LPG", f"Rp {total_operasional:,.0f}".replace(',', '.'))
    
    st.markdown("---")
    
    # --- 2. DATA HARIAN (GRAFIK & TABEL) ---
    df_harian = df_raw.head(35).copy()
    if ' TANGGAL' in df_harian.columns and 'OMSET' in df_harian.columns:
        df_harian = df_harian.dropna(subset=[' TANGGAL'])
        df_harian = df_harian[df_harian[' TANGGAL'].astype(str).str.isnumeric() == True]
        
        df_harian['OMSET'] = pd.to_numeric(df_harian['OMSET'], errors='coerce').fillna(0)
        df_harian['Pengeluaran_Op'] = pd.to_numeric(df_harian['Unnamed: 3'], errors='coerce').fillna(0)
        df_harian['Rincian'] = df_harian['RINCIAN'].fillna("-")
        
        df_bersih = df_harian[df_harian['OMSET'] > 0].copy()
        
        if not df_bersih.empty:
            df_bersih['Tgl_Angka'] = df_bersih[' TANGGAL'].astype(int)
            min_tgl = int(df_bersih['Tgl_Angka'].min())
            max_tgl = int(df_bersih['Tgl_Angka'].max())
            
            rentang_tgl = st.sidebar.slider("Pilih Rentang Tanggal:", min_tgl, max_tgl, (min_tgl, max_tgl))
            
            df_filter = df_bersih[(df_bersih['Tgl_Angka'] >= rentang_tgl[0]) & (df_bersih['Tgl_Angka'] <= rentang_tgl[1])].copy()
            df_filter['Tanggal_Tampil'] = "Tgl " + df_filter['Tgl_Angka'].astype(str)
            
            # Grafik Omset
            st.subheader(f"📈 Grafik Omset Harian (Tgl {rentang_tgl[0]} - {rentang_tgl[1]})")
            st.line_chart(data=df_filter.set_index('Tanggal_Tampil')['OMSET'])
            
            # Tabel Harian Lengkap
            st.subheader("📝 Tabel Pemasukan & Pengeluaran Harian")
            tabel_tampil = df_filter[['Tanggal_Tampil', 'OMSET', 'Pengeluaran_Op', 'Rincian']].rename(
                columns={'Pengeluaran_Op': 'Pengeluaran Lain (Rp)', 'Rincian': 'Keterangan/LPG'}
            )
            st.dataframe(tabel_tampil, use_container_width=True)
            
        else:
            st.info(f"Belum ada data omset harian untuk bulan {bulan_terpilih}.")
    
    st.markdown("---")
    
    # --- 3. LAPORAN STOK (BAGIAN BAWAH EXCEL) ---
    st.subheader(f"📦 Laporan Stok Bawa & Sisa ({bulan_terpilih})")
    
    # Mencari baris "STOK DI BAWA" secara otomatis
    pencarian_stok = df_raw[df_raw.astype(str).apply(lambda x: x.str.contains('STOK DI BAWA', case=False, na=False)).any(axis=1)].index
    
    if len(pencarian_stok) > 0:
        baris_mulai = pencarian_stok[0]
        # Mengambil kolom Item, Stok Bawa, Sisa, dan Laku
        df_stok = df_raw.iloc[baris_mulai+2 : baris_mulai+12, [1, 3, 5, 6]].copy() 
        df_stok.columns = ["Nama Menu", "Stok Dibawa (Pcs)", "Sisa Stok (Pcs)", "Laku Terjual (Pcs)"]
        
        df_stok = df_stok.dropna(subset=['Nama Menu'])
        df_stok = df_stok[df_stok['Nama Menu'].astype(str).str.strip() != ""]
        
        if not df_stok.empty:
            st.dataframe(df_stok, use_container_width=True)
        else:
            st.info("Data tabel stok masih kosong.")
    else:
        st.warning("Tabel stok tidak ditemukan. Pastikan format tabel bawah sama dengan template sebelumnya.")

except Exception as e:
    st.error(f"Gagal membaca data Google Sheets. Cek apakah izin 'Anyone with the link' sudah aktif. Error: {e}")
