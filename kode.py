import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from analisa import run_analisa  # ambil fungsi analisa dari analisa.py

# === Konfigurasi Google Sheets API ===
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# 🔑 Ambil kredensial dari Streamlit Secrets
try:
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    client = gspread.authorize(creds)
except Exception as e:
    st.error(f"❌ Gagal autentikasi ke Google Sheets: {e}")
    st.stop()

# Ganti dengan Spreadsheet ID kamu
SPREADSHEET_ID = "15-I60dvETnknwpONxl3HtZS2Pm-vb2P33Kw7LMc_ThQ"
spreadsheet = client.open_by_key(SPREADSHEET_ID)

# === Setup Streamlit ===
st.set_page_config(page_title="Dashboard Barang & Jasa", layout="wide")
st.title("📊 Dashboard Barang & Jasa 2025")

# === Sidebar Navigation ===
st.sidebar.header("📑 Navigasi")
menu = st.sidebar.radio("Pilih Menu", ["Dashboard", "Analisa"])

# ================= DASHBOARD =================
if menu == "Dashboard":
    # sheet yang boleh dipilih
    allowed_sheets = ["bun", "nak", "psp", "tph"]
    sheet_titles = [ws.title for ws in spreadsheet.worksheets() if ws.title.lower() in allowed_sheets]

    selected = st.sidebar.radio("Pilih Sub-Bidang / Sheet", sheet_titles)
    worksheet = spreadsheet.worksheet(selected)

    # === Ambil Data Google Sheets (sekali saja) ===
    if f"original_data_{selected}" not in st.session_state:
        raw_data = worksheet.get_all_values()
        header_rows = raw_data[:4]   # header baris 1–4
        data_rows = raw_data[4:]     # mulai baris 5

        # Gabung header multi-baris
        combined_headers = []
        for col in zip(*header_rows):
            merged = " ".join([h.strip() for h in col if h.strip() != ""]).strip()
            if merged == "":
                merged = "Kolom"
            combined_headers.append(merged)

        # Header unik (hindari duplikat)
        unique_headers = []
        seen = {}
        for h in combined_headers:
            if h in seen:
                seen[h] += 1
                h = f"{h}_{seen[h]}"
            else:
                seen[h] = 1
            unique_headers.append(h)

        df = pd.DataFrame(data_rows, columns=unique_headers)

        st.session_state[f"headers_{selected}"] = unique_headers
        st.session_state[f"edited_df_{selected}"] = df.copy()

    # === Konfigurasi Kolom (Rp & Persen) ===
    column_config = {}
    for col in st.session_state[f"headers_{selected}"]:
        col_upper = col.upper()
        if "RP" in col_upper or "ANGGARAN" in col_upper or "HPS" in col_upper or "NILAI" in col_upper:
            column_config[col] = st.column_config.NumberColumn(
                col,
                format="Rp %d",
                step=1000
            )
        elif "%" in col_upper or "PERSEN" in col_upper or "PERSENTASE" in col_upper:
            column_config[col] = st.column_config.NumberColumn(
                col,
                format="%.2f%%",
                min_value=0,
                max_value=100,
                step=0.01
            )

    st.subheader(f"📌 Data: {selected.upper()}")

    # === Data Editor (editable) ===
    st.session_state[f"edited_df_{selected}"] = st.data_editor(
        st.session_state[f"edited_df_{selected}"],
        num_rows="dynamic",
        use_container_width=True,
        column_config=column_config,
        key=f"editor_{selected}"
    )

    # === Tombol Simpan ke Google Sheets ===
    if st.button("💾 Simpan Perubahan", use_container_width=True):
        edited_df = st.session_state[f"edited_df_{selected}"]
        values = edited_df.values.tolist()
        headers = st.session_state[f"headers_{selected}"]

        # Tentukan range update
        cell_list = worksheet.range(
            f"A5:{chr(65+len(headers)-1)}{len(values)+4}"
        )

        flat_values = [str(item) if item is not None else "" for row in values for item in row]

        for cell, val in zip(cell_list, flat_values):
            cell.value = val

        worksheet.update_cells(cell_list, value_input_option="USER_ENTERED")

        st.success(f"✅ Data berhasil disimpan ke sheet: {selected.upper()}")

# ================= ANALISA =================
elif menu == "Analisa":
    run_analisa(spreadsheet)
