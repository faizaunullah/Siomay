import streamlit as st
import pandas as pd

# Konfigurasi halaman agar lebih lebar
st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide")

st.title("🥟 Dashboard Lengkap Siomay Jawara Malang")
st.markdown("*(Data otomatis ditarik dari Google Sheets Baru. Gunakan menu di sebelah kiri untuk memfilter data)*")

SHEET_ID = "1L1C72W0C8heL5YLahlAliT3K_9gYkcfy9mCAk4rSFXY"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=15)
def load_data():
    return pd.read_excel(EXCEL_URL, sheet_name=None, engine='openpyxl')

try:
    semua_sheet = load_data()
    
    # --- MENU FILTER DI SAMPING (SIDEBAR) ---
    st.sidebar.header("🎛️ Filter Data Laporan")
    daftar_bulan = list(semua_sheet.keys())
    bulan_terpilih = st.sidebar.selectbox("Pilih Bulan:", daftar_bulan)
    
    df_raw = semua_sheet[bulan_terpilih]
    
    # --- 1. RINGKASAN KEUANGAN BULANAN ---
    total_omset_sebulan = pd.to_numeric(df_raw.iloc[1, 1], errors='coerce')
    total_produksi = pd.to_numeric(df_raw.iloc[1, 2], errors='coerce') 
    total_operasional = pd.to_numeric(df_raw.iloc[1, 3], errors='coerce')
    
    st.subheader(f"💰 Ringkasan Keuangan ({bulan_terpilih})")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Omset 1 Bulan", f"Rp {total_omset_sebulan:,.0f}".replace(',', '.'))
    col2.metric("Total Biaya Produksi", f"Rp {total_produksi:,.0f}".replace(',', '.'))
    col3.metric("Total Pengeluaran Lain", f"Rp {total_operasional:,.0f}".replace(',', '.'))
    
    st.markdown("---")
    
    # --- 2. DATA HARIAN (PERSIAPAN) ---
    df_harian = df_raw.head(35).copy()
    if ' TANGGAL' in df_harian.columns and 'OMSET' in df_harian.columns:
        # Bersihkan data tanggal
        df_harian = df_harian.dropna(subset=[' TANGGAL'])
        df_harian = df_harian[df_harian[' TANGGAL'].astype(str).str.isnumeric() == True]
        df_harian['Tgl_Angka'] = df_harian[' TANGGAL'].astype(int)
        
        # Bersihkan data angka & teks
        df_harian['OMSET'] = pd.to_numeric(df_harian['OMSET'], errors='coerce').fillna(0)
        df_harian['Pengeluaran_Op'] = pd.to_numeric(df_harian['Unnamed: 3'], errors='coerce').fillna(0)
        df_harian['Rincian'] = df_harian['RINCIAN'].fillna("-")
        
        # Buat Slider Tanggal
        min_tgl = int(df_harian['Tgl_Angka'].min())
        max_tgl = int(df_harian['Tgl_Angka'].max())
        rentang_tgl = st.sidebar.slider("Pilih Rentang Tanggal:", min_tgl, max_tgl, (min_tgl, max_tgl))
        
        # Filter data berdasarkan slider
        df_filter = df_harian[(df_harian['Tgl_Angka'] >= rentang_tgl[0]) & (df_harian['Tgl_Angka'] <= rentang_tgl[1])].copy()
        df_filter['Tanggal_Tampil'] = "Tgl " + df_filter['Tgl_Angka'].astype(str)
        
        # --- 2A. BAGIAN PEMASUKAN (OMSET) ---
        st.subheader(f"📈 Laporan Pemasukan (Tgl {rentang_tgl[0]} - {rentang_tgl[1]})")
        df_omset = df_filter[df_filter['OMSET'] > 0].copy()
        
        if not df_omset.empty:
            st.line_chart(data=df_omset.set_index('Tanggal_Tampil')['OMSET'])
            st.dataframe(df_omset[['Tanggal_Tampil', 'OMSET']].rename(columns={'Tanggal_Tampil': 'Tanggal', 'OMSET': 'Omset (Rp)'}), use_container_width=True)
        else:
            st.info("Belum ada pemasukan/omset di rentang tanggal ini.")

        # --- 2B. BAGIAN PENGELUARAN KHUSUS ---
        st.subheader(f"💸 Rincian Pengeluaran Lain / Operasional")
        df_pengeluaran = df_filter[df_filter['Pengeluaran_Op'] > 0].copy()
        
        if not df_pengeluaran.empty:
            tabel_pengeluaran = df_pengeluaran[['Tanggal_Tampil', 'Pengeluaran_Op', 'Rincian']].rename(
                columns={'Tanggal_Tampil': 'Tanggal', 'Pengeluaran_Op': 'Nominal (Rp)', 'Rincian': 'Keterangan Penggunaan'}
            )
            st.dataframe(tabel_pengeluaran, use_container_width=True)
            
            # Hitung total pengeluaran di tabel yang tampil
            total_pengeluaran_tabel = df_pengeluaran['Pengeluaran_Op'].sum()
            st.warning(f"**Total Penggunaan Uang (Pengeluaran Lain): Rp {total_pengeluaran_tabel:,.0f}**".replace(',', '.'))
        else:
            st.success("✨ Tidak ada pengeluaran operasional lain pada rentang tanggal ini.")
            
    else:
        st.error(f"Format tabel harian untuk bulan {bulan_terpilih} tidak sesuai.")
    
    st.markdown("---")
    
    # --- 3. LAPORAN STOK (BAGIAN BAWAH EXCEL) ---
    st.subheader(f"📦 Laporan Stok Bawa & Sisa ({bulan_terpilih})")
    pencarian_stok = df_raw[df_raw.astype(str).apply(lambda x: x.str.contains('STOK DI BAWA', case=False, na=False)).any(axis=1)].index
    
    if len(pencarian_stok) > 0:
        baris_mulai = pencarian_stok[0]
        df_stok = df_raw.iloc[baris_mulai+2 : baris_mulai+12, [1, 3, 5, 6]].copy() 
        df_stok.columns = ["Nama Menu", "Stok Dibawa (Pcs)", "Sisa Stok (Pcs)", "Laku Terjual (Pcs)"]
        
        df_stok = df_stok.dropna(subset=['Nama Menu'])
        df_stok = df_stok[df_stok['Nama Menu'].astype(str).str.strip() != ""]
        
        if not df_stok.empty:
            st.dataframe(df_stok, use_container_width=True)
        else:
            st.info("Data tabel stok masih kosong.")
    else:
        st.warning("Tabel stok tidak ditemukan.")

except Exception as e:
    st.error(f"Gagal membaca data Google Sheets. Cek apakah izin 'Anyone with the link' sudah aktif. Error: {e}")
