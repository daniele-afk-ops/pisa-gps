import streamlit as st
import pandas as pd
import os

# Configurazione della pagina e tema scuro/sportivo
st.set_page_config(page_title="Pisa SC - GPS Load Planner", layout="wide")

# 🔵⚫ RESET E DESIGN VISIVO AVANZATO (Card grandi, spaziate e non schiacciate)
st.markdown("""
    <style>
    .main { background-color: #f8fafc; padding: 20px; }
    h1 { color: #002855; font-weight: 800; font-size: 2.2rem; }
    h3 { color: #0052a5; font-weight: 700; margin-top: 25px; }
    
    /* Griglia contenitore per dare respiro */
    .metric-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 25px;
        margin-top: 15px;
        margin-bottom: 25px;
    }
    
    /* Card atletica spaziosa ed elegante */
    .metric-card {
        background-color: #ffffff;
        padding: 25px 20px;
        border-radius: 12px;
        border-left: 6px solid #0052a5;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-label {
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        color: #475569 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        line-height: 1;
    }
    
    .sidebar .sidebar-content { background-color: #002855; color: white; }
    </style>
""", unsafe_allow_html=True)

# 📊 CONFIGURAZIONE INTESTAZIONE
col_logo, col_titolo = st.columns([1, 6])
with col_logo:
    if os.path.exists("stemma_pisa.png"):
        st.image("stemma_pisa.png", width=110)
with col_titolo:
    st.title("🔵⚫ PISA SPORTING CLUB")
    st.subheader("Performance & Analytics — Pianificazione Carico Atletico")

st.markdown("<hr style='border-top: 3px solid #002855; margin-bottom: 20px;'>", unsafe_allow_html=True)

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
            st.write("### ⏱️ Volume di Lavoro (Durata in minuti)")
            
            cols_minuti = st.columns(len(scelte_totali))
            for i, es in enumerate(scelte_totali):
                with cols_minuti[i]:
                    minuti = st.number_input(f"🏃 {es} (min)", min_value=1, max_value=120, value=15, key=f"min_{es}")
                    id_es = db_completo[db_completo['Nome_Esercitazione'] == es]['Esercitazione_ID'].values
                    if len(id_es) > 0:
                        programma.append({'Esercitazione_ID': str(id_es), 'Nuovi_Minuti': minuti})
            
            df_programma = pd.DataFrame(programma)
            report_stimato = pd.merge(df_programma, db_completo, on='Esercitazione_ID')
            
            for col in colonne_gps:
                if col in df_gps_totali.columns:
                    nome_col = col.replace('(m)', 'Stimati (m)').replace('n°', 'Tot.').strip()
                    report_stimato[nome_col] = report_stimato[col] * report_stimato['Nuovi_Minuti']
            
            colonne_finali = ['Nome_Esercitazione', 'Nuovi_Minuti', 'Categoria'] + [col.replace('(m)', 'Stimati (m)').replace('n°', 'Tot.').strip() for col in colonne_gps if col in df_gps_totali.columns]
            report_finale = report_stimato[colonne_finali].copy()
            
            # ARROTONDAMENTO COMPLETO PER CORREGGERE LE VIRGOLE NELLA TABELLA
            for col in report_finale.columns:
                if report_finale[col].dtype in ['float64', 'int64']:
                    if 'sprint' in col.lower() or 'breaks' in col.lower() or 'burst' in col.lower():
                        report_finale[col] = report_finale[col].round(1)
                    elif 'minuti' not in col.lower():
                        report_finale[col] = report_finale[col].round(0).astype(int)
            
            # 📊 RIEPILOGO CARICO STIMATO - HTML PERSONALIZZATO SPAZIOSO (3x3 Grid)
            st.write("### 📊 Riepilogo Carico Stimato Allenamento")
            
            # Estrazione valori totali sommati per i blocchi grafici
            v_vol = int(report_finale['Nuovi_Minuti'].sum())
            v_dist = int(report_finale['total dist. Stimati (m)'].sum())
            v_spr = report_finale['Tot. sprint'].sum() if 'Tot. sprint' in report_finale.columns else 0.0
            v_z2 = int(report_finale['z2 Stimati (m)'].sum()) if 'z2 Stimati (m)' in report_finale.columns else 0
            v_z3 = int(report_finale['z3 Stimati (m)'].sum()) if 'z3 Stimati (m)' in report_finale.columns else 0
            v_acc = int(report_finale['Tot. accel.'].sum()) if 'Tot. accel.' in report_finale.columns else 0
            v_dec = int(report_finale['Tot. decel.'].sum()) if 'Tot. decel.' in report_finale.columns else 0
            v_bur = report_finale['Tot. burst'].sum() if 'Tot. burst' in report_finale.columns else 0.0
            v_brk = report_finale['Tot. breaks'].sum() if 'Tot. breaks' in report_finale.columns else 0.0

            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card"><div class="metric-label">⏱️ Volume Totale Seduta</div><div class="metric-value">{v_vol} min</div></div>
                <div class="metric-card"><div class="metric-left"></div><div class="metric-label">🏃 Distanza Complessiva</div><div class="metric-value">{v_dist} m</div></div>
                <div class="metric-card"><div class="metric-label">⚡ Sprint Complessivi</div><div class="metric-value">{v_spr:.1f}</div></div>
                <div class="metric-card"><div class="metric-label">🏃‍♂️ Corsa in Zona 2</div><div class="metric-value">{v_z2} m</div></div>
                <div class="metric-card"><div class="metric-label">🔥 Corsa in Zona 3</div><div class="metric-value">{v_z3} m</div></div>
                <div class="metric-card"><div class="metric-label">📈 Accelerazioni Totali</div><div class="metric-value">{v_acc}</div></div>
                <div class="metric-card"><div class="metric-label">📉 Decelerazioni Totali</div><div class="metric-value">{v_dec}</div></div>
                <div class="metric-card"><div class="metric-label">💥 Burst Totali</div><div class="metric-value">{v_bur:.1f}</div></div>
                <div class="metric-card"><div class="metric-label">🛑 Breaks Totali</div><div class="metric-value">{v_brk:.1f}</div></div>
            </div>
            """, unsafe_allow_html=True)
            
            # 📋 TABELLA COMPLESSIVA
            st.write("### 📋 Tabella Complessiva sul Carico delle Fasi")
            colonne_numeriche = report_finale.select_dtypes(include=['number']).columns.tolist()
            
            st.dataframe(report_finale.style.background_gradient(cmap="Blues", subset=colonne_numeriche, axis=0), use_container_width=True)
            
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
