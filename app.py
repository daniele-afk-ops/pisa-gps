import streamlit as st
import pandas as pd
import os

# Configurazione della pagina e tema scuro/sportivo
st.set_page_config(page_title="Pisa SC - GPS Load Planner", layout="wide")

# 🔵⚫ STILE GRAFICO PERSONALIZZATO (Colori Pisa SC)
st.markdown("""
    <style>
    .main { background-color: #f5f7fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #0052a5; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h1 { color: #002855; font-weight: 800; }
    h3 { color: #0052a5; }
    .sidebar .sidebar-content { background-color: #002855; color: white; }
    </style>
""", unsafe_allow_html=True)

# 📊 CONFIGURAZIONE INTESTAZIONE
col_logo, col_titolo = st.columns(2)
with col_logo:
    if os.path.exists("stemma_pisa.png"):
        st.image("stemma_pisa.png", width=120)
with col_titolo:
    st.title("🔵⚫ PISA SPORTING CLUB")
    st.subheader("Performance & Analytics — Stima del Carico Atletico")

st.markdown("<hr style='border-top: 3px solid #002855;'>", unsafe_allow_html=True)

# 📂 CARICAMENTO AUTOMATICO DEL FILE DA GITHUB
FILE_AUTO = "database_gps.xlsx"

if os.path.exists(FILE_AUTO):
    try:
        df_esercizi = pd.read_excel(FILE_AUTO, sheet_name='Anagrafica_Esercitazioni')
        df_gps_totali = pd.read_excel(FILE_AUTO, sheet_name='Parametri_GPS_Minuto')
        
        df_gps_totali.rename(columns={'esercitazione_ID': 'Esercitazione_ID'}, inplace=True)
        df_esercizi.rename(columns={'Esercitazione_ID': 'Esercitazione_ID'}, inplace=True)
        
        df_esercizi['Esercitazione_ID'] = df_esercizi['Esercitazione_ID'].astype(str).str.strip()
        df_gps_totali['Esercitazione_ID'] = df_gps_totali['Esercitazione_ID'].astype(str).str.strip()
        
        df_gps_min = df_gps_totali.copy()
        colonne_gps = ['total dist. (m)', 'z2 (m)', 'z3 (m)', 'n° sprint', 'n° accel.', 'n° decel.', 'n° burst', 'n° breaks']
        
        for col in colonne_gps:
            if col in df_gps_totali.columns:
                df_gps_min[col] = pd.to_numeric(df_gps_totali[col], errors='coerce') / pd.to_numeric(df_gps_totali['minuti'], errors='coerce')
        
        db_completo = pd.merge(df_esercizi, df_gps_min, on='Esercitazione_ID')
        
        # INTERFACCIA BARRA LATERALE (NEROAZZURRA)
        st.sidebar.markdown("## 📋 CONFIGURATORE SEDUTA")
        esercizi_disponibili = db_completo['Nome_Esercitazione'].tolist()
        scelte = st.sidebar.multiselect("Quali esercitazioni svolgi oggi?", esercizi_disponibili)
        
        if scelte:
            programma = []
            st.write("### ⏱️ Volume di Lavoro (Inserisci la durata per esercizio)")
            
            cols_minuti = st.columns(len(scelte))
            for i, es in enumerate(scelte):
                with cols_minuti[i]:
                    minuti = st.number_input(f"🏃 {es} (min)", min_value=1, max_value=120, value=15, key=es)
                    id_es = db_completo[db_completo['Nome_Esercitazione'] == es]['Esercitazione_ID'].values
                    programma.append({'Esercitazione_ID': str(id_es), 'Nuovi_Minuti': minutes})
            
            df_programma = pd.DataFrame(programma)
            report_stimato = pd.merge(df_programma, db_completo, on='Esercitazione_ID')
            
            for col in colonne_gps:
                if col in df_gps_totali.columns:
                    nome_col = col.replace('(m)', 'Stimati (m)').replace('n°', 'Tot.').strip()
                    report_stimato[nome_col] = report_stimato[col] * report_stimato['Nuovi_Minuti']
                
            colonne_finali = ['Nome_Esercitazione', 'Nuovi_Minuti', 'Categoria'] + [col.replace('(m)', 'Stimati (m)').replace('n°', 'Tot.').strip() for col in colonne_gps if col in df_gps_totali.columns]
            report_finale = report_stimato[colonne_finali]
            
            # BLOCCHI METRICHE MODERNE IN EVIDENZA
            st.write("### 📊 RIEPILOGO CARICO STIMATO")
            m1, m2, m3 = st.columns(3)
            m1.metric("⏱️ VOLUME TOTALE", f"{report_finale['Nuovi_Minuti'].sum()} min")
            m2.metric("🏃 DISTANZA COMPLESSIVA", f"{report_finale['total dist. Stimati (m)'].sum():.0f} m")
            if 'Tot. sprint' in report_finale.columns:
                m3.metric("⚡ SPRINT COMPLESSIVI", f"{report_finale['Tot. sprint'].sum():.1f}")
            
            # TABELLA DETTAGLIATA CON FORMATTAZIONE
            st.write("### 📋 DETTAGLIO EXCEL DEGLI ESERCIZI DI OGGI")
            st.dataframe(report_finale.style.background_gradient(cmap="Blues", subset=['total dist. Stimati (m)']))
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="📥 SCARICA REPORT EXCEL UFFICIALE",
                data=report_finale.to_csv(index=False).encode('utf-8'),
                file_name='Report_Pisa_Oggi.csv',
                mime='text/csv',
            )
    except Exception as e:
        st.error(f"Errore nell'elaborazione del file automatico: {e}")
else:
    st.info("ℹ️ Carica il tuo file database_gps.xlsx su GitHub per attivare la lettura automatica.")
