import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pisa SC - GPS Load Planner", layout="wide")

# 📊 GRAFICA PERSONALIZZATA: Inserimento dello stemma ufficiale del Pisa SC locale
col_logo, col_titolo = st.columns([1, 4])
with col_logo:
    st.image("stemma_pisa.png", width=120)
with col_titolo:
    st.title("🔵⚫ Pisa SC")
    st.subheader("Pianificazione seduta e stima del carico atletico")

st.markdown("---")

uploaded_file = st.file_uploader("📂 Trascina o seleziona il tuo file database_gps.xlsx", type=["xlsx"])

if uploaded_file is not None:
    try:
        df_esercizi = pd.read_excel(uploaded_file, sheet_name='Anagrafica_Esercitazioni')
        df_gps_totali = pd.read_excel(uploaded_file, sheet_name='Parametri_GPS_Minuto')
        
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
        
        st.sidebar.header("📋 Seleziona Esercitazioni")
        esercizi_disponibili = db_completo['Nome_Esercitazione'].tolist()
        scelte = st.sidebar.multiselect("Quali esercizi svolgi oggi?", esercizi_disponibili)
        
        if scelte:
            programma = []
            st.write("### ⏱️ Inserisci la durata in minuti per ogni lavoro:")
            cols_minuti = st.columns(len(scelte))
            for i, es in enumerate(scelte):
                with cols_minuti[i]:
                    minuti = st.number_input(f"{es}", min_value=1, max_value=120, value=15, key=es)
                    id_es = db_completo[db_completo['Nome_Esercitazione'] == es]['Esercitazione_ID'].values
                    programma.append({'Esercitazione_ID': str(id_es[0]), 'Nuovi_Minuti': minuti})
            
            df_programma = pd.DataFrame(programma)
            report_stimato = pd.merge(df_programma, db_completo, on='Esercitazione_ID')
            
            for col in colonne_gps:
                if col in df_gps_totali.columns:
                    nome_col = col.replace('(m)', 'Stimati (m)').replace('n°', 'Tot.').strip()
                    report_stimato[nome_col] = report_stimato[col] * report_stimato['Nuovi_Minuti']
                
            colonne_finali = ['Nome_Esercitazione', 'Nuovi_Minuti', 'Categoria'] + [col.replace('(m)', 'Stimati (m)').replace('n°', 'Tot.').strip() for col in colonne_gps if col in df_gps_totali.columns]
            report_finale = report_stimato[colonne_finali]
            
            st.write("### 📊 Carico Totale Stimato Allenamento")
            m1, m2, m3 = st.columns(3)
            m1.metric("⏱️ Durata Totale", f"{report_finale['Nuovi_Minuti'].sum()} min")
            m2.metric("🏃 Distanza Totale", f"{report_finale['total dist. Stimati (m)'].sum():.0f} m")
            if 'Tot. sprint' in report_finale.columns:
                m3.metric("⚡ Sprint Totali", f"{report_finale['Tot. sprint'].sum():.0f}")
            
            st.write("### 📋 Dettaglio Lavori Odierni")
            st.dataframe(report_finale)
            
            st.download_button(
                label="📥 Scarica Report Excel",
                data=report_finale.to_csv(index=False).encode('utf-8'),
                file_name='Report_Pisa_Oggi.csv',
                mime='text/csv',
            )
    except Exception as e:
        st.error(f"Errore nei dati del file Excel: {e}")
else:
    st.info("ℹ️ Carica il tuo file database_gps.xlsx per iniziare.")
