import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import openai  # Importazione della libreria OpenAI

# Configurazione della pagina
st.set_page_config(
    page_title="Dashboard Sales KPI + AI 🚀",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Input della chiave API tramite la barra laterale
with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")

# Verifica che la chiave API sia stata inserita
if not openai_api_key:
    st.warning("Inserisci la tua OpenAI API Key nella barra laterale per continuare.")
else:
    # Imposta la chiave API di OpenAI
    openai.api_key = openai_api_key
    st.success("Chiave API di OpenAI configurata correttamente!")

    # Resto del codice dell'applicazione

    # Titolo dell'app
    st.title("📈 Dashboard Sales KPI + AI 🚀")

    # Funzione per processare il campo 'Canale'
    def process_canale(canale):
        canale = str(canale).strip().lower()
        main_channel = canale.title()  # Valore predefinito

        # Gestione dei canali
        if 'linkedin' in canale:
            if 'in' in canale:
                main_channel = 'LinkedIn Inbound'
            elif 'out' in canale:
                main_channel = 'LinkedIn Outbound'
            else:
                main_channel = 'LinkedIn'
        elif 'advertising' in canale:
            main_channel = 'Advertising'
        elif 'eventi' in canale:
            main_channel = 'Eventi'
        elif 'referral' in canale:
            main_channel = 'Referral'
        elif 'rinnovi' in canale or 'upselling' in canale:
            main_channel = 'Rinnovi-Upselling'
        elif 'cold calling' in canale:
            main_channel = 'Cold Calling'
        elif 'sito' in canale:
            main_channel = 'Sito'
        else:
            main_channel = canale.title()

        return main_channel

    # Funzione per calcolare le metriche
    def calculate_metrics(data):
        totale_opportunita = data['Opportunity_Created'].notnull().sum()
        totale_vinti = data['Closed_Won'].notnull().sum()
        totale_persi = data['Closed_Lost'].notnull().sum()
        totale_revenue = data.loc[data['Closed_Won'].notnull(), 'Valore Tot €'].sum()
        win_rate = (totale_vinti / (totale_vinti + totale_persi)) * 100 if (totale_vinti + totale_persi) > 0 else 0
        lost_rate = (totale_persi / (totale_vinti + totale_persi)) * 100 if (totale_vinti + totale_persi) > 0 else 0

        # Tempo medio di chiusura per le opportunità vinte
        data['Days_to_Close'] = (data['Closed_Won'] - data['Opportunity_Created']).dt.days
        tempo_medio_chiusura = data.loc[data['Closed_Won'].notnull(), 'Days_to_Close'].mean()

        # ACV
        acv = data.loc[data['Closed_Won'].notnull(), 'Valore Tot €'].mean()

        # Pipeline Velocity
        pipeline_velocity = (totale_opportunita * (win_rate/100) * acv) / tempo_medio_chiusura if tempo_medio_chiusura and tempo_medio_chiusura > 0 else 0

        return {
            'totale_opportunita': totale_opportunita,
            'totale_vinti': totale_vinti,
            'totale_persi': totale_persi,
            'totale_revenue': totale_revenue,
            'win_rate': win_rate,
            'lost_rate': lost_rate,
            'tempo_medio_chiusura': tempo_medio_chiusura,
            'acv': acv,
            'pipeline_velocity': pipeline_velocity
        }

    # Funzione per generare gli insight utilizzando GPT-4o
    def generate_ai_insights(metrics, summary_df):
        # Preparazione del prompt per GPT-4o
        prompt = f"""
        Sei un assistente virtuale che analizza le performance di vendita di un'azienda. Fornisci interpretazioni qualitative basate sulle seguenti metriche:

        - Totale Opportunità Create: {metrics['totale_opportunita']}
        - Totale Opportunità Vinte: {metrics['totale_vinti']}
        - Totale Opportunità Perse: {metrics['totale_persi']}
        - Win Rate: {metrics['win_rate']:.2f}%
        - Lost Rate: {metrics['lost_rate']:.2f}%
        - Revenue Totale: €{metrics['totale_revenue']:.2f}
        - Valore Medio Contratto: €{metrics['acv']:.2f}
        - Tempo Medio di Chiusura: {metrics['tempo_medio_chiusura']:.2f} giorni
        - Pipeline Velocity: €{metrics['pipeline_velocity']:.2f}

        Analizza anche le performance per canale:

        {summary_df.to_string()}

        Fornisci un'analisi dettagliata delle performance, identificando punti di forza, aree di miglioramento e possibili azioni da intraprendere. Sii specifico e professionale nella tua risposta.
        """

        # Chiamata all'API di OpenAI
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "Sei un esperto analista di vendite."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7,
            )

            # Estrazione del testo dalla risposta
            insights = response.choices[0].message.content
            return insights

        except Exception as e:
            st.error(f"Errore durante la generazione degli insight: {e}")
            return None

    # Caricamento dati
    st.header("Caricamento dei Dati")

    # Aggiunta del pulsante per pulire la cache
    if st.button("Pulisci Cache"):
        st.cache_data.clear()
        st.success("Cache pulita con successo!")

    uploaded_file = st.file_uploader("Carica un file Excel con i dati di vendita", type=["xlsx"])
    if uploaded_file is not None:
        # Pulisce la cache prima di caricare nuovi dati
        st.cache_data.clear()

        # Ottiene i nomi dei fogli nel file Excel
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names

        # Cerca il foglio che contiene 'input' (case-insensitive)
        sheet_name = None
        for name in sheet_names:
            if 'input' in name.lower():
                sheet_name = name
                break

        if sheet_name is None:
            # Se non trova un foglio con 'input', usa il primo foglio
            sheet_name = xls.sheet_names[0]

        # Legge il foglio corretto
        data = pd.read_excel(uploaded_file, sheet_name=sheet_name)

        # Rimuove eventuali spazi nei nomi delle colonne
        data.columns = data.columns.str.strip()

        # Verifica se le colonne sono state lette correttamente
        expected_columns = ['Sales', 'Canale', 'Meeting FIssato', 'Meeting Effettuato (SQL)', 'Offerte Inviate', 'Analisi Firmate', 'Contratti Chiusi', 'Persi', 'Stato', 'Servizio', 'Valore Tot €', 'Azienda', 'Nome Persona', 'Ruolo', 'Dimensioni', 'Settore', 'Come mai ha accettato?', 'Obiezioni', 'Note']
        missing_columns = [col for col in expected_columns if col not in data.columns]
        if missing_columns:
            st.error(f"Le seguenti colonne sono mancanti nel file caricato: {', '.join(missing_columns)}")
        else:
            # Pulizia delle colonne di data
            date_columns = ['Meeting FIssato', 'Meeting Effettuato (SQL)', 'Offerte Inviate', 'Analisi Firmate', 'Contratti Chiusi', 'Persi']
            for col in date_columns:
                if col in data.columns:
                    data[col] = pd.to_datetime(data[col], dayfirst=True, errors='coerce')

            # Pulizia della colonna 'Valore Tot €'
            if 'Valore Tot €' in data.columns:
                data['Valore Tot €'] = data['Valore Tot €'].astype(str).replace({'€': '', ',': '', '\.': ''}, regex=True)
                data['Valore Tot €'] = pd.to_numeric(data['Valore Tot €'], errors='coerce').fillna(0)
            else:
                data['Valore Tot €'] = 0

            # Processamento del campo 'Canale'
            if 'Canale' in data.columns:
                data['MainChannel'] = data['Canale'].apply(process_canale)
            else:
                data['MainChannel'] = 'Unknown'

            # Aggiunta del campo 'TeamMember' dal campo 'Sales'
            if 'Sales' in data.columns:
                data['TeamMember'] = data['Sales'].str.title()
            else:
                data['TeamMember'] = None

            # Creazione delle colonne 'Opportunity_Created', 'Closed_Won', 'Closed_Lost'
            # 'Opportunity_Created' lo prendiamo da 'Meeting Effettuato (SQL)' o 'Meeting FIssato'
            data['Opportunity_Created'] = data['Meeting Effettuato (SQL)'].combine_first(data['Meeting FIssato'])

            # 'Closed_Won' lo prendiamo da 'Contratti Chiusi'
            data['Closed_Won'] = data['Contratti Chiusi']

            # 'Closed_Lost' lo prendiamo da 'Persi'
            data['Closed_Lost'] = data['Persi']

            # Aggiusta la colonna 'Stato'
            data['Stato'] = data['Stato'].fillna('In Progress')

            st.success("Dati caricati con successo!")
            if st.checkbox("Mostra dati grezzi"):
                st.subheader("Dati Grezzi")
                st.write(data)
            st.session_state['data'] = data

    else:
        st.warning("Per favore, carica un file Excel per iniziare.")

    if 'data' in st.session_state:
        data = st.session_state['data']

        # Selezione dei filtri
        st.sidebar.header("Filtri")
        # Periodo temporale specifico per mese/trimestre/anno
        periodo_temporale = st.sidebar.selectbox("Filtro Temporale", ["Intervallo Date", "Mese", "Trimestre", "Anno"])

        if periodo_temporale == "Intervallo Date":
            # Periodo temporale
            min_date = data['Opportunity_Created'].min()
            max_date = data['Opportunity_Created'].max()
            if pd.isnull(min_date) or pd.isnull(max_date):
                min_date = datetime.today()
                max_date = datetime.today()
            start_date, end_date = st.sidebar.date_input("Seleziona il periodo", [min_date, max_date])
            date_mask = (data['Opportunity_Created'] >= pd.to_datetime(start_date)) & (data['Opportunity_Created'] <= pd.to_datetime(end_date))
        elif periodo_temporale == "Mese":
            mesi = data['Opportunity_Created'].dt.to_period('M').unique().astype(str)
            selected_months = st.sidebar.multiselect("Seleziona Mese/i", mesi, default=mesi)
            date_mask = data['Opportunity_Created'].dt.to_period('M').astype(str).isin(selected_months)
        elif periodo_temporale == "Trimestre":
            trimestri = data['Opportunity_Created'].dt.to_period('Q').unique().astype(str)
            selected_quarters = st.sidebar.multiselect("Seleziona Trimestre/i", trimestri, default=trimestri)
            date_mask = data['Opportunity_Created'].dt.to_period('Q').astype(str).isin(selected_quarters)
        elif periodo_temporale == "Anno":
            anni = data['Opportunity_Created'].dt.year.unique()
            selected_years = st.sidebar.multiselect("Seleziona Anno/i", anni, default=anni)
            date_mask = data['Opportunity_Created'].dt.year.isin(selected_years)

        # Canale
        canali = data['MainChannel'].unique()
        selected_canali = st.sidebar.multiselect("Seleziona Canali", canali, default=canali)

        # Sales Rep
        sales_reps = data['TeamMember'].dropna().unique()
        selected_sales_reps = st.sidebar.multiselect("Seleziona Sales Rep", sales_reps, default=sales_reps)

        # Tipo di opportunità (Servizio)
        servizi = data['Servizio'].dropna().unique()
        selected_servizi = st.sidebar.multiselect("Seleziona Servizi", servizi, default=servizi)

        # Stato opportunità
        stati = data['Stato'].dropna().unique()
        selected_stati = st.sidebar.multiselect("Seleziona Stato Opportunità", stati, default=stati)

        # Filtro dei dati in base alle selezioni
        data_filtered = data[
            date_mask &
            (data['MainChannel'].isin(selected_canali)) &
            (data['TeamMember'].isin(selected_sales_reps)) &
            (data['Servizio'].isin(selected_servizi)) &
            (data['Stato'].isin(selected_stati))
        ]

        # Calcolo delle metriche
        metrics = calculate_metrics(data_filtered)

        # Sezione metriche chiave
    st.subheader("Key Performance Indicators")

    # Creazione di un layout a 3 colonne per i KPI
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-container">
            <div class="metric-label">Opportunità Totali</div>
            <div class="metric-value">{}</div>
        </div>
        """.format(metrics['totale_opportunita']), unsafe_allow_html=True)

        st.markdown("""
        <div class="metric-container">
            <div class="metric-label">Win Rate</div>
            <div class="metric-value">{:.2f}%</div>
        </div>
        """.format(metrics['win_rate']), unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-container">
            <div class="metric-label">Opportunità Vinte</div>
            <div class="metric-value">{}</div>
        </div>
        """.format(metrics['totale_vinti']), unsafe_allow_html=True)

        st.markdown("""
        <div class="metric-container">
            <div class="metric-label">Lost Rate</div>
            <div class="metric-value">{:.2f}%</div>
        </div>
        """.format(metrics['lost_rate']), unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-container">
            <div class="metric-label">Revenue Totale</div>
            <div class="metric-value">€{:,.2f}</div>
        </div>
        """.format(metrics['totale_revenue']), unsafe_allow_html=True)

        st.markdown("""
        <div class="metric-container">
            <div class="metric-label">Pipeline Velocity</div>
            <div class="metric-value">€{:,.2f}</div>
        </div>
        """.format(metrics['pipeline_velocity']), unsafe_allow_html=True)

        # Tabella riepilogativa
        st.subheader("Tabella Riepilogativa per Canale")

        grouping_column = 'MainChannel'
        if grouping_column in data_filtered.columns:
            summary_df = data_filtered.groupby(grouping_column).agg({
                'Opportunity_Created': 'count',
                'Closed_Lost': lambda x: x.notnull().sum(),
                'Closed_Won': lambda x: x.notnull().sum(),
                'Valore Tot €': 'sum',
                'Days_to_Close': 'mean'
            }).rename(columns={
                'Opportunity_Created': 'Opportunità Create',
                'Closed_Lost': 'Opportunità Perse',
                'Closed_Won': 'Opportunità Vinte',
                'Valore Tot €': 'Revenue Totale',
                'Days_to_Close': 'Tempo Medio di Chiusura (giorni)'
            })

            summary_df['Valore Medio Contratto'] = summary_df['Revenue Totale'] / summary_df['Opportunità Vinte']
            summary_df['Win Rate'] = (summary_df['Opportunità Vinte'] / (summary_df['Opportunità Vinte'] + summary_df['Opportunità Perse'])) * 100
            summary_df['Pipeline Velocity'] = (summary_df['Opportunità Create'] * (summary_df['Win Rate']/100) * summary_df['Valore Medio Contratto']) / summary_df['Tempo Medio di Chiusura (giorni)']
            summary_df['Pipeline Velocity'] = summary_df['Pipeline Velocity'].fillna(0)

            # Aggiunta della colonna 'Tempo Medio di Chiusura (giorni)' alle colonne da visualizzare
            columns_to_display = ['Opportunità Create', 'Opportunità Vinte', 'Opportunità Perse', 'Revenue Totale', 'Valore Medio Contratto', 'Win Rate', 'Tempo Medio di Chiusura (giorni)', 'Pipeline Velocity']

            # Formattazione dei dati
            summary_df_formatted = summary_df[columns_to_display].style.format({
                "Revenue Totale": "€{:.2f}",
                "Valore Medio Contratto": "€{:.2f}",
                "Pipeline Velocity": "€{:.2f}",
                "Win Rate": "{:.2f}%",
                "Tempo Medio di Chiusura (giorni)": "{:.2f}"
            }).highlight_max(subset=['Opportunità Create', 'Revenue Totale', 'Win Rate', 'Pipeline Velocity'], color='#d4edda').highlight_min(subset=['Tempo Medio di Chiusura (giorni)'], color='#f8d7da')

            # Visualizzazione tabella
            st.dataframe(summary_df_formatted, use_container_width=True)

            # Esportazione dati
            csv = summary_df[columns_to_display].to_csv(index=True).encode('utf-8')
            st.download_button(
                label="Scarica dati come CSV",
                data=csv,
                file_name='summary.csv',
                mime='text/csv',
                key='download_summary'
            )

        # Generazione degli insight utilizzando GPT-4o
        insights = generate_ai_insights(metrics, summary_df)

        if insights:
            st.subheader("Interpretazione delle Metriche")
            st.markdown(insights)

       

        # [Aggiungi qui il codice per le visualizzazioni grafiche]

            # Visualizzazioni grafiche
            st.subheader("Visualizzazioni Grafiche")

            # Selezione della metrica per il trend temporale
            metriche_disponibili = ['Opportunità Create', 'Opportunità Vinte', 'Opportunità Perse', 'Revenue Totale']
            metrica_selezionata = st.selectbox("Seleziona la metrica per il trend temporale", metriche_disponibili, key='metrica_trend')

            # Preparazione dei dati per il trend temporale
            if periodo_temporale == "Mese":
                data_filtered['Periodo'] = data_filtered['Opportunity_Created'].dt.to_period('M').astype(str)
            elif periodo_temporale == "Trimestre":
                data_filtered['Periodo'] = data_filtered['Opportunity_Created'].dt.to_period('Q').astype(str)
            elif periodo_temporale == "Anno":
                data_filtered['Periodo'] = data_filtered['Opportunity_Created'].dt.to_period('A').astype(str)
            else:
                data_filtered['Periodo'] = data_filtered['Opportunity_Created'].dt.to_period('D').astype(str)

            trend_df = data_filtered.groupby(['Periodo']).agg({
                'Opportunity_Created': 'count',
                'Closed_Won': lambda x: x.notnull().sum(),
                'Closed_Lost': lambda x: x.notnull().sum(),
                'Valore Tot €': 'sum'
            }).rename(columns={
                'Opportunity_Created': 'Opportunità Create',
                'Closed_Won': 'Opportunità Vinte',
                'Closed_Lost': 'Opportunità Perse',
                'Valore Tot €': 'Revenue Totale',
            }).reset_index()

            # Calcolo del Growth
            trend_df = trend_df.sort_values('Periodo')
            trend_df['Growth (%)'] = trend_df[metrica_selezionata].pct_change() * 100

            # Grafico del trend temporale
            fig_trend = px.line(trend_df, x='Periodo', y=metrica_selezionata,
                                title=f"Trend temporale di {metrica_selezionata}",
                                markers=True)
            fig_trend.update_layout(
                xaxis_title="Periodo",
                yaxis_title=metrica_selezionata,
                legend_title="",
                hovermode="x unified"
            )
            st.plotly_chart(fig_trend, use_container_width=True)

            # Grafico del Growth
            st.subheader(f"Variazione Percentuale di {metrica_selezionata}")
            fig_growth = px.bar(trend_df, x='Periodo', y='Growth (%)',
                                title=f"Variazione Percentuale di {metrica_selezionata} nel tempo",
                                color_discrete_sequence=['#007bff'])
            fig_growth.update_layout(
                xaxis_title="Periodo",
                yaxis_title="Growth (%)",
                hovermode="x unified"
            )
            st.plotly_chart(fig_growth, use_container_width=True)

            # Grafico di confronto canali
            st.subheader("Confronto tra Canali")
            metrica_canali = st.selectbox("Seleziona la metrica per il confronto canali", metriche_disponibili, index=0, key='metrica_confronto')

            confronto_df = data_filtered.groupby('MainChannel').agg({
                'Opportunity_Created': 'count',
                'Closed_Won': lambda x: x.notnull().sum(),
                'Closed_Lost': lambda x: x.notnull().sum(),
                'Valore Tot €': 'sum'
            }).rename(columns={
                'Opportunity_Created': 'Opportunità Create',
                'Closed_Won': 'Opportunità Vinte',
                'Closed_Lost': 'Opportunità Perse',
                'Valore Tot €': 'Revenue Totale',
            }).reset_index()

            # Ordinamento per valore nei grafici
            confronto_df = confronto_df.sort_values(by=metrica_canali, ascending=False)

            fig_confronto = px.bar(confronto_df, x=metrica_canali, y='MainChannel',
                                title=f"Confronto Canali - {metrica_canali}",
                                text=metrica_canali,
                                orientation='h',
                                color='MainChannel',
                                color_discrete_sequence=px.colors.qualitative.Safe)
            fig_confronto.update_layout(
                xaxis_title=metrica_canali,
                yaxis_title="Canale",
                showlegend=False,
                hovermode="y"
            )
            st.plotly_chart(fig_confronto, use_container_width=True)

            # Pipeline Funnel con breakdown per canale
            st.subheader("Pipeline Funnel")
            funnel_option = st.selectbox("Seleziona il canale per visualizzare il funnel", ['Tutti'] + list(data_filtered['MainChannel'].unique()), key='funnel_option')

            if funnel_option == 'Tutti':
                funnel_data = data_filtered
                funnel_title = "Pipeline Funnel - Tutti i Canali"
            else:
                funnel_data = data_filtered[data_filtered['MainChannel'] == funnel_option]
                funnel_title = f"Pipeline Funnel - {funnel_option}"

            funnel_stages = ['Opportunità Create', 'Opportunità Vinte', 'Opportunità Perse']
            funnel_values = [
                funnel_data['Opportunity_Created'].count(),
                funnel_data['Closed_Won'].notnull().sum(),
                funnel_data['Closed_Lost'].notnull().sum()
            ]

            # Calcolo delle percentuali per il funnel
            funnel_percentages = [f"{(value / funnel_values[0]) * 100:.2f}%" if funnel_values[0] > 0 else "0%" for value in funnel_values]

            fig_funnel = go.Figure(go.Funnel(
                y=funnel_stages,
                x=funnel_values,
                textinfo="value+percent previous",
                textposition="inside",
                texttemplate="<b>%{label}</b><br>%{value} (%{percentPrevious:.2%})"
            ))
            fig_funnel.update_layout(
                title=funnel_title,
                yaxis_title="Fase",
                xaxis_title="Numero di Opportunità"
            )
            st.plotly_chart(fig_funnel, use_container_width=True)

            # Confronti temporali
            st.subheader("Confronti Temporali")
            periodi = ['Mese', 'Trimestre', 'Anno']
            periodo_selezionato = st.selectbox("Seleziona il periodo per il confronto", periodi, key='periodo_confronto')

            if periodo_selezionato == 'Mese':
                data_filtered['Periodo'] = data_filtered['Opportunity_Created'].dt.to_period('M').astype(str)
            elif periodo_selezionato == 'Trimestre':
                data_filtered['Periodo'] = data_filtered['Opportunity_Created'].dt.to_period('Q').astype(str)
            elif periodo_selezionato == 'Anno':
                data_filtered['Periodo'] = data_filtered['Opportunity_Created'].dt.to_period('A').astype(str)

            confronto_temporale_df = data_filtered.groupby('Periodo').agg({
                'Opportunity_Created': 'count',
                'Closed_Won': lambda x: x.notnull().sum(),
                'Closed_Lost': lambda x: x.notnull().sum(),
                'Valore Tot €': 'sum'
            }).rename(columns={
                'Opportunity_Created': 'Opportunità Create',
                'Closed_Won': 'Opportunità Vinte',
                'Closed_Lost': 'Opportunità Perse',
                'Valore Tot €': 'Revenue Totale',
            }).reset_index()

            # Calcolo del Growth per ogni metrica
            confronto_temporale_df = confronto_temporale_df.sort_values('Periodo')
            for metrica in metriche_disponibili:
                confronto_temporale_df[f"{metrica} Growth (%)"] = confronto_temporale_df[metrica].pct_change() * 100

            # Grafico per il confronto temporale
            fig_confronto_temporale = px.line(confronto_temporale_df, x='Periodo', y=metriche_disponibili,
                                            title=f"Confronto Temporale delle Metriche - {periodo_selezionato}",
                                            markers=True)
            fig_confronto_temporale.update_layout(
                xaxis_title="Periodo",
                yaxis_title="Valore",
                hovermode="x unified"
            )
            st.plotly_chart(fig_confronto_temporale, use_container_width=True)

            # Zoom temporale avanzato
            st.subheader("Zoom Temporale Avanzato")
            zoom_options = ['Tutto', 'Ultimi 12 periodi', 'Ultimi 6 periodi', 'Ultimi 3 periodi']
            zoom_selection = st.selectbox("Seleziona il range temporale", zoom_options, key='zoom_selection')

            if zoom_selection == 'Tutto':
                zoom_df = trend_df
            else:
                n_periods = int(zoom_selection.split(' ')[1])
                zoom_df = trend_df.tail(n_periods)

            fig_zoom = px.line(zoom_df, x='Periodo', y=metrica_selezionata,
                            title=f"{metrica_selezionata} - {zoom_selection}",
                            markers=True)
            fig_zoom.update_layout(
                xaxis_title="Periodo",
                yaxis_title=metrica_selezionata,
                hovermode="x unified"
            )
            st.plotly_chart(fig_zoom, use_container_width=True)

        else:
            st.warning("Per favore, carica i dati nella sezione 'Caricamento Dati' per continuare.")


        # Footer
        st.markdown("""
            <hr>
            <div style='text-align: center; color: #888888;'>
                © 2024 - Boosha AI + Result Consulting.
            </div>
            """, unsafe_allow_html=True)
