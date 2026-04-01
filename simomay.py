import streamlit as st
import pandas as pd

# Konfigurasi halaman agar lebih lebar
st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide")

st.title("🥟 Dashboard Penjualan Siomay Jawara Malang")
st.markdown("*(Data otomatis ditarik dari Google Sheets. Gunakan menu di sebelah kiri untuk memfilter data)*")

# Link Google Sheets milikmu
SHEET_ID = "1U8Wu-iBqii4Mj_wPXmaX6722phs-LywC"
# URL diubah ke format .xlsx agar bisa membaca SEMUA TAB (Januari, Februari, dll)
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=15) # Refresh otomatis setiap 15 detik
def load_data():
    # Membaca seluruh tab/sheet yang ada di Google Sheets menggunakan openpyxl
    xls = pd.read_excel(EXCEL_URL, sheet_name=None, engine='openpyxl')
    return xls

try:
    semua_sheet = load_data()
    
    # --- MEMBUAT MENU FILTER DI SAMPING (SIDEBAR) ---
    st.sidebar.header("🎛️ Filter Data Laporan")
    
    # 1. Pilih Bulan (Berdasarkan nama Tab di Google Sheets)
    daftar_bulan = list(semua_sheet.keys())
    bulan_terpilih = st.sidebar.selectbox("Pilih Bulan:", daftar_bulan)
    
    # Ambil data hanya dari bulan yang dipilih
    df = semua_sheet[bulan_terpilih]
    
    # Mengambil maksimal 35 baris pertama (menghindari tabel stok di bawahnya)
    df = df.head(35)
    
    # Cek apakah kolom yang dibutuhkan tersedia
    if ' TANGGAL' in df.columns and 'OMSET' in df.columns:
        # Bersihkan data
        df_sub = df[[' TANGGAL', 'OMSET']].copy()
        df_sub = df_sub.dropna(subset=[' TANGGAL'])
        df_sub = df_sub[df_sub[' TANGGAL'].astype(str).str.isnumeric() == True]
        df_sub['OMSET'] = pd.to_numeric(df_sub['OMSET'], errors='coerce').fillna(0)
        
        # Saring data yang omsetnya lebih dari 0
        df_bersih = df_sub[df_sub['OMSET'] > 0].copy()
        
        if not df_bersih.empty:
            # Jadikan angka agar bisa dibuat slider (geser-geser tanggal)
            df_bersih['Tgl_Angka'] = df_bersih[' TANGGAL'].astype(int)
            min_tgl = int(df_bersih['Tgl_Angka'].min())
            max_tgl = int(df_bersih['Tgl_Angka'].max())
            
            # 2. Filter Tanggal menggunakan Slider
            rentang_tgl = st.sidebar.slider(
                "Pilih Rentang Tanggal:",
                min_value=min_tgl,
                max_value=max_tgl,
                value=(min_tgl, max_tgl) # Defaultnya memilih semua tanggal yang tersedia
            )
            
            # Potong data sesuai rentang tanggal yang digeser di slider
            df_filter = df_bersih[
                (df_bersih['Tgl_Angka'] >= rentang_tgl[0]) & 
                (df_bersih['Tgl_Angka'] <= rentang_tgl[1])
            ].copy()
            
            df_filter['Tanggal_Tampil'] = "Tgl " + df_filter['Tgl_Angka'].astype(str)
            
            if not df_filter.empty:
                total_omset = df_filter['OMSET'].sum()
                max_omset = df_filter['OMSET'].max()
                
                # --- TAMPILAN DASHBOARD UTAMA ---
                st.subheader(f"📊 Laporan: {rentang_tgl[0]} s/d {rentang_tgl[1]} {bulan_terpilih}")
                
                col1, col2 = st.columns(2)
                col1.metric("Total Pendapatan", f"Rp {total_omset:,.0f}".replace(',', '.'))
                col2.metric("Penjualan Tertinggi", f"Rp {max_omset:,.0f}".replace(',', '.'))
                
                # Grafik
                st.line_chart(data=df_filter.set_index('Tanggal_Tampil')['OMSET'])
                
                # Tabel
                st.subheader("Tabel Rincian")
                st.dataframe(df_filter[['Tanggal_Tampil', 'OMSET']], use_container_width=True)
                
                # Tombol Download
                csv = df_filter[['Tanggal_Tampil', 'OMSET']].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Download Laporan {bulan_terpilih} (CSV)",
                    data=csv,
                    file_name=f"Laporan_{bulan_terpilih}_{rentang_tgl[0]}_{rentang_tgl[1]}.csv",
                    mime="text/csv",
                )
            else:
                st.warning("Tidak ada data penjualan pada rentang tanggal tersebut.")
        else:
            st.info(f"Belum ada data omset yang diisi untuk bulan {bulan_terpilih}.")
    else:
        st.error(f"Format tabel di sheet '{bulan_terpilih}' tidak sesuai template.")

except Exception as e:
    st.error(f"Gagal membaca data. Pastikan file terhubung dan diset 'Siapa saja yang memiliki link'. Error: {e}")
