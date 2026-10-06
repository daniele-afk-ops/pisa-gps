import streamlit as st
import pandas as pd
import os, re
st.set_page_config(page_title="Pisa SC - GPS Load Planner", layout="wide")
st.markdown("""<style>
    .main { background-color: #f1f5f9; padding: 10px 25px !important; }
    h1 { color: #002855; font-weight: 900; font-size: 1.7rem; margin: 0 !important; letter-spacing: -0.5px; }
    h3 { color: #0052a5; font-weight: 800; font-size: 1.1rem; margin-top: 15px !important; margin-bottom: 5px !important; text-transform: uppercase; letter-spacing: 0.5px; }
    h4 { color: #0f172a; font-weight: 700; font-size: 0.95rem; margin-bottom: 4px !important; border-bottom: 2px solid #002855; padding-bottom: 2px; width: fit-content; }
    .metric-container { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 8px 0 12px 0; }
    .metric-card { background-color: #ffffff; padding: 8px 14px; border-radius: 6px; border-left: 5px solid #0052a5; border-right: 1px solid #e2e8f0; border-top: 1px solid #e2e8f0; border-bottom: 2px solid #0f172a; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .metric-label { font-size: 0.68rem !important; font-weight: 800 !important; color: #475569 !important; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { font-size: 1.15rem !important; font-weight: 900 !important; color: #002855 !important; }
    .sidebar .sidebar-content { background-color: #002855; color: white; }
    .t-container { width: 100% !important; overflow-x: hidden !important; margin-top: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); border-radius: 4px; }
    .pisa-table { width: 100% !important; border-collapse: collapse !important; table-layout: fixed !important; }
    .pisa-table th, .pisa-table td { font-size: 0.72rem !important; padding: 5px 4px !important; text-align: center !important; white-space: normal !important; word-break: break-word !important; border: 1px solid #cbd5e1 !important; }
    .pisa-table th { background-color: #002855 !important; color: white !important; font-weight: 800 !important; text-transform: uppercase; font-size: 0.7rem !important; letter-spacing: 0.3px; }
    .m-box { background-color: #f8fafc; color: #002855; padding: 6px 12px; border-radius: 4px; font-size: 0.75rem; margin: -4px 0 15px 0; border: 1px solid #e2e8f0; border-left: 4px solid #0052a5; font-weight: 500; }
</style>""", unsafe_allow_html=True)
col_l, col_t = st.columns([1, 10])
with col_l:
    if os.path.exists("stemma_pisa.png"): st.image("stemma_pisa.png", width=75)
with col_t:
    st.title("🔵⚫ PISA SPORTING CLUB")
    st.markdown("<p style='color: #64748b; font-weight: 600; margin: -5px 0 0 0; font-size: 0.9rem;'>Performance & Analytics — Pianificazione Carichi GPS</p>", unsafe_allow_html=True)
st.markdown("<hr style='border-top: 3px solid #002855; margin-top: 8px; margin-bottom: 12px;'>", unsafe_allow_html=True)
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
        st.sidebar.markdown("<h2 style='color: white; font-size: 1.1rem; font-weight: 800; letter-spacing: 0.5px;'>📋 MENU CONFIGURAZIONE</h2>", unsafe_allow_html=True)
        ordine = ["Attivazione", "tecnico-tattica", "possesso", "preparazione atletica", "SSG", "partita a tema", "partita"]
        scelte_totali = []
        for cat_o in ordine:
            m_df = db_completo[db_completo['Cat_P'].str.lower() == cat_o.lower()]
            if not m_df.empty:
                st.sidebar.markdown(f"<span style='color: #cbd5e1; font-size: 0.8rem; font-weight: 700;'>📂 {cat_o.upper()}</span>", unsafe_allow_html=True)
                ex_cat = m_df['Nome_Esercitazione'].tolist()
                s_cat = st.sidebar.multiselect(f"Seleziona {cat_o}:", ex_cat, key=f"s_{cat_o.lower()}", label_visibility="collapsed")
                if s_cat: scelte_totali.extend(s_cat)
        if scelte_totali:
            programma = []
            st.write("### ⏱️ Impostazione Fasi di Lavoro & Spazi")
            for es in scelte_totali:
                st.markdown(f"#### 🏃 Phase: {es}")
                c1, c2, c3, c4 = st.columns(4)
                with c1: minuti = st.number_input("Durata (min):", min_value=1, max_value=120, value=15, key=f"m_{es}")
                with c2: lunghezza = st.number_input("Lunghezza (m):", min_value=5, max_value=120, value=30, key=f"lu_{es}")
                with c3: larghezza = st.number_input("Larghezza (m):", min_value=5, max_value=90, value=20, key=f"la_{es}")
                with c4: giocatori = st.number_input("N° Giocatori:", min_value=1, max_value=30, value=10, key=f"gi_{es}")
                area_fase = lunghezza * larghezza
                mq_fase = area_fase / giocatori
                st.markdown(f'<div class="m-box">📐 Superficie Totale: <b>{area_fase} m²</b> &nbsp;|&nbsp; 👥 Densità Individuale: <b>{mq_fase:.1f} m²/giocatore</b></div>', unsafe_allow_html=True)
                id_es = db_completo[db_completo['Nome_Esercitazione'] == es]['Esercitazione_ID'].values
                if len(id_es) > 0: programma.append({'Esercitazione_ID': str(id_es), 'Nuovi_Minuti': minuti})
            df_prog = pd.DataFrame(programma)
            rep = pd.merge(df_prog, db_completo, on='Esercitazione_ID')
            for col in colonne_gps:
                if col in df_gps.columns:
                    n_col = col.replace('(m)', 'Stimati (m)').replace('n°', 'Tot.').strip()
                    rep[n_col] = rep[col] * rep['Nuovi_Minuti']
            c_finali = ['Nome_Esercitazione', 'Nuovi_Minuti', 'Categoria'] + [col.replace('(m)', 'Stimati (m)').replace('n°', 'Tot.').strip() for col in colonne_gps if col in df_gps.columns]
            report_finale = rep[c_finali].copy()
            for col in report_finale.columns:
                if col not in ['Nome_Esercitazione', 'Categoria']: report_finale[col] = pd.to_numeric(report_finale[col], errors='coerce').fillna(0).round(0).astype(int)
            st.write("### 📊 Riepilogo Carico Totale Allenamento")
            v_vol = int(report_finale['Nuovi_Minuti'].sum())
            v_dist = int(report_finale['total dist. Stimati (m)'].sum())
            col_sprint = [c for c in report_finale.columns if 'sprint' in c.lower()]
            v_spr = int(report_finale[col_sprint].sum().sum()) if col_sprint else 0
            v_z2 = int(report_finale['z2 Stimati (m)'].sum()) if 'z2 Stimati (m)' in report_finale.columns else 0
            v_z3 = int(report_finale['z3 Stimati (m)'].sum()) if 'z3 Stimati (m)' in report_finale.columns else 0
            col_acc = [c for c in report_finale.columns if 'accel' in c.lower()]
            v_acc = int(report_finale[col_acc].sum().sum()) if col_acc else 0
            col_dec = [c for c in report_finale.columns if 'decel' in c.lower()]
            v_dec = int(report_finale[col_dec].sum().sum()) if col_dec else 0
            col_bur = [c for c in report_finale.columns if 'burst' in c.lower()]
            v_bur_val = int(report_finale[col_bur].sum().sum()) if col_bur else 0
            col_brk = [c for c in report_finale.columns if 'breaks' in c.lower()]
            v_brk_val = int(report_finale[col_brk].sum().sum()) if col_brk else 0
            st.markdown(f"""<div class="metric-container">
                <div class="metric-card"><div class="metric-label">⏱️ Volume Totale</div><div class="metric-value">{v_vol} min</div></div>
                <div class="metric-card"><div class="metric-label">🏃 Distanza Totale</div><div class="metric-value">{v_dist} m</div></div>
                <div class="metric-card"><div class="metric-label">⚡ Sprint Totali</div><div class="metric-value">{v_spr}</div></div>
                <div class="metric-card"><div class="metric-label">🏃‍♂️ Zona 2 Totale</div><div class="metric-value">{v_z2} m</div></div>
                <div class="metric-card"><div class="metric-label">🔥 Zona 3 Totale</div><div class="metric-value">{v_z3} m</div></div>
                <div class="metric-card"><div class="metric-label">📈 Accelerazioni</div><div class="metric-value">{v_acc}</div></div>
                <div class="metric-card"><div class="metric-label">📉 Decelerazioni</div><div class="metric-value">{v_dec}</div></div>
                <div class="metric-card"><div class="metric-label">💥 Burst Totali</div><div class="metric-value">{v_bur_val}</div></div>
                <div class="metric-card"><div class="metric-label">🛑 Breaks Totali</div><div class="metric-value">{v_brk_val}</div></div>
            </div>""", unsafe_allow_html=True)
            st.write("### 📋 Quadro Analitico Report Carichi Fasi")
            col_num = report_finale.select_dtypes(include=['number']).columns.tolist()
            formato_v = {c: "{:.0f}" for c in col_num}
            html_rows = ""
            for idx, row in report_finale.iterrows():
                row_html = f"<tr><td style='font-weight: 600; text-align: left; padding-left: 8px;'>{row['Nome_Esercitazione']}</td><td>{row['Nuovi_Minuti']}</td><td style='color: #475569;'>{row['Categoria']}</td>"
                for col in col_num:
                    if col != 'Nuovi_Minuti':
                        val = row[col]
                        max_v, min_v = report_finale[col].max(), report_finale[col].min()
                        alpha = 0.08 + 0.48 * ((val - min_v) / (max_v - min_v)) if max_v != min_v else 0.15
                        row_html += f"<td style='background-color: rgba(0, 82, 165, {alpha:.2f}); font-weight: 600; color: #002855 !important;'>{val:.0f}</td>"
                row_html += "</tr>"
                html_rows += row_html
            headers_html = "<tr><th style='width: 16%; text-align: left; padding-left: 8px;'>Esercitazione</th><th style='width: 6%;'>Minuti</th><th style='width: 11%;'>Categoria</th>"
            for col in col_num:
                if col != 'Nuovi_Minuti':
                    nome_p = col.replace('total dist.', 'total dist.').replace('Stimati', 'Stimati').replace('Tot. sprint', 'Sprint Stimati').replace('Tot. accel.', 'Accel. Stimati').replace('Tot. decel.', 'Decel. Stimati').replace('Tot. burst', 'Burst Stimati').replace('Tot. breaks', 'Breaks Stimati')
                    headers_html += f"<th>{nome_p}</th>"
            headers_html += "</tr>"
            st.markdown(f'<div class="t-container"><table class="pisa-table"><thead>{headers_html}</thead><tbody>{html_rows}</tbody></table></div>', unsafe_allow_html=True)
            st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
            st.download_button(label="📥 ESPORTA REPORT EXCEL UFFICIALE (.CSV)", data=report_finale.to_csv(index=False).encode('utf-8'), file_name='Report_Pisa_Oggi.csv', mime='text/csv')
        else: st.write("### 💡 Seleziona gli esercizi dal pannello laterale per iniziare.")
    except Exception as e: st.error(f"Errore: {e}")
else: st.info("ℹ️ Database database_gps.xlsx non rilevato.")
