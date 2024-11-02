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

# Aggiunta di stile personalizzato
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

    /* Caricamento file */
    .css-1y4p8pa {
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
        # Leggi il file Excel
        data = pd.read_excel(uploaded_file, sheet_name='🚀INPUT')  # Carica il foglio '🚀INPUT'
        
        # Definisci le colonne richieste e imposta valori di default a 0 se mancanti
        required_columns = ['Sales', 'Canale', 'Meeting Fissato', 'Meeting Effettuato (SQL)', 'Offerte Inviate',
                            'Analisi Firmate', 'Contratti Chiusi', 'Persi', 'Nome Persona', 'Ruolo', 'Azienda',
                            'Dimensioni', 'Settore', 'Come mai ha accettato?', 'SQL', 'Stato', 'Servizio',
                            'Valore Tot €', 'Obiezioni', 'Note']
        
        # Aggiungi le colonne mancanti con valore di default 0
        for column in required_columns:
            if column not in data.columns:
                data[column] = 0

        # Messaggio di successo e anteprima dati
        st.success("Dati caricati con successo!")
        if st.checkbox("Mostra dati grezzi"):
            st.subheader("Dati Grezzi")
            st.write(data)
        st.session_state['data'] = data

    else:
        st.warning("Per favore, carica un file Excel per iniziare.")

elif 'data' in st.session_state:
    data = st.session_state['data']

    # Preprocessamento dei dati
    date_columns = ['Meeting Fissato', 'Meeting Effettuato (SQL)', 'Offerte Inviate',
                    'Analisi Firmate', 'Contratti Chiusi']
    for col in date_columns:
        data[col] = pd.to_datetime(data[col], errors='coerce', dayfirst=True)

    # Calcolo delle metriche globali
    data['Valore Tot €'] = pd.to_numeric(data['Valore Tot €'], errors='coerce')
    vendite_totali = data['Valore Tot €'].sum()
    totale_lead = data['Meeting Fissato'].notnull().sum()
    totale_conversioni = data['Contratti Chiusi'].notnull().sum()
    conversion_rate = (totale_conversioni / totale_lead) * 100 if totale_lead > 0 else 0
    canali_perf = data[data['Contratti Chiusi'].notnull()].groupby('Canale').size().reset_index(name='Conversioni')
    pipeline_stages = ['Meeting Fissato', 'Meeting Effettuato (SQL)', 'Offerte Inviate', 'Analisi Firmate', 'Contratti Chiusi']
    pipeline_counts = {stage: data[stage].notnull().sum() for stage in pipeline_stages}
    totale_clienti = data['Azienda'].nunique()
    clienti_persi = data['Persi'].notnull().sum()
    churn_rate = (clienti_persi / totale_clienti) * 100 if totale_clienti > 0 else 0

    # Salva le metriche in session_state
    st.session_state['vendite_totali'] = vendite_totali
    st.session_state['totale_lead'] = totale_lead
    st.session_state['totale_conversioni'] = totale_conversioni
    st.session_state['conversion_rate'] = conversion_rate
    st.session_state['canali_perf'] = canali_perf
    st.session_state['pipeline_counts'] = pipeline_counts
    st.session_state['churn_rate'] = churn_rate

    # Sezione Dashboard
    if sezione == "Dashboard":
        st.header("Dashboard")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("Prestazioni di Vendita")
            st.metric(label="Vendite Totali", value=f"€ {vendite_totali:,.2f}")
            data['Mese'] = data['Contratti Chiusi'].dt.to_period('M')
            vendite_mensili = data.groupby('Mese')['Valore Tot €'].sum().reset_index()
            vendite_mensili['Mese'] = vendite_mensili['Mese'].astype(str)
            fig = px.bar(vendite_mensili, x='Mese', y='Valore Tot €', title="Vendite per Mese", color_discrete_sequence=['#007aff'])
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Conversioni e Lead")
            st.metric(label="Leads Generati", value=int(totale_lead))
            st.metric(label="Conversion Rate", value=f"{conversion_rate:.2f}%")
            fig2 = px.pie(canali_perf, values='Conversioni', names='Canale', title='Canali di Acquisizione più Performanti', color_discrete_sequence=px.colors.sequential.Blues)
            st.plotly_chart(fig2, use_container_width=True)

        with col3:
            st.subheader("Customer Retention e Churn Rate")
            st.metric(label="Customer Retention", value=f"{100 - churn_rate:.2f}%")
            st.metric(label="Churn Rate", value=f"{churn_rate:.2f}%")
            fig3 = go.Figure(go.Indicator(mode="gauge+number", value=churn_rate, title={'text': "Churn Rate"}, gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#ff3b30"}, 'steps': [{'range': [0, 25], 'color': '#34c759'}, {'range': [25, 50], 'color': '#ffcc00'}, {'range': [50, 100], 'color': '#ff3b30'}]}))
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("---")
        st.subheader("Gestione Pipeline")
        pipeline_df = pd.DataFrame(list(pipeline_counts.items()), columns=['Fase', 'Leads'])
        pipeline_df = pipeline_df.sort_values(by='Leads', ascending=False)
                # Continuazione della gestione Pipeline
        fig4 = px.funnel(pipeline_df, x='Leads', y='Fase', title='Pipeline di Vendita', color='Fase', color_discrete_sequence=px.colors.sequential.Blues)
        st.plotly_chart(fig4, use_container_width=True)
        
        # Creazione della heatmap per visualizzare le vendite per canale e mese
        st.subheader("Mappe di Calore dei Canali di Vendita")
        data['Mese'] = data['Mese'].astype(str)
        heatmap_data = data.pivot_table(values='Valore Tot €', index='Canale', columns='Mese', aggfunc='sum')
        fig5, ax5 = plt.subplots(figsize=(10, 6))
        sns.heatmap(heatmap_data, annot=True, fmt=".2f", cmap='Blues', ax=ax5)
        ax5.set_title("Vendite per Canale e Mese", fontsize=16, fontweight='bold')
        st.pyplot(fig5)

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

