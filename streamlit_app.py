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

# Stile personalizzato
st.markdown("""
    <style>
    /* Font e colori */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        background-color: #ffffff;
    }

    /* Titoli */
    .css-18e3th9 {
        color: #333333;
    }

    /* Pulsanti */
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

    # Revenue per Servizio
    revenue_per_servizio = data.groupby('Servizio')['Valore Tot €'].sum()

    # Visualizzazione delle metriche chiave nella dashboard
    if sezione == "Dashboard":
        st.header("Dashboard")
        
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

        # Tabella riepilogativa per Canale
        st.subheader("Tabella Riepilogativa per Canale")
        summary_df = pd.DataFrame({
            'Total Revenue': revenue_per_canale,
            '% of Pipeline Contribution': percentuale_contributo
        }).reset_index()
        st.write(summary_df)

        # Visualizzazione grafici interattivi
        # Grafico a barre delle opportunità chiuse per canale
        st.subheader("Opportunità Chiuse per Canale")
        closed_opps = data[data['Contratti Chiusi'].notnull()]
        closed_opps_count = closed_opps.groupby('Canale').size().reset_index(name='Opportunità Chiuse')
        fig1 = px.bar(closed_opps_count, x='Canale', y='Opportunità Chiuse', title="Opportunità Chiuse per Canale", color='Canale')
        st.plotly_chart(fig1, use_container_width=True)

        # Grafico a torta per la percentuale di contributo per canale
        st.subheader("Contributo Percentuale alla Pipeline per Canale")
        fig2 = px.pie(summary_df, values='% of Pipeline Contribution', names='Canale', title='Contributo Percentuale alla Pipeline')
        st.plotly_chart(fig2, use_container_width=True)

        # Grafico a barre per Revenue per Servizio
        st.subheader("Revenue per Servizio")
        revenue_servizio_df = revenue_per_servizio.reset_index()
        fig3 = px.bar(revenue_servizio_df, x='Servizio', y='Valore Tot €', title="Revenue per Servizio", color='Servizio')
        st.plotly_chart(fig3, use_container_width=True)


    elif sezione == "AI Descrittiva":
        st.header("Modulo AI Descrittiva")
        domanda = st.text_input("Fai una domanda sui dati di vendita")
        if domanda:
            risposta = ""
            if "quante vendite" in domanda.lower():
                risposta = f"Il totale delle vendite è € {vendite_totali:,.2f}"
            elif "canali di vendita" in domanda.lower():
                canali = data['Canale'].unique()
                risposta = f"I principali canali di vendita sono: {', '.join(canali)}"
            elif "churn rate" in domanda.lower():
                risposta = f"Il churn rate è {churn_rate:.2f}%"
            elif "conversion rate" in domanda.lower():
                risposta = f"Il tasso di conversione è {conversion_rate:.2f}%"
            else:
                risposta = "Non ho una risposta precisa a questa domanda al momento."
            st.write(risposta)

    elif sezione == "AI Predittiva":
        st.header("Modulo AI Predittivo")
        st.write("Previsioni di vendita per i prossimi 3 mesi")
        df_pred = data.dropna(subset=['Contratti Chiusi', 'Valore Tot €'])
        df_pred = df_pred.sort_values('Contratti Chiusi')
        df_pred['DataOrdinal'] = df_pred['Contratti Chiusi'].map(pd.Timestamp.toordinal)
        X = df_pred[['DataOrdinal']]
        y = df_pred['Valore Tot €']
        if len(X) > 1:
            model = LinearRegression()
            model.fit(X, y)
            last_date = df_pred['Contratti Chiusi'].max()
            future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=90, freq='D')
            future_dates_ordinal = future_dates.map(pd.Timestamp.toordinal).values.reshape(-1, 1)
            predictions = model.predict(future_dates_ordinal)
            future_df = pd.DataFrame({'Contratti Chiusi': future_dates, 'Valore Tot €': predictions})
            combined_df = pd.concat([df_pred[['Contratti Chiusi', 'Valore Tot €']], future_df])
            fig6 = px.line(combined_df, x='Contratti Chiusi', y='Valore Tot €', title="Vendite Storiche e Previsioni Future", color_discrete_sequence=['#007aff'])
            st.plotly_chart(fig6, use_container_width=True)
        else:
            st.warning("Dati insufficienti per effettuare una previsione.")

    elif sezione == "Consulenza Strategica":
        st.header("Modulo AI Consulenza Strategica")
        st.write("Analisi dei dati per fornire consigli strategici personalizzati.")
        if st.button("Genera consigli strategici"):
            consigli = []
            if not canali_perf.empty:
                top_canale = canali_perf.loc[canali_perf['Conversioni'].idxmax()]['Canale']
                consigli.append(f"**Suggerimento:** Investi maggiormente nel canale '{top_canale}' che mostra le migliori performance in termini di conversioni.")
            if churn_rate > 30:
                consigli.append("**Consiglio:** Il churn rate è elevato. Implementa programmi di fidelizzazione per migliorare la customer retention.")
            else:
                consigli.append("**Consiglio:** Il churn rate è sotto controllo. Continua a monitorare la soddisfazione dei clienti.")
            if conversion_rate < 20:
                consigli.append("**Consiglio:** Il tasso di conversione è basso. Valuta di ottimizzare le strategie di vendita e formazione del team.")
            else:
                consigli.append("**Suggerimento:** Mantieni le attuali strategie di conversione che stanno dando buoni risultati.")
            for consiglio in consigli:
                st.write(consiglio)

else:
    st.warning("Per favore, carica i dati nella sezione 'Caricamento Dati' per continuare.")

# Footer
st.markdown("""
    <hr>
    <div style='text-align: center; color: #888888;'>
        © 2024 - Boosha 
    </div>
    """, unsafe_allow_html=True)

