import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Siomay Jawara", layout="wide")

st.title("🥟 Dashboard Ultimate Siomay Jawara")
st.markdown("*(Versi AI Auto-Radar: Otomatis melacak tabel yang geser di bulan baru)*")

# Link Spreadsheet Terbarumu
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

    # ---------------------------------------------------------
    # 1. RADAR PENCARI TABEL UTAMA (OMSET)
    # ---------------------------------------------------------
    r_omset, c_omset = -1, -1
    
    # Cek baris nama kolom dulu
    for i, col in enumerate(df_raw.columns):
        if "OMSET" in str(col).upper():
            r_omset = -1
            c_omset = i
            break
            
    # Jika tidak ketemu, sisir ke bawah (Cari jika judulnya turun ke bawah)
    if r_omset == -1:
        for r in range(20):
            for c in range(len(df_raw.columns)):
                if "OMSET" in str(df_raw.iloc[r, c]).upper():
                    r_omset = r
                    c_omset = c
                    break
            if r_omset != -1: break

    if c_omset != -1:
        # Menarik data: Tanggal(kiri), Omset, Produksi(kanan), Belanja(kanannya lagi)
        c_tgl = max(0, c_omset - 1)
        c_prod = c_omset + 1 if c_omset + 1 < len(df_raw.columns) else c_omset
        c_op = c_omset + 2 if c_omset + 2 < len(df_raw.columns) else c_omset
        
        baris_mulai = r_omset + 1 if r_omset != -1 else 0
        df_main = df_raw.iloc[baris_mulai:baris_mulai+35, [c_tgl, c_omset, c_prod, c_op]].copy()
        df_main.columns = ['Tanggal', 'Omset', 'Biaya Produksi', 'Belanja Operasional']
        
        # Bersihkan data huruf/kosong
        df_main['Tanggal'] = pd.to_numeric(df_main['Tanggal'], errors='coerce')
        df_main = df_main.dropna(subset=['Tanggal'])
        df_main['Tanggal'] = df_main['Tanggal'].astype(int)
        
        for col in ['Omset', 'Biaya Produksi', 'Belanja Operasional']:
            df_main[col] = pd.to_numeric(df_main[col], errors='coerce').fillna(0)
            
        # Hitung Uang Setor Bersih
        df_main['Uang Setor'] = df_main['Omset'] - (df_main['Biaya Produksi'] + df_main['Belanja Operasional'])
        
        min_t, max_t = int(df_main['Tanggal'].min()), int(df_main['Tanggal'].max())
        rentang = st.sidebar.slider("Pilih Rentang Tanggal:", min_t, max_t, (min_t, max_t))
        df_main_filter = df_main[(df_main['Tanggal'] >= rentang[0]) & (df_main['Tanggal'] <= rentang[1])]
    else:
        st.error(f"Gagal menemukan kata 'OMSET' di bulan {bulan_terpilih}. Cek apakah ada di Excel.")
        st.stop()

    # ---------------------------------------------------------
    # 2. RADAR PENCARI DAFTAR BELANJA (LPG, KRESEK)
    # ---------------------------------------------------------
    semua_rincian = []
    kolom_rincian_ditemukan = []
    kata_kunci = ["KETERANGAN", "BARANG", "ITEM", "RINCIAN", "PENGELUARAN LAIN"]
    
    for r in range(30):
        for c in range(1, len(df_raw.columns) - 1): 
            val = str(df_raw.iloc[r, c]).strip().upper()
            
            # Jika ada kata kunci di dalam sel itu
            if any(k in val for k in kata_kunci) and c not in kolom_rincian_ditemukan:
                # PASTI BUKAN rincian tabel utama (Jauhkan dari kolom Omset)
                if abs(c - c_omset) <= 3:
                    continue 
                    
                kolom_rincian_ditemukan.append(c)
                
                # Baca 100 baris ke bawahnya (Tgl | Keterangan | Nominal)
                df_temp = df_raw.iloc[r+1:150, [c-1, c, c+1]].copy()
                df_temp.columns = ['Tanggal', 'Barang Dibeli', 'Nominal']
                df_temp = df_temp.dropna(subset=['Barang Dibeli'])
                
                # Saring kata-kata nyasar
                df_temp['Barang Dibeli'] = df_temp['Barang Dibeli'].astype(str).str.strip()
                kata_buang = ['', 'NAN', 'NONE', 'TANGGAL', 'NOMINAL', 'HARGA'] + kata_kunci
                df_temp = df_temp[~df_temp['Barang Dibeli'].str.upper().isin(kata_buang)]
                
                df_temp['Tanggal'] = pd.to_numeric(df_temp['Tanggal'], errors='coerce')
                df_temp['Nominal'] = pd.to_numeric(df_temp['Nominal'], errors='coerce').fillna(0)
                df_temp = df_temp.dropna(subset=['Tanggal'])
                
                if not df_temp.empty:
                    semua_rincian.append(df_temp)

    if semua_rincian:
        df_rincian_gabung = pd.concat(semua_rincian, ignore_index=True)
        df_rincian_gabung = df_rincian_gabung[(df_rincian_gabung['Tanggal'] >= rentang[0]) & (df_rincian_gabung['Tanggal'] <= rentang[1])]
        df_rincian_gabung = df_rincian_gabung[df_rincian_gabung['Nominal'] > 0]
    else:
        df_rincian_gabung = pd.DataFrame()

    # ---------------------------------------------------------
    # 3. TAMPILAN WEB (RINGKAS & RAPI)
    # ---------------------------------------------------------
    st.subheader(f"💵 Ringkasan Keuangan (Tgl {rentang[0]} - {rentang[1]})")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Omset", f"Rp {df_main_filter['Omset'].sum():,.0f}".replace(',', '.'))
    c2.metric("Biaya Produksi", f"Rp {df_main_filter['Biaya Produksi'].sum():,.0f}".replace(',', '.'))
    c3.metric("Belanja Operasional", f"Rp {df_main_filter['Belanja Operasional'].sum():,.0f}".replace(',', '.'))
    c4.error(f"**UANG SETOR: Rp {df_main_filter['Uang Setor'].sum():,.0f}**".replace(',', '.'))
    
    st.markdown("---")

    # Fitur TAB agar tidak kepanjangan scroll ke bawah
    tab1, tab2, tab3 = st.tabs(["📊 Laporan Utama & Setor", "🛍️ Daftar Rincian Belanja", "📦 Laporan Stok"])
    
    with tab1:
        st.write("### Grafik Omset Harian")
        grafik_data = df_main_filter.copy()
        grafik_data['Tgl'] = "Tgl " + grafik_data['Tanggal'].astype(str)
        st.line_chart(data=grafik_data.set_index('Tgl')['Omset'])
        
        st.write("### Tabel Setoran Harian")
        st.dataframe(df_main_filter.rename(columns={'Biaya Produksi': 'Produksi (Rp)', 'Belanja Operasional': 'Operasional (Rp)', 'Omset': 'Omset (Rp)', 'Uang Setor': 'Setor (Rp)'}).reset_index(drop=True), use_container_width=True)

    with tab2:
        st.write("### Semua Catatan Pembelian Barang")
        st.write("*(Diambil otomatis dari tabel rincian di sebelah kanan)*")
        if not df_rincian_gabung.empty:
            st.dataframe(df_rincian_gabung[['Tanggal', 'Barang Dibeli', 'Nominal']].rename(columns={'Nominal': 'Harga (Rp)'}).reset_index(drop=True), use_container_width=True)
            
            total_rincian_tampil = df_rincian_gabung['Nominal'].sum()
            st.warning(f"**Total Rincian Belanja yang tampil: Rp {total_rincian_tampil:,.0f}**".replace(',', '.'))
        else:
            st.info("💡 Tidak ada rincian belanja (LPG/Kresek) yang tercatat pada rentang tanggal ini.")

    with tab3:
        st.write("### Catatan Stok Barang")
        idx_stok_r, idx_stok_c = -1, -1
        for r in range(100):
            for c in range(len(df_raw.columns)):
                if "STOK DI BAWA" in str(df_raw.iloc[r, c]).upper():
                    idx_stok_r, idx_stok_c = r, c
                    break
            if idx_stok_r != -1: break
            
        if idx_stok_r != -1:
            c_nama = max(0, idx_stok_c - 2)
            df_s = df_raw.iloc[idx_stok_r+2:idx_stok_r+12, [c_nama, idx_stok_c, idx_stok_c+2, idx_stok_c+3]].copy()
            df_s.columns = ["Menu", "Bawa", "Sisa", "Laku"]
            st.dataframe(df_s.dropna(subset=["Menu"]).reset_index(drop=True), use_container_width=True)
        else:
            st.warning("Tabel stok tidak ditemukan.")

    # ---------------------------------------------------------
    # 4. MODE PERBAIKAN JIKA TERJADI ERROR
    # ---------------------------------------------------------
    with st.expander("🛠️ Klik di sini jika ada data yang kosong/salah baca"):
        st.write(f"- Radar Sistem membaca 'OMSET' di Baris: {r_omset}, Kolom: {c_omset}")
        st.write(f"- Radar Sistem menemukan Tabel Belanja (LPG dll) di Kolom ke: {kolom_rincian_ditemukan}")
        st.write("- 10 Baris Pertama Spreadsheet kamu yang dibaca robot:")
        st.dataframe(df_raw.head(10))

except Exception as e:
    st.error(f"Terjadi kendala saat membaca Spreadsheet: {e}")
