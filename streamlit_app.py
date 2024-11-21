import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sklearn.linear_model import LinearRegression

# Configurazione della pagina
st.set_page_config(
    page_title="Dashboard Sales KPI + AI 🚀",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Stile personalizzato
st.markdown("""
    <style>
    /* Font e colori */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        background-color: #ffffff;
        color: #333333;
    }

    /* Stile delle metriche */
    .stMetricLabel, .stMetricValue {
        color: #007aff;
    }

    /* Pulsanti e interattività */
    .stButton>button {
        color: #ffffff;
        background-color: #007aff;
        border-radius: 8px;
        height: 3em;
        font-size: 16px;
    }

    </style>
    """, unsafe_allow_html=True)

# Titolo dell'app
st.title("📈 Dashboard Sales KPI + AI 🚀")

# Barra laterale per la navigazione e filtri
st.sidebar.title("Filtri")

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
    # Periodo temporale
    min_date = data['Opportunity_Created'].min()
    max_date = data['Opportunity_Created'].max()
    if pd.isnull(min_date) or pd.isnull(max_date):
        min_date = datetime.today()
        max_date = datetime.today()
    start_date, end_date = st.sidebar.date_input("Seleziona il periodo", [min_date, max_date])

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
        (data['Opportunity_Created'] >= pd.to_datetime(start_date)) &
        (data['Opportunity_Created'] <= pd.to_datetime(end_date)) &
        (data['MainChannel'].isin(selected_canali)) &
        (data['TeamMember'].isin(selected_sales_reps)) &
        (data['Servizio'].isin(selected_servizi)) &
        (data['Stato'].isin(selected_stati))
    ]

    # Calcolo delle metriche
    metrics = calculate_metrics(data_filtered)

    # Sezione metriche chiave
    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Opportunità Totali", metrics['totale_opportunita'])
    col2.metric("Opportunità Vinte", metrics['totale_vinti'])
    col3.metric("Opportunità Perse", metrics['totale_persi'])
    col4.metric("Revenue Totale", f"€{metrics['totale_revenue']:,.2f}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Win Rate", f"{metrics['win_rate']:.2f}%")
    col2.metric("Lost Rate", f"{metrics['lost_rate']:.2f}%")
    col3.metric("Tempo Medio di Chiusura (giorni)", f"{metrics['tempo_medio_chiusura']:.2f}" if not np.isnan(metrics['tempo_medio_chiusura']) else "N/A")
    col4.metric("Pipeline Velocity", f"€{metrics['pipeline_velocity']:,.2f}" if not np.isnan(metrics['pipeline_velocity']) else "N/A")

    # Tabella riepilogativa
    st.subheader("Tabella Riepilogativa")

    grouping_column = 'MainChannel'
    if grouping_column in data_filtered.columns:
        summary_df = data_filtered.groupby(grouping_column).agg({
            'Opportunity_Created': 'count',
            'Closed_Lost': lambda x: x.notnull().sum(),
            'Closed_Won': lambda x: x.notnull().sum(),
            'Valore Tot €': 'sum',
            'Days_to_Close': 'mean'
        }).rename(columns={
            'Opportunity_Created': 'Total Opportunities Created',
            'Closed_Lost': 'Total Closed Lost Opportunities',
            'Closed_Won': 'Total Closed Won Opportunities',
            'Valore Tot €': 'Total Closed Won Revenue',
            'Days_to_Close': 'Closed Won Avg. Sales Cycle'
        })

        summary_df['Average Contract Value'] = summary_df['Total Closed Won Revenue'] / summary_df['Total Closed Won Opportunities']
        summary_df['Win Rate'] = (summary_df['Total Closed Won Opportunities'] / (summary_df['Total Closed Won Opportunities'] + summary_df['Total Closed Lost Opportunities'])) * 100
        summary_df['Pipeline Velocity'] = (summary_df['Total Opportunities Created'] * (summary_df['Win Rate']/100) * summary_df['Average Contract Value']) / summary_df['Closed Won Avg. Sales Cycle']
        summary_df['Pipeline Velocity'] = summary_df['Pipeline Velocity'].fillna(0)

        # Funzionalità di ordinamento
        sort_by = st.selectbox("Ordina per", summary_df.columns, index=0)
        summary_df = summary_df.sort_values(by=sort_by, ascending=False)

        # Esportazione dati
        csv = summary_df.to_csv(index=True).encode('utf-8')
        st.download_button(
            label="Scarica dati come CSV",
            data=csv,
            file_name='summary.csv',
            mime='text/csv',
        )

        # Visualizzazione tabella
        st.dataframe(summary_df.style.format({
            "Total Closed Won Revenue": "€{:.2f}",
            "Average Contract Value": "€{:.2f}",
            "Pipeline Velocity": "€{:.2f}",
            "Win Rate": "{:.2f}%",
            "Closed Won Avg. Sales Cycle": "{:.2f}"
        }))

    # Visualizzazioni grafiche
    st.subheader("Visualizzazioni Grafiche")

    # Selezione della metrica per il trend temporale
    metriche_disponibili = ['Total Opportunities Created', 'Total Closed Won Opportunities', 'Total Closed Lost Opportunities', 'Total Closed Won Revenue']
    metrica_selezionata = st.selectbox("Seleziona la metrica per il trend temporale", metriche_disponibili)

    # Preparazione dei dati per il trend temporale
    data_filtered['Mese'] = data_filtered['Opportunity_Created'].dt.to_period('M').astype(str)
    trend_df = data_filtered.groupby(['Mese', 'MainChannel']).agg({
        'Opportunity_Created': 'count',
        'Closed_Won': lambda x: x.notnull().sum(),
        'Closed_Lost': lambda x: x.notnull().sum(),
        'Valore Tot €': 'sum'
    }).rename(columns={
        'Opportunity_Created': 'Total Opportunities Created',
        'Closed_Won': 'Total Closed Won Opportunities',
        'Closed_Lost': 'Total Closed Lost Opportunities',
        'Valore Tot €': 'Total Closed Won Revenue',
    }).reset_index()

    # Calcolo del Month-over-Month Growth
    trend_df = trend_df.sort_values('Mese')
    trend_df['Month-over-Month Growth'] = trend_df.groupby('MainChannel')[metrica_selezionata].pct_change() * 100

    # Grafico del trend temporale
    fig_trend = px.line(trend_df, x='Mese', y=metrica_selezionata, color='MainChannel',
                        title=f"Trend temporale di {metrica_selezionata}",
                        markers=True)
    st.plotly_chart(fig_trend, use_container_width=True)

    # Grafico del Month-over-Month Growth
    st.subheader("Month-over-Month Growth")
    fig_mom = px.bar(trend_df, x='Mese', y='Month-over-Month Growth', color='MainChannel',
                     title=f"Month-over-Month Growth di {metrica_selezionata}")
    st.plotly_chart(fig_mom, use_container_width=True)

    # Grafico di confronto canali
    st.subheader("Confronto tra Canali")
    metrica_canali = st.selectbox("Seleziona la metrica per il confronto canali", metriche_disponibili, index=0, key='metrica_canali')

    confronto_df = data_filtered.groupby('MainChannel').agg({
        'Opportunity_Created': 'count',
        'Closed_Won': lambda x: x.notnull().sum(),
        'Closed_Lost': lambda x: x.notnull().sum(),
        'Valore Tot €': 'sum'
    }).rename(columns={
        'Opportunity_Created': 'Total Opportunities Created',
        'Closed_Won': 'Total Closed Won Opportunities',
        'Closed_Lost': 'Total Closed Lost Opportunities',
        'Valore Tot €': 'Total Closed Won Revenue',
    }).reset_index()

    fig_confronto = px.bar(confronto_df, x='MainChannel', y=metrica_canali, color='MainChannel',
                           title=f"Confronto Canali - {metrica_canali}",
                           text=metrica_canali)
    st.plotly_chart(fig_confronto, use_container_width=True)

    # Pipeline Funnel
    st.subheader("Pipeline Funnel")
    funnel_stages = ['Total Opportunities Created', 'Total Closed Won Opportunities', 'Total Closed Lost Opportunities']
    funnel_values = [
        data_filtered['Opportunity_Created'].count(),
        data_filtered['Closed_Won'].notnull().sum(),
        data_filtered['Closed_Lost'].notnull().sum()
    ]
    fig_funnel = go.Figure(go.Funnel(
        y=funnel_stages,
        x=funnel_values,
        textinfo="value+percent initial"))
    fig_funnel.update_layout(title="Pipeline Funnel")
    st.plotly_chart(fig_funnel, use_container_width=True)

    # Confronti temporali
    st.subheader("Confronti Temporali")
    periodi = ['Mese', 'Trimestre', 'Anno']
    periodo_selezionato = st.selectbox("Seleziona il periodo per il confronto", periodi)

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
        'Opportunity_Created': 'Total Opportunities Created',
        'Closed_Won': 'Total Closed Won Opportunities',
        'Closed_Lost': 'Total Closed Lost Opportunities',
        'Valore Tot €': 'Total Closed Won Revenue',
    }).reset_index()

    # Calcolo del Month-over-Month Growth per ogni metrica
    confronto_temporale_df = confronto_temporale_df.sort_values('Periodo')
    for metrica in metriche_disponibili:
        confronto_temporale_df[f"{metrica} MoM Growth (%)"] = confronto_temporale_df[metrica].pct_change() * 100

    # Grafico per il confronto temporale
    fig_confronto_temporale = px.bar(confronto_temporale_df, x='Periodo', y=metriche_disponibili, barmode='group',
                                     title=f"Confronto Temporale - {periodo_selezionato}")
    st.plotly_chart(fig_confronto_temporale, use_container_width=True)

    # Visualizzazione del MoM Growth
    st.subheader("Month-over-Month Growth per Metriche Principali")
    metrica_mom = st.selectbox("Seleziona la metrica per visualizzare il MoM Growth", metriche_disponibili)
    fig_mom_temporale = px.line(confronto_temporale_df, x='Periodo', y=f"{metrica_mom} MoM Growth (%)",
                                title=f"MoM Growth di {metrica_mom}",
                                markers=True)
    st.plotly_chart(fig_mom_temporale, use_container_width=True)

else:
    st.warning("Per favore, carica i dati nella sezione 'Caricamento Dati' per continuare.")

# Footer
st.markdown("""
    <hr>
    <div style='text-align: center; color: #888888;'>
        © 2024 - Boosha AI + Result Consulting.
    </div>
    """, unsafe_allow_html=True)
