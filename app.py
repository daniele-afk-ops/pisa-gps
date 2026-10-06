import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Pisa SC - GPS Load Planner", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; padding: 5px 20px !important; }
    h1 { color: #002855; font-weight: 800; font-size: 1.5rem; margin: 0px !important; }
    h3 { color: #0052a5; font-weight: 700; font-size: 1rem; margin-top: 5px !important; margin-bottom: 2px !important; }
    .metric-container { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 5px; margin-bottom: 8px; }
    .metric-card { background-color: #ffffff; padding: 6px 12px; border-radius: 6px; border-left: 4px solid #0052a5; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
    .metric-label { font-size: 0.65rem !important; font-weight: 700 !important; color: #475569 !important; text-transform: uppercase; }
    .metric-value { font-size: 1.05rem !important; font-weight: 800 !important; color: #0f172a !important; }
    .sidebar .sidebar-content { background-color: #002855; color: white; }
    </style>
""", unsafe_allow_html=True)

col_logo, col_titolo = st.columns(2)
with col_logo:
    if os.path.exists("stemma_pisa.png"): st.image("stemma_pisa.png", width=60)
with col_titolo:
    st.title("🔵⚫ PISA SPORTING CLUB")
    st.subheader("Performance & Analytics")

st.markdown("<hr style='border-top: 2px solid #002855;'>", unsafe_allow_html=True)
FILE_AUTO = "database_gps.xlsx"

if os.path.exists(FILE_AUTO):
    try:
        df_es = pd.read_excel(FILE_AUTO, sheet_name='Anagrafica_Esercitazioni')
        df_gps = pd.read_excel(FILE_AUTO, sheet_name='Parametri_GPS_Minuto')
        df_gps.rename(columns={'esercitazione_ID': 'Esercitazione_ID'}, inplace=True)
        df_es.rename(columns={'Esercitazione_ID': 'Esercitazione_ID'}, inplace=True)
        df_es['Esercitazione_ID'] = df_es['Esercitazione_ID'].astype(str).str.strip()
        df_gps['Esercitazione_ID'] = df_gps['Esercitazione_ID'].astype(str).str.strip()
        
        colonne_gps = ['total dist. (m)', 'z2 (m)', 'z3 (m)', 'n° sprint', 'n° accel.', 'n° decel.', 'n° burst', 'n° breaks']
        for col in colonne_gps:
            if col in df_gps.columns: df_gps[col] = pd.to_numeric(df_gps[col], errors='coerce').fillna(0)
        df_gps['minuti'] = pd.to_numeric(df_gps['minuti'], errors='coerce').fillna(1)
        
        df_gps_min = df_gps.copy()
        for col in colonne_gps:
            if col in df_gps.columns: df_gps_min[col] = df_gps[col] / df_gps['minuti']
            
        db_completo = pd.merge(df_es, df_gps_min, on='Esercitazione_ID')
        db_completo['Cat_P'] = db_completo['Categoria'].astype(str).str.replace('*', '', regex=False).str.strip()
        
        st.sidebar.markdown("## 📋 CATEGORIE ALLENAMENTO")
        ordine = ["Attivazione", "tecnico-tattica", "possesso", "preparazione atletica", "SSG", "partita a tema", "partita"]
        scelte_totali = []
        
        for cat_o in ordine:
            m_df = db_completo[db_completo['Cat_P'].str.lower() == cat_o.lower()]
            if not m_df.empty:
                st.sidebar.markdown(f"**📂 {cat_o.upper()}**")
                ex_cat = m_df['Nome_Esercitazione'].tolist()
                s_cat = st.sidebar.multiselect(f"Seleziona {cat_o}:", ex_cat, key=f"s_{cat_o.lower()}", label_visibility="collapsed")
                if s_cat: scelte_totali.extend(s_cat)
                
        if scelte_totali:
            programma = []
            st.write("### ⏱️ Volume di Lavoro")
            cols_m = st.columns(len(scelte_totali))
            for i, es in enumerate(scelte_totali):
                with cols_m[i]:
                    minuti = st.number_input(f"🏃 {es} (min)", min_value=1, max_value=120, value=15, key=f"m_{es}")
                    id_es = db_completo[db_completo['Nome_Esercitazione'] == es]['Esercitazione_ID'].values
                    if len(id_es) > 0:
                        # 🛠️ CORREZIONE DEFINITIVA: Sostituito 'minutes' con 'minuti'
                        programma.append({'Esercitazione_ID': str(id_es[0]), 'Nuovi_Minuti': minuti})
                    
            df_prog = pd.DataFrame(programma)
            rep = pd.merge(df_prog, db_completo, on='Esercitazione_ID')
            
            for col in colonne_gps:
                if col in df_gps.columns:
                    n_col = col.replace('(m)', 'Stimati (m)').replace('n°', 'Tot.').strip()
                    rep[n_col] = rep[col] * rep['Nuovi_Minuti']
                    
            c_finali = ['Nome_Esercitazione', 'Nuovi_Minuti', 'Categoria'] + [col.replace('(m)', 'Stimati (m)').replace('n°', 'Tot.').strip() for col in colonne_gps if col in df_gps.columns]
            report_finale = rep[c_finali].copy()
            
            for col in report_finale.columns:
                if col not in ['Nome_Esercitazione', 'Categoria']:
                    report_finale[col] = pd.to_numeric(report_finale[col], errors='coerce').fillna(0).round(0).astype(int)
                    
            st.write("### 📊 Riepilogo Carico Stimato Allenamento")
            v_vol = int(report_finale['Nuovi_Minuti'].sum())
            v_dist = int(report_finale['total dist. Stimati (m)'].sum())
            
            col_sprint = [c for c in report_finale.columns if 'sprint' in c.lower()]
            v_spr = int(report_finale[col_sprint].sum()) if col_sprint else 0
            
            v_z2 = int(report_finale['z2 Stimati (m)'].sum()) if 'z2 Stimati (m)' in report_finale.columns else 0
            v_z3 = int(report_finale['z3 Stimati (m)'].sum()) if 'z3 Stimati (m)' in report_finale.columns else 0
            
            col_acc = [c for c in report_finale.columns if 'accel' in c.lower()]
            v_acc = int(report_finale[col_acc].sum()) if col_acc else 0
            
            col_dec = [c for c in report_finale.columns if 'decel' in c.lower()]
            v_dec = int(report_finale[col_dec].sum()) if col_dec else 0
            
            col_bur = [c for c in report_finale.columns if 'burst' in c.lower()]
            v_bur = int(report_finale[col_bur].sum()) if col_bur else 0
            
            col_brk = [c for c in report_finale.columns if 'breaks' in c.lower()]
            v_brk = int(report_finale[col_brk].sum()) if col_brk else 0

            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card"><div class="metric-label">⏱️ Volume Totale</div><div class="metric-value">{v_vol} min</div></div>
                <div class="metric-card"><div class="metric-label">🏃 Distanza Totale</div><div class="metric-value">{v_dist} m</div></div>
                <div class="metric-card"><div class="metric-label">⚡ Sprint Totali</div><div class="metric-value">{v_spr}</div></div>
                <div class="metric-card"><div class="metric-label">🏃‍♂️ Zona 2 Totale</div><div class="metric-value">{v_z2} m</div></div>
                <div class="metric-card"><div class="metric-label">🔥 Zona 3 Totale</div><div class="metric-value">{v_z3} m</div></div>
                <div class="metric-card"><div class="metric-label">📈 Accelerazioni</div><div class="metric-value">{v_acc}</div></div>
                <div class="metric-card"><div class="metric-label">📉 Decelerazioni</div><div class="metric-value">{v_dec}</div></div>
                <div class="metric-card"><div class="metric-label">💥 Burst Totali</div><div class="metric-value">{v_bur}</div></div>
                <div class="metric-card"><div class="metric-label">🛑 Breaks Totali</div><div class="metric-value">{v_brk}</div></div>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("### 📋 Tabella Complessiva Carico Fasi")
            col_num = report_finale.select_dtypes(include=['number']).columns.tolist()
            formato_v = {c: "{:.0f}" for c in col_num}
            
            # 🛠️ SISTEMAZIONE VISIVA DELLE COLONNE: Nome fisso e largo, i numeri si stringono proporzionati
            config_colonne = {
                'Nome_Esercitazione': st.column_config.Column(pinned=True, width="medium"),
                'Categoria': st.column_config.Column()
            }
            for col in col_num:
                config_colonne[col] = st.column_config.Column(width="small")
            
            st.dataframe(
                report_finale.style.background_gradient(cmap="Blues", subset=col_num, axis=0).format(formato_v), 
                use_container_width=True,
                column_config=config_colonne
            )
            st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
            st.download_button(label="📥 SCARICA REPORT EXCEL UFFICIALE", data=report_finale.to_csv(index=False).encode('utf-8'), file_name='Report_Pisa_Oggi.csv', mime='text/csv')
        else:
            st.write("### 💡 Seleziona uno o più esercizi dai menu a sinistra.")
    except Exception as e:
        st.error(f"Errore: {e}")
else:
    st.info("ℹ️ Carica il tuo file database_gps.xlsx su GitHub.")
