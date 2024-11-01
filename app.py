import openpyxl
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
        data = pd.read_excel(uploaded_file)

        # Controllo delle colonne necessarie
        required_columns = ['Data', 'Vendite', 'Leads', 'Conversioni', 'Canale', 'Fase', 'Cliente', 'Abbandono']
        if all(column in data.columns for column in required_columns):
            st.success("Dati caricati con successo!")
            # Mostra i dati
            if st.checkbox("Mostra dati grezzi"):
                st.subheader("Dati Grezzi")
                st.write(data)
            st.session_state['data'] = data
        else:
            st.error(f"Il file deve contenere le seguenti colonne: {', '.join(required_columns)}")
    else:
        st.warning("Per favore, carica un file Excel per iniziare.")

elif 'data' in st.session_state:
    data = st.session_state['data']

    # Calcolo delle metriche globali da usare in diverse sezioni
    # Converti 'Data' in datetime
    data['Data'] = pd.to_datetime(data['Data'])

    # Calcolo di churn_rate
    totale_clienti = data['Cliente'].nunique()
    clienti_persi = data[data['Abbandono'] == True]['Cliente'].nunique()
    churn_rate = (clienti_persi / totale_clienti) * 100 if totale_clienti > 0 else 0
    st.session_state['churn_rate'] = churn_rate

    # Calcolo del conversion_rate
    totale_lead = data['Leads'].sum()
    totale_conversioni = data['Conversioni'].sum()
    conversion_rate = (totale_conversioni / totale_lead) * 100 if totale_lead > 0 else 0
    st.session_state['conversion_rate'] = conversion_rate

    # Sezione Dashboard
    if sezione == "Dashboard":
        st.header("Dashboard")
        # Dividi la pagina in colonne
        col1, col2, col3 = st.columns(3)

        # Prestazioni di vendita
        with col1:
            st.subheader("Prestazioni di Vendita")
            vendite_totali = data['Vendite'].sum()
            st.metric(label="Vendite Totali", value=f"€ {vendite_totali:,.2f}")

            # Andamento vendite per trimestre
            data['Trimestre'] = data['Data'].dt.to_period('Q')
            vendite_trimestrali = data.groupby('Trimestre')['Vendite'].sum().reset_index()

            # Converti 'Trimestre' in stringa
            vendite_trimestrali['Trimestre'] = vendite_trimestrali['Trimestre'].astype(str)

            fig = px.bar(
                vendite_trimestrali,
                x='Trimestre',
                y='Vendite',
                title="Vendite per Trimestre",
                color_discrete_sequence=['#007aff']
            )
            st.plotly_chart(fig, use_container_width=True)

        # Conversioni e lead
        with col2:
            st.subheader("Conversioni e Lead")
            st.metric(label="Leads Generati", value=int(totale_lead))
            st.metric(label="Conversion Rate", value=f"{conversion_rate:.2f}%")

            # Canali di acquisizione più performanti
            canali_perf = data.groupby('Canale')['Conversioni'].sum().reset_index()
            fig2 = px.pie(
                canali_perf,
                values='Conversioni',
                names='Canale',
                title='Canali di Acquisizione più Performanti',
                color_discrete_sequence=px.colors.sequential.Blues
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Customer Retention e Churn Rate
        with col3:
            st.subheader("Customer Retention e Churn Rate")
            st.metric(label="Customer Retention", value=f"{100 - churn_rate:.2f}%")
            st.metric(label="Churn Rate", value=f"{churn_rate:.2f}%")

            # Goal Gauge per Churn Rate
            fig3 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=churn_rate,
                title={'text': "Churn Rate"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "#ff3b30"},
                       'steps': [
                           {'range': [0, 25], 'color': '#34c759'},
                           {'range': [25, 50], 'color': '#ffcc00'},
                           {'range': [50, 100], 'color': '#ff3b30'}]},
            ))
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("---")

        # Grafico a imbuto per la gestione pipeline
        st.subheader("Gestione Pipeline")
        fasi = data['Fase'].unique()
        pipeline = data.groupby('Fase')['Leads'].sum().reset_index()
        pipeline = pipeline.sort_values(by='Leads', ascending=False)
        fig4 = px.funnel(
            pipeline,
            x='Leads',
            y='Fase',
            title='Pipeline di Vendita',
            color='Fase',
            color_discrete_sequence=px.colors.sequential.Blues
        )
        st.plotly_chart(fig4, use_container_width=True)

        # Mappe di calore per canali di vendita
        st.subheader("Mappe di Calore dei Canali di Vendita")
        # Converti 'Trimestre' in stringa
        data['Trimestre'] = data['Trimestre'].astype(str)
        heatmap_data = data.pivot_table(values='Vendite', index='Canale', columns='Trimestre', aggfunc='sum')
        fig5, ax5 = plt.subplots(figsize=(10,6))
        sns.heatmap(heatmap_data, annot=True, fmt=".2f", cmap='Blues', ax=ax5)
        ax5.set_title("Vendite per Canale e Trimestre", fontsize=16, fontweight='bold')
        st.pyplot(fig5)

    elif sezione == "AI Descrittiva":
        st.header("Modulo AI Descrittiva")
        domanda = st.text_input("Fai una domanda sui dati di vendita")
        if domanda:
            # Implementazione semplice per scopo dimostrativo
            risposta = ""
            if "quante vendite" in domanda.lower():
                vendite_totali = data['Vendite'].sum()
                risposta = f"Il totale delle vendite è € {vendite_totali:,.2f}"
            elif "canali di vendita" in domanda.lower():
                canali = data['Canale'].unique()
                risposta = f"I principali canali di vendita sono: {', '.join(canali)}"
            elif "churn rate" in domanda.lower():
                risposta = f"Il churn rate è {churn_rate:.2f}%"
            elif "conversion rate" in domanda.lower():
                risposta = f"Il tasso di conversione è {conversion_rate:.2f}%"
            else:
                risposta = "Mi dispiace, non ho una risposta a questa domanda al momento."
            st.write(risposta)

    elif sezione == "AI Predittiva":
        st.header("Modulo AI Predittivo")
        st.write("Previsioni di vendita per i prossimi 3 mesi")
        # Previsione semplice usando regressione lineare
        data['DataOrdinal'] = data['Data'].map(pd.Timestamp.toordinal)
        X = data[['DataOrdinal']]
        y = data['Vendite']
        model = LinearRegression()
        model.fit(X, y)
        # Previsione per i prossimi 90 giorni
        last_date = data['Data'].max()
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=90, freq='D')
        future_dates_ordinal = future_dates.map(pd.Timestamp.toordinal).values.reshape(-1, 1)
        predictions = model.predict(future_dates_ordinal)
        # Unisci dati storici e previsioni
        future_df = pd.DataFrame({'Data': future_dates, 'Vendite': predictions})
        combined_df = pd.concat([data[['Data', 'Vendite']], future_df])
        # Visualizzazione delle previsioni
        fig2 = px.line(combined_df, x='Data', y='Vendite', title="Vendite Storiche e Previsioni Future", color_discrete_sequence=['#007aff'])
        st.plotly_chart(fig2, use_container_width=True)

    elif sezione == "Consulenza Strategica":
        st.header("Modulo AI Consulenza Strategica")
        st.write("Analisi dei dati per fornire consigli strategici personalizzati.")
        if st.button("Genera consigli strategici"):
            # Implementazione semplice per scopo dimostrativo
            consigli = []
            # Analisi del canale più performante
            canali_perf = data.groupby('Canale')['Conversioni'].sum().reset_index()
            top_canale = canali_perf.loc[canali_perf['Conversioni'].idxmax()]['Canale']
            consigli.append(f"**Suggerimento:** Investi maggiormente nel canale '{top_canale}' che mostra le migliori performance in termini di conversioni.")
            # Consiglio sulla riduzione del churn rate
            if churn_rate > 30:
                consigli.append("**Consiglio:** Il churn rate è elevato. Implementa programmi di fidelizzazione per migliorare la customer retention.")
            else:
                consigli.append("**Consiglio:** Il churn rate è sotto controllo. Continua a monitorare la soddisfazione dei clienti.")
            # Consiglio sul tasso di conversione
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
        © 2024 - Boosha AI
    </div>
    """, unsafe_allow_html=True)
