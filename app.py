import streamlit as st
import pandas as pd
import os

# Configurazione della pagina e tema scuro/sportivo
st.set_page_config(page_title="Pisa SC - GPS Load Planner", layout="wide")

# 🔵⚫ STILE GRAFICO PERSONALIZZATO (Font ridotti per 9 metriche in linea)
st.markdown("""
    <style>
    .main { background-color: #f5f7fa; }
    .stMetric { background-color: #ffffff; padding: 8px 3px; border-radius: 6px; border-left: 3px solid #0052a5; box-shadow: 0 1px 3px rgba(0,0,0,0.05); text-align: center; }
    .stMetric label { font-size: 0.65rem !important; font-weight: 700; color: #002855; white-space: nowrap; }
    .stMetric .st-c2 { font-size: 0.95rem !important; font-weight: 800; color: #111111; }
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
    st.subheader("Performance & Analytics — Pianificazione Seduta")

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
        
        db_completo['Categoria_Pulita'] = db_completo['Categoria'].astype(str).str.replace('*', '', regex=False).str.strip()
        
        # 📋 INTERFACCIA BARRA LATERALE
        st.sidebar.markdown("## 📋 CATEGORIE ALLENAMENTO")
        
        ordine_cronologico = [
            "Attivazione",
            "tecnico-tattica", 
            "possesso",
            "preparazione atletica",
            "SSG",
            "partita a tema",
            "partita"
        ]
        
        scelte_totali = []
        
        for cat_ordine in ordine_cronologico:
            match_df = db_completo[db_completo['Categoria_Pulita'].str.lower() == cat_ordine.lower()]
            if not match_df.empty:
                nome_categoria_visibile = cat_ordine.upper()
                st.sidebar.markdown(f"**📂 {nome_categoria_visibile}**")
                
                esercizi_cat = match_df['Nome_Esercitazione'].tolist()
                scelte_cat = st.sidebar.multiselect(
                    f"Seleziona attività per {cat_ordine}:", 
                    esercizi_cat, 
                    key=f"sel_{cat_ordine.lower()}", 
                    label_visibility="collapsed"
                )
                if scelte_cat:
                    scelte_totali.extend(scelte_cat)
        
        if scelte_totali:
            programma = []
            st.write("### ⏱️ Volume di Lavoro (Inserisci la durata di ogni fase)")
            
            cols_minuti = st.columns(len(scelte_totali))
            for i, es in enumerate(scelte_totali):
                with cols_minuti[i]:
                    minuti = st.number_input(f"🏃 {es} (min)", min_value=1, max_value=120, value=15, key=f"min_{es}")
                    id_es = db_completo[db_completo['Nome_Esercitazione'] == es]['Esercitazione_ID'].values
                    if len(id_es) > 0:
                        # 🛠️ FIX ERRORE: cambiato 'minuti' in 'minuti'
                        programma.append({'Esercitazione_ID': str(id_es[0]), 'Nuovi_Minuti': minuti})
            
            df_programma = pd.DataFrame(programma)
            report_stimato = pd.merge(df_programma, db_completo, on='Esercitazione_ID')
            
            for col in colonne_gps:
                if col in df_gps_totali.columns:
                    nome_col = col.replace('(m)', 'Stimati (m)').replace('n°', 'Tot.').strip()
                    report_stimato[nome_col] = report_stimato[col] * report_stimato['Nuovi_Minuti']
                    
                    if 'sprint' in nome_col or 'breaks' in nome_col or 'burst' in nome_col:
                        report_stimato[nome_col] = report_stimato[nome_col].round(1)
                    else:
                        report_stimato[nome_col] = report_stimato[nome_col].round(0).astype(int)
                
            colonne_finali = ['Nome_Esercitazione', 'Nuovi_Minuti', 'Categoria'] + [col.replace('(m)', 'Stimati (m)').replace('n°', 'Tot.').strip() for col in colonne_gps if col in df_gps_totali.columns]
            report_finale = report_stimato[colonne_finali]
            
            # 📊 RIEPILOGO COMPATTO - 9 COLONNE ALLINEATE IN UNA SOLA RIGA
            st.write("### 📊 RIEPILOGO CARICO STIMATO ALLENAMENTO")
            
            tot_cols = st.columns(9)
            tot_cols[0].metric("⏱️ VOL. TOTALE", f"{int(report_finale['Nuovi_Minuti'].sum())} m'")
            tot_cols[1].metric("🏃 DIST. TOTALE", f"{int(report_finale['total dist. Stimati (m)'].sum())} m")
            if 'Tot. sprint' in report_finale.columns:
                tot_cols[2].metric("⚡ TOT. SPRINT", f"{report_finale['Tot. sprint'].sum():.1f}")
            if 'z2 Stimati (m)' in report_finale.columns:
                tot_cols[3].metric("🏃‍♂️ ZONA 2 TOT.", f"{int(report_finale['z2 Stimati (m)'].sum())} m")
            if 'z3 Stimati (m)' in report_finale.columns:
                tot_cols[4].metric("🔥 ZONA 3 TOT.", f"{int(report_finale['z3 Stimati (m)'].sum())} m")
            if 'Tot. accel.' in report_finale.columns:
                tot_cols[5].metric("📈 ACCEL. TOT.", f"{int(report_finale['Tot. accel.'].sum())}")
            if 'Tot. decel.' in report_finale.columns:
                tot_cols[6].metric("📉 DECEL. TOT.", f"{int(report_finale['Tot. decel.'].sum())}")
            if 'Tot. burst' in report_finale.columns:
                tot_cols[7].metric("💥 BURST TOT.", f"{report_finale['Tot. burst'].sum():.1f}")
            if 'Tot. breaks' in report_finale.columns:
                tot_cols[8].metric("🛑 BREAKS TOT.", f"{report_finale['Tot. breaks'].sum():.1f}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 📋 TABELLA CON BLU INDIPENDENTE PER OGNI COLONNA NUMERICA
            st.write("### 📋 TABELLA COMPLESSIVA SUL CARICO DELLE FASI")
            colonne_numeriche = report_finale.select_dtypes(include=['number']).columns.tolist()
            
            # L'asse 0 (axis=0) applica il colore blu evidenziando il massimo valore di ogni colonna in verticale
            st.dataframe(report_finale.style.background_gradient(cmap="Blues", subset=colonne_numeriche, axis=0))
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="📥 SCARICA REPORT EXCEL UFFICIALE",
                data=report_finale.to_csv(index=False).encode('utf-8'),
                file_name='Report_Pisa_Oggi.csv',
                mime='text/csv',
            )
        else:
            st.write("### 💡 Seleziona uno o più esercizi dai menu a sinistra per calcolare il carico dell'allenamento.")
    except Exception as e:
        st.error(f"Errore nell'elaborazione del file automatico: {e}")
else:
    st.info("ℹ️ Carica il tuo file database_gps.xlsx su GitHub per attivare la lettura automatica.")
