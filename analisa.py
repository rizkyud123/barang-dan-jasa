# analisa.py
import streamlit as st
import pandas as pd
import plotly.express as px

def run_analisa(spreadsheet):
    try:
        worksheet = spreadsheet.worksheet("Belanja Barang dan Jasa")
        data = worksheet.get_all_values()

        # --- cari baris header otomatis ---
        header_row = None
        for i, row in enumerate(data):
            if any("PAGU" in str(cell).upper() for cell in row):
                header_row = i
                break

        if header_row is None:
            raise ValueError("❌ Tidak menemukan baris header yang mengandung 'PAGU'")

        headers = data[header_row]
        rows = data[header_row + 1:]

        df = pd.DataFrame(rows, columns=headers)
        df = df.loc[:, df.columns.notnull()]
        df = df.loc[:, df.columns != ""]
        df = df.loc[:, ~df.columns.duplicated()]

    except Exception as e:
        st.error(f"❌ Gagal membaca worksheet: {e}")
        return

    st.header("📊 Analisa Data Barang & Jasa")

    # --- fungsi ubah ke angka ---
    def to_number(x):
        if pd.isna(x): return 0
        return pd.to_numeric(str(x).replace(",", "").replace("%", "").strip(), errors="coerce")

    numeric_cols = [
        "KEUANGAN REALISASI", "KEUANGAN %",
        "FISIK RENCANA (%)", "FISIK REALISASI (%)", "FISIK DEVIASI (%)",
        "SP2D NILAI"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(to_number)

    # === Menu pilihan analisa ===
    pilihan = st.selectbox(
        "Pilih jenis analisa:",
        ["Keuangan", "Fisik", "SP2D"]
    )

    # === Keuangan ===
    if pilihan == "Keuangan":
        if "KEUANGAN REALISASI" in df.columns:
            st.subheader("💰 Realisasi Keuangan")
            fig1 = px.bar(df, x="NAMA PEKERJAAN",
                          y="KEUANGAN REALISASI",
                          title="Realisasi Keuangan per Pekerjaan")
            st.plotly_chart(fig1, use_container_width=True)

        if "KEUANGAN %" in df.columns:
            st.subheader("📈 Persentase Realisasi Keuangan")
            fig2 = px.histogram(df, x="KEUANGAN %", nbins=20,
                                title="Distribusi Persentase Realisasi Keuangan")
            st.plotly_chart(fig2, use_container_width=True)

    # === Fisik ===
    elif pilihan == "Fisik":
        if "FISIK REALISASI (%)" in df.columns:
            st.subheader("🏗️ Realisasi Fisik")
            fig3 = px.bar(df, x="NAMA PEKERJAAN",
                          y="FISIK REALISASI (%)",
                          title="Realisasi Fisik per Pekerjaan")
            st.plotly_chart(fig3, use_container_width=True)

        if "FISIK RENCANA (%)" in df.columns and "FISIK REALISASI (%)" in df.columns:
            st.subheader("📊 Rencana vs Realisasi Fisik")
            fig4 = px.bar(df, x="NAMA PEKERJAAN",
                          y=["FISIK RENCANA (%)", "FISIK REALISASI (%)"],
                          barmode="group")
            st.plotly_chart(fig4, use_container_width=True)

    # === Tracking SP2D ===
    elif pilihan == "SP2D":
        if "TGL SP2D" in df.columns and "SP2D NILAI" in df.columns:
            st.subheader("📅 Tracking SP2D")
            df["TGL SP2D"] = pd.to_datetime(df["TGL SP2D"], errors="coerce")
            df_sp2d = df.groupby("TGL SP2D")["SP2D NILAI"].sum().reset_index()
            fig5 = px.line(df_sp2d, x="TGL SP2D", y="SP2D NILAI", markers=True,
                           title="Nilai SP2D per Tanggal")
            st.plotly_chart(fig5, use_container_width=True)

            st.dataframe(df[["TGL SP2D", "SP2D NILAI"]])
