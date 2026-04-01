import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

# 1. Koneksi ke Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# 2. Ambil data
sheet = client.open("Siomay Jawara Malang").worksheet("Februari 2026")
data = sheet.get_all_records()
df = pd.DataFrame(data)

# 3. Buat Website
st.title("Dashboard Penjualan Siomay Jawara")

# Grafik Penjualan Harian
fig = px.line(df, x="Tanggal", y="Omset", title="Tren Penjualan Per Hari")
st.plotly_chart(fig)

# Tampilkan Tabel
st.write("Data Lengkap:", df)
