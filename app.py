import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# Konfigurasi Halaman Web
st.set_page_config(page_title="Dynamic Music - MCC Maintenance", page_icon="🎸")

st.title("🎸 Checklist Maintenance MCC")
st.write("Sistem pencatatan servis instrumen Dynamic Music")

# Fungsi pembantu untuk mengambil data dari SQLite
def get_data(query):
    conn = sqlite3.connect('checklist_mcc.db')
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Mengambil data master instrumen untuk Dropdown
df_instruments = get_data('''
    SELECT i.id_instrument, i.kode_unit, i.nama_alat, l.nama_ruangan 
    FROM instruments i
    JOIN locations l ON i.id_location = l.id_location
''')

# Merakit opsi dropdown agar mudah dibaca
options = df_instruments.apply(
    lambda row: f"[{row['kode_unit']}] {row['nama_alat']} ({row['nama_ruangan']})", 
    axis=1
).tolist()
instrument_ids = df_instruments['id_instrument'].tolist()
id_mapping = dict(zip(options, instrument_ids))

# Membuat 2 Tab utama di web
tab1, tab2 = st.tabs(["📝 Input Service Baru", "📊 Riwayat Service"])

# --- TAB 1: FORM INPUT ---
with tab1:
    st.header("Form Pengerjaan")
    
    with st.form("form_service"):
        pilihan_alat = st.selectbox("Pilih Instrumen", options)
        teknisi = st.text_input("Nama Teknisi", placeholder="Contoh: Dani")
        
        st.write("**Checklist Pengerjaan**")
        col1, col2 = st.columns(2)
        with col1:
            chk_clean = st.checkbox("Clean & Polish")
            chk_neck = st.checkbox("Neck & Setup")
            chk_elec = st.checkbox("Electronics Check")
        with col2:
            chk_fret = st.checkbox("Fretwork / Polish")
            chk_senar = st.checkbox("Ganti Senar")
            
        catatan = st.text_area("Catatan Khusus (Keluhan / Parts Diganti)")
        status_akhir = st.radio("Status Akhir", ["Selesai", "Pending Part"])
        
        # Tombol Submit
        submitted = st.form_submit_button("Simpan Data")
        
        if submitted:
            if teknisi == "":
                st.error("Nama teknisi harus diisi!")
            else:
                id_inst = id_mapping[pilihan_alat]
                tgl_sekarang = date.today().strftime("%Y-%m-%d")
                
                conn = sqlite3.connect('checklist_mcc.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO service_logs 
                    (id_instrument, tanggal_service, nama_teknisi, chk_clean_polish, chk_neck_setup, 
                    chk_electronics, chk_fretwork, chk_ganti_senar, catatan_khusus, status_akhir) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (id_inst, tgl_sekarang, teknisi, chk_clean, chk_neck, chk_elec, chk_fret, chk_senar, catatan, status_akhir))
                conn.commit()
                conn.close()
                
                st.success("✅ Data berhasil disimpan ke database!")

# --- TAB 2: RIWAYAT ---
with tab2:
    st.header("Rekapitulasi Maintenance")
    
    query_history = '''
        SELECT 
            s.tanggal_service AS "Tanggal",
            i.kode_unit AS "Kode",
            i.nama_alat AS "Instrumen",
            s.nama_teknisi AS "Teknisi",
            s.status_akhir AS "Status",
            s.catatan_khusus AS "Catatan"
        FROM service_logs s
        JOIN instruments i ON s.id_instrument = i.id_instrument
        ORDER BY s.id_service DESC
    '''
    df_history = get_data(query_history)
    
    if df_history.empty:
        st.info("Belum ada data servis yang tercatat.")
    else:
        # Menampilkan tabel interaktif (bisa di-sort & scroll)
        st.dataframe(df_history, use_container_width=True)