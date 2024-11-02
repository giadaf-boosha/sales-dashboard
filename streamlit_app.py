import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
import plotly.express as px
import plotly.graph_objects as go

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

    /* Intestazioni */
    .stHeader {
        color: #333333;
    }

    /* Caselle di testo e selezione */
    .stTextInput>div>div>input, .stSelectbox>div>div>div>input {
        border-radius: 8px;
    }

    /* Messaggi di successo e avviso */
    .stAlert {
        border-radius: 8px;
    }

    /* Grafici */
    .css-1aumxhk {
        background-color: #ffffff;
        border-radius: 8px;
    }

    /* Sidebar */
    .css-1d391kg {
        background-color: #f7f7f7;
    }

    /* Separatori */
    hr {
        border: 0;
        border-top: 1px solid #cccccc;
    }

    </style>
    """, unsafe_allow_html=True)

# Titolo dell'app
st.title("📈 Dashboard Avanzata di Monitoraggio Vendite con AI")

# Barra laterale per la navigazione
st.sidebar.title("Navigazione")
sezione = st.sidebar.radio("Vai a:", ["Caricamento Dati", "Dashboard", "AI Descrittiva", "AI Predittiva", "Consulenza Strategica"])

# Caricamento dati
if sezione == "Caricamento Dati":
    st.header("Caricamento dei Dati")
    uploaded_file = st.file_uploader("Carica un file Excel con i dati di vendita", type=["xlsx"])
    if uploaded_file is not None:
        data = pd.read_excel(uploaded_file, sheet_name='🚀INPUT')
        
        # Definisci le colonne richieste e imposta valori di default a 0 se mancanti
        required_columns = ['Sales', 'Canale', 'Meeting Fissato', 'Meeting Effettuato (SQL)', 'Offerte Inviate',
                            'Analisi Firmate', 'Contratti Chiusi', 'Persi', 'Nome Persona', 'Ruolo', 'Azienda',
                            'Dimensioni', 'Settore', 'Come mai ha accettato?', 'SQL', 'Stato', 'Servizio',
                            'Valore Tot €', 'Obiezioni', 'Note']
        
        for column in required_columns:
            if column not in data.columns:
                data[column] = 0

        st.success("Dati caricati con successo!")
        if st.checkbox("Mostra dati grezzi"):
            st.subheader("Dati Grezzi")
            st.write(data)
        st.session_state['data'] = data

    else:
        st.warning("Per favore, carica un file Excel per iniziare.")

elif 'data' in st.session_state:
    data = st.session_state['data']

    # Calcola le colonne derivate per la tabella riepilogativa
    data['Total Opps. created'] = data['Meeting Fissato'].notnull().astype(int)
    data['Total Closed Lost Opps.'] = data['Persi'].notnull().astype(int)
    data['Total Closed Won Opps.'] = data['Contratti Chiusi'].notnull().astype(int)
    data['ACV'] = data['Valore Tot €']
    data['% of pipeline contribution'] = (data['Valore Tot €'] / data['Valore Tot €'].sum()) * 100
    summary_df = data.groupby('Canale').agg({
        'Total Opps. created': 'sum',
        'Total Closed Lost Opps.': 'sum',
        'Total Closed Won Opps.': 'sum',
        'ACV': 'sum',
        '% of pipeline contribution': 'sum'
    }).reset_index()

    # Visualizza la tabella riepilogativa
    if sezione == "Dashboard":
        st.header("Dashboard")
        st.subheader("Tabella Riepilogativa")
        st.write(summary_df)

        # Visualizzazione delle metriche chiave
        st.subheader("Key Metrics")
        totale_opportunita = summary_df['Total Opps. created'].sum()
        totale_persi = summary_df['Total Closed Lost Opps.'].sum()
        totale_vinti = summary_df['Total Closed Won Opps.'].sum()
        totale_revenue = summary_df['ACV'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Opportunità Totali", totale_opportunita)
        col2.metric("Opportunità Perse", totale_persi)
        col3.metric("Opportunità Vinte", totale_vinti)
        col4.metric("Revenue Totale", f"€{totale_revenue:,.2f}")

        # Grafico a barre delle opportunità chiuse per canale
        st.subheader("Opportunità Chiuse per Canale")
        fig = px.bar(summary_df, x='Canale', y='Total Closed Won Opps.', title="Opportunità Chiuse per Canale", color='Canale')
        st.plotly_chart(fig, use_container_width=True)

        # Grafico a torta della percentuale di contributo per canale
        st.subheader("Contributo Percentuale alla Pipeline")
        fig2 = px.pie(summary_df, values='% of pipeline contribution', names='Canale', title='Contributo Percentuale alla Pipeline')
        st.plotly_chart(fig2, use_container_width=True)

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

