import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configurazione della pagina
st.set_page_config(
    page_title="Dashboard Avanzata di Monitoraggio Vendite con AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Stile personalizzato in linea con il branding fornito
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
st.title("📈 Dashboard Avanzata di Monitoraggio Vendite con AI")

# Barra laterale per la navigazione
st.sidebar.title("Navigazione")
sezione = st.sidebar.radio("Vai a:", ["Caricamento Dati", "Dashboard"])

# Caricamento dati
if sezione == "Caricamento Dati":
    st.header("Caricamento dei Dati")
    uploaded_file = st.file_uploader("Carica un file Excel con i dati di vendita", type=["xlsx"])
    if uploaded_file is not None:
        data = pd.read_excel(uploaded_file, sheet_name='🚀INPUT')
        
        # Pulizia colonne rilevanti
        data.columns = data.columns.str.strip()
        data['Meeting FIssato'] = pd.to_datetime(data['Meeting FIssato'], errors='coerce')
        data['Contratti Chiusi'] = pd.to_datetime(data['Contratti Chiusi'], errors='coerce')
        data['Persi'] = pd.to_datetime(data['Persi'], errors='coerce')
        data['Valore Tot €'] = pd.to_numeric(data['Valore Tot €'], errors='coerce').fillna(0)

        st.success("Dati caricati con successo!")
        if st.checkbox("Mostra dati grezzi"):
            st.subheader("Dati Grezzi")
            st.write(data)
        st.session_state['data'] = data

    else:
        st.warning("Per favore, carica un file Excel per iniziare.")

elif 'data' in st.session_state:
    data = st.session_state['data']

    # Calcolo delle metriche chiave
    totale_opportunita = data['Meeting FIssato'].notnull().sum()
    totale_vinti = data['Contratti Chiusi'].notnull().sum()
    totale_persi = data['Persi'].notnull().sum()
    totale_revenue = data['Valore Tot €'].sum()
    win_rate = (totale_vinti / totale_opportunita) * 100 if totale_opportunita > 0 else 0
    lost_rate = (totale_persi / totale_opportunita) * 100 if totale_opportunita > 0 else 0

    # Tempo medio di chiusura per le opportunità vinte
    data['Days_to_Close'] = (data['Contratti Chiusi'] - data['Meeting FIssato']).dt.days
    tempo_medio_chiusura = data.loc[data['Contratti Chiusi'].notnull(), 'Days_to_Close'].mean()
    
    # Pipeline Velocity (Velocità della pipeline)
    pipeline_velocity = totale_revenue / tempo_medio_chiusura if tempo_medio_chiusura > 0 else 0
    
    # Contributo percentuale alla pipeline per canale
    revenue_per_canale = data.groupby('Canale')['Valore Tot €'].sum()
    percentuale_contributo = (revenue_per_canale / totale_revenue) * 100

    # ACV (Average Contract Value) per canale
    acv_per_canale = revenue_per_canale / data[data['Contratti Chiusi'].notnull()].groupby('Canale').size()
    acv_per_canale = acv_per_canale.fillna(0)  # Gestione dei valori NaN

    # Tabella riepilogativa per Canale
    st.header("Dashboard")
    st.subheader("Tabella Riepilogativa per Canale")
    summary_df = pd.DataFrame({
        'Source': revenue_per_canale.index,
        'Total Opps. created': data.groupby('Canale').size(),
        'Total Closed Lost Opps.': data[data['Persi'].notnull()].groupby('Canale').size(),
        'Total Closed Won Opps.': data[data['Contratti Chiusi'].notnull()].groupby('Canale').size(),
        'Total Closed Won Revenue': revenue_per_canale,
        'ACV': acv_per_canale,
        'Closed Won Avg. Sales Cycle': data[data['Contratti Chiusi'].notnull()].groupby('Canale')['Days_to_Close'].mean(),
        'Win-Rate': (data[data['Contratti Chiusi'].notnull()].groupby('Canale').size() / data.groupby('Canale').size()) * 100,
        'Pipeline Velocity': pipeline_velocity,
        '% of pipeline contribution': percentuale_contributo
    }).reset_index(drop=True)
    st.write(summary_df)

    # Sezione metriche chiave
    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Opportunità Totali", totale_opportunita)
    col2.metric("Opportunità Vinte", totale_vinti)
    col3.metric("Opportunità Perse", totale_persi)
    col4.metric("Revenue Totale", f"€{totale_revenue:,.2f}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Win Rate", f"{win_rate:.2f}%")
    col2.metric("Lost Rate", f"{lost_rate:.2f}%")
    col3.metric("Tempo Medio di Chiusura (giorni)", f"{tempo_medio_chiusura:.2f}")
    col4.metric("Pipeline Velocity", f"€{pipeline_velocity:,.2f}")

    # Visualizzazione grafici interattivi
    # Grafico a barre delle opportunità chiuse per canale
    st.subheader("Opportunità Chiuse per Canale")
    closed_opps = data[data['Contratti Chiusi'].notnull()]
    closed_opps_count = closed_opps.groupby('Canale').size().reset_index(name='Opportunità Chiuse')
    fig1 = px.bar(closed_opps_count, x='Canale', y='Opportunità Chiuse', title="Opportunità Chiuse per Canale", color='Canale', color_discrete_sequence=px.colors.sequential.Blues)
    st.plotly_chart(fig1, use_container_width=True)

    # Grafico a torta per la percentuale di contributo per canale
    st.subheader("Contributo Percentuale alla Pipeline per Canale")
    fig2 = px.pie(summary_df, values='% of pipeline contribution', names='Source', title='Contributo Percentuale alla Pipeline')
    st.plotly_chart(fig2, use_container_width=True)

    # Grafico a barre
        # Grafico a barre per Revenue per Servizio
    st.subheader("Revenue per Servizio")
    revenue_servizio_df = data.groupby('Servizio')['Valore Tot €'].sum().reset_index()
    fig3 = px.bar(revenue_servizio_df, x='Servizio', y='Valore Tot €', title="Revenue per Servizio", color='Servizio', color_discrete_sequence=px.colors.sequential.Blues)
    st.plotly_chart(fig3, use_container_width=True)

    # Distribuzione dei Valori dei Contratti (Istogramma)
    st.subheader("Distribuzione dei Valori dei Contratti")
    fig4 = px.histogram(data[data['Valore Tot €'] > 0], x='Valore Tot €', nbins=20, title="Distribuzione dei Valori dei Contratti", color_discrete_sequence=['#007aff'])
    st.plotly_chart(fig4, use_container_width=True)

    # Andamento Mensile delle Opportunità e delle Revenue
    st.subheader("Andamento Mensile delle Opportunità e delle Revenue")
    data['Mese'] = data['Contratti Chiusi'].dt.to_period('M').astype(str)
    monthly_revenue = data.groupby('Mese')['Valore Tot €'].sum().reset_index()
    monthly_opportunities = data.groupby('Mese').size().reset_index(name='Opportunità Totali')
    
    fig5 = px.line(monthly_revenue, x='Mese', y='Valore Tot €', title="Andamento Mensile delle Revenue", markers=True, line_shape='linear', color_discrete_sequence=['#007aff'])
    fig5.update_layout(yaxis_title="Revenue (€)")
    st.plotly_chart(fig5, use_container_width=True)
    
    fig6 = px.line(monthly_opportunities, x='Mese', y='Opportunità Totali', title="Andamento Mensile delle Opportunità", markers=True, line_shape='linear', color_discrete_sequence=['#ff7f0e'])
    fig6.update_layout(yaxis_title="Opportunità Totali")
    st.plotly_chart(fig6, use_container_width=True)

    # Conversion Rate per Fase della Pipeline
    st.subheader("Conversion Rate per Fase della Pipeline")
    pipeline_stages = ['Meeting FIssato', 'Offerte Inviate', 'Analisi Firmate', 'Contratti Chiusi']
    conversion_rates = {
        stage: (data[stage].notnull().sum() / totale_opportunita) * 100 if totale_opportunita > 0 else 0
        for stage in pipeline_stages
    }
    conversion_df = pd.DataFrame(list(conversion_rates.items()), columns=['Fase', 'Conversion Rate (%)'])
    fig7 = px.bar(conversion_df, x='Fase', y='Conversion Rate (%)', title="Conversion Rate per Fase della Pipeline", color='Fase', color_discrete_sequence=px.colors.sequential.Blues)
    st.plotly_chart(fig7, use_container_width=True)

else:
    st.warning("Per favore, carica i dati nella sezione 'Caricamento Dati' per continuare.")

# Footer
st.markdown("""
    <hr>
    <div style='text-align: center; color: #888888;'>
        © 2024 - Boosha 
    </div>
    """, unsafe_allow_html=True)

