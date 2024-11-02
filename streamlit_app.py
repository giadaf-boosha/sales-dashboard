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
    """
    , unsafe_allow_html=True)

# Titolo dell'app
st.title("📈 Dashboard Sales KPI + AI 🚀")

# Barra laterale per la navigazione
st.sidebar.title("Navigazione")
sezione = st.sidebar.radio("Vai a:", ["Caricamento Dati", "Dashboard", "AI Descrittiva", "AI Predittiva", "Consulenza Strategica"])

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
    
    # Calcolo metriche aggiuntive per AI
    churn_rate = (totale_persi / (totale_vinti + totale_persi)) * 100 if (totale_vinti + totale_persi) > 0 else 0
    conversion_rate = (totale_vinti / totale_opportunita) * 100 if totale_opportunita > 0 else 0
    
    # Analisi performance per canale
    if 'Canale' in data.columns:
        canali_perf = pd.DataFrame({
            'Canale': data['Canale'].unique(),
            'Conversioni': [
                len(data[(data['Canale'] == canale) & (data['Contratti Chiusi'].notnull())]) 
                for canale in data['Canale'].unique()
            ]
        })
        
        # Contributo percentuale alla pipeline per canale
        revenue_per_canale = data.groupby('Canale')['Valore Tot €'].sum()
        percentuale_contributo = (revenue_per_canale / totale_revenue) * 100

        # ACV (Average Contract Value) per canale
        acv_per_canale = revenue_per_canale / data[data['Contratti Chiusi'].notnull()].groupby('Canale').size()
        acv_per_canale = acv_per_canale.fillna(0)

    if sezione == "Dashboard":
        st.header("Dashboard")
        
        # Tabella riepilogativa per Canale
        if 'Canale' in data.columns:
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
        if 'Canale' in data.columns:
            # Grafico a barre delle opportunità chiuse per canale
            st.subheader("Opportunità Chiuse per Canale")
            closed_opps = data[data['Contratti Chiusi'].notnull()]
            closed_opps_count = closed_opps.groupby('Canale').size().reset_index(name='Opportunità Chiuse')
            fig1 = px.bar(closed_opps_count, x='Canale', y='Opportunità Chiuse', 
                         title="Opportunità Chiuse per Canale", 
                         color='Canale', 
                         color_discrete_sequence=px.colors.sequential.Blues)
            st.plotly_chart(fig1, use_container_width=True)

            # Grafico a torta per la percentuale di contributo per canale
            st.subheader("Contributo Percentuale alla Pipeline per Canale")
            fig2 = px.pie(summary_df, values='% of pipeline contribution', names='Source', 
                         title='Contributo Percentuale alla Pipeline')
            st.plotly_chart(fig2, use_container_width=True)

        if 'Servizio' in data.columns:
            # Grafico a barre per Revenue per Servizio
            st.subheader("Revenue per Servizio")
            revenue_servizio_df = data.groupby('Servizio')['Valore Tot €'].sum().reset_index()
            fig3 = px.bar(revenue_servizio_df, x='Servizio', y='Valore Tot €', 
                         title="Revenue per Servizio", 
                         color='Servizio', 
                         color_discrete_sequence=px.colors.sequential.Blues)
            st.plotly_chart(fig3, use_container_width=True)

        # Distribuzione dei Valori dei Contratti (Istogramma)
        st.subheader("Distribuzione dei Valori dei Contratti")
        fig4 = px.histogram(data[data['Valore Tot €'] > 0], x='Valore Tot €', nbins=20, 
                           title="Distribuzione dei Valori dei Contratti", 
                           color_discrete_sequence=['#007aff'])
        st.plotly_chart(fig4, use_container_width=True)

        # Andamento Mensile delle Opportunità e delle Revenue
        st.subheader("Andamento Mensile delle Opportunità e delle Revenue")
        data['Mese'] = data['Contratti Chiusi'].dt.to_period('M').astype(str)
        monthly_revenue = data.groupby('Mese')['Valore Tot €'].sum().reset_index()
        monthly_opportunities = data.groupby('Mese').size().reset_index(name='Opportunità Totali')
        
        fig5 = px.line(monthly_revenue, x='Mese', y='Valore Tot €', 
                       title="Andamento Mensile delle Revenue", 
                       markers=True, line_shape='linear', 
                       color_discrete_sequence=['#007aff'])
        fig5.update_layout(yaxis_title="Revenue (€)")
        st.plotly_chart(fig5, use_container_width=True)
        
        fig6 = px.line(monthly_opportunities, x='Mese', y='Opportunità Totali', 
                       title="Andamento Mensile delle Opportunità", 
                       markers=True, line_shape='linear', 
                       color_discrete_sequence=['#ff7f0e'])
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
        fig7 = px.bar(conversion_df, x='Fase', y='Conversion Rate (%)', 
                      title="Conversion Rate per Fase della Pipeline", 
                      color='Fase', 
                      color_discrete_sequence=px.colors.sequential.Blues)
        st.plotly_chart(fig7, use_container_width=True)

    elif sezione == "AI Descrittiva":
        st.header("Modulo AI Descrittiva")
        domanda = st.text_input("Fai una domanda sui dati di vendita")
        if domanda:
            # Implementazione semplice per scopo dimostrativo
            risposta = ""
            if "quante vendite" in domanda.lower():
                risposta = f"Il totale delle vendite è € {totale_revenue:,.2f}"
            elif "canali di vendita" in domanda.lower():
                if 'Canale' in data.columns:
                    canali = data['Canale'].unique()
                    risposta = f"I principali canali di vendita sono: {', '.join(canali)}"
                else:
                    risposta = "Non sono disponibili informazioni sui canali di vendita."
            elif "churn rate" in domanda.lower():
                risposta = f"Il churn rate è {churn_rate:.2f}%"
            elif "conversion rate" in domanda.lower():
                risposta = f"Il tasso di conversione è {conversion_rate:.2f}%"
            elif "tempo medio" in domanda.lower():
                risposta = f"Il tempo medio di chiusura delle opportunità è {tempo_medio_chiusura:.1f} giorni"
            elif "pipeline velocity" in domanda.lower():
                risposta = f"La pipeline velocity è € {pipeline_velocity:,.2f}"
            elif "win rate" in domanda.lower():
                risposta = f"Il win rate è {win_rate:.2f}%"
            else:
                risposta = "Mi dispiace, non ho una risposta a questa domanda al momento."
            st.write(risposta)

    elif sezione == "AI Predittiva":
        st.header("Modulo AI Predittivo")
        st.write("Previsioni di vendita per i prossimi 3 mesi")
        
        if 'Contratti Chiusi' in data.columns and 'Valore Tot €' in data.columns:
            df_pred = data.dropna(subset=['Contratti Chiusi', 'Valore Tot €'])
            df_pred = df_pred.sort_values('Contratti Chiusi')
            df_pred['DataOrdinal'] = df_pred['Contratti Chiusi'].map(pd.Timestamp.toordinal)
            X = df_pred[['DataOrdinal']]
            y = df_pred['Valore Tot €']
            
            if len(X) > 1:
                model = LinearRegression()
                model.fit(X, y)
                last_date = df_pred['Contratti Chiusi'].max()
                future_dates = pd.date_range(start=last_date + pd.Tim
                # Continua dalla sezione AI Predittiva
                future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=90, freq='D')
                future_dates_ordinal = future_dates.map(pd.Timestamp.toordinal).values.reshape(-1, 1)
                predictions = model.predict(future_dates_ordinal)
                
                # Calcolo statistiche predittive
                prediction_mean = predictions.mean()
                prediction_total = predictions.sum()
                
                # Visualizzazione delle statistiche predittive
                col1, col2 = st.columns(2)
                col1.metric("Media Vendite Previste", f"€ {prediction_mean:,.2f}")
                col2.metric("Totale Vendite Previste (90 giorni)", f"€ {prediction_total:,.2f}")
                
                # Creazione del dataframe per la visualizzazione
                future_df = pd.DataFrame({'Contratti Chiusi': future_dates, 'Valore Tot €': predictions})
                combined_df = pd.concat([df_pred[['Contratti Chiusi', 'Valore Tot €']], future_df])
                
                # Grafico delle previsioni
                fig_pred = px.line(combined_df, x='Contratti Chiusi', y='Valore Tot €', 
                                 title="Vendite Storiche e Previsioni Future",
                                 color_discrete_sequence=['#007aff'])
                
                # Aggiunta della linea di demarcazione tra dati storici e previsioni
                fig_pred.add_vline(x=last_date, line_dash="dash", line_color="red",
                                 annotation_text="Inizio Previsioni",
                                 annotation_position="top right")
                
                st.plotly_chart(fig_pred, use_container_width=True)
                
                # Aggiunta di informazioni sulle previsioni
                st.info("📊 Le previsioni sono basate su un modello di regressione lineare che utilizza i dati storici delle vendite. " +
                       "La linea tratteggiata rossa separa i dati storici dalle previsioni future.")
                
            else:
                st.warning("Dati insufficienti per effettuare una previsione. Sono necessari almeno due punti dati.")

    elif sezione == "Consulenza Strategica":
        st.header("Modulo AI Consulenza Strategica")
        st.write("Analisi dei dati per fornire consigli strategici personalizzati.")
        
        if st.button("Genera consigli strategici"):
            consigli = []
            
            # Analisi del canale più performante
            if 'Canale' in data.columns and not canali_perf.empty:
                top_canale = canali_perf.loc[canali_perf['Conversioni'].idxmax()]['Canale']
                consigli.append(f"**Suggerimento sul canale di vendita:**\n"
                              f"Il canale '{top_canale}' mostra le migliori performance in termini di conversioni. "
                              f"Considera di aumentare gli investimenti su questo canale e analizza le best practice "
                              f"che lo rendono più efficace.")
            
            # Analisi del churn rate
            if churn_rate > 30:
                consigli.append("**Analisi del Churn Rate:**\n"
                              f"Il churn rate attuale del {churn_rate:.1f}% è superiore alla media. Suggerimenti:\n"
                              "- Implementa un programma di fidelizzazione clienti\n"
                              "- Migliora il processo di onboarding\n"
                              "- Aumenta il follow-up post-vendita\n"
                              "- Analizza i motivi principali di abbandono")
            else:
                consigli.append("**Analisi del Churn Rate:**\n"
                              f"Il churn rate del {churn_rate:.1f}% è nella norma. Continua a:\n"
                              "- Monitorare la soddisfazione dei clienti\n"
                              "- Raccogliere feedback regolarmente\n"
                              "- Mantenere un'alta qualità del servizio")
            
            # Analisi del tasso di conversione
            if conversion_rate < 20:
                consigli.append("**Ottimizzazione del Tasso di Conversione:**\n"
                              f"Il tasso di conversione attuale del {conversion_rate:.1f}% è sotto la media. Azioni consigliate:\n"
                              "- Rivedi e ottimizza il processo di vendita\n"
                              "- Implementa training specifici per il team commerciale\n"
                              "- Migliora la qualifica delle opportunità\n"
                              "- Analizza i punti di frizione nel funnel di vendita")
            elif conversion_rate < 40:
                consigli.append("**Ottimizzazione del Tasso di Conversione:**\n"
                              f"Il tasso di conversione del {conversion_rate:.1f}% è nella media. Per migliorare:\n"
                              "- Identifica e replica le best practice dei top performer\n"
                              "- Implementa A/B testing sulle strategie di vendita\n"
                              "- Migliora la personalizzazione delle proposte")
            else:
                consigli.append("**Ottimizzazione del Tasso di Conversione:**\n"
                              f"Eccellente tasso di conversione del {conversion_rate:.1f}%! Suggerimenti:\n"
                              "- Documenta e standardizza le best practice\n"
                              "- Implementa un programma di mentoring interno\n"
                              "- Mantieni l'alto standard qualitativo")
            
            # Analisi del tempo di chiusura
            if tempo_medio_chiusura > 60:
                consigli.append("**Ottimizzazione del Ciclo di Vendita:**\n"
                              f"Il tempo medio di chiusura di {tempo_medio_chiusura:.1f} giorni è elevato. Suggerimenti:\n"
                              "- Identifica e rimuovi i colli di bottiglia nel processo di vendita\n"
                              "- Automatizza le attività ripetitive\n"
                              "- Migliora la gestione delle obiezioni\n"
                              "- Ottimizza il processo di approvazione interno")
            
            # Mostra i consigli con formattazione migliorata
            for i, consiglio in enumerate(consigli, 1):
                st.markdown(f"### 💡 Consiglio #{i}")
                st.markdown(consiglio)
                st.markdown("---")

else:
    st.warning("Per favore, carica i dati nella sezione 'Caricamento Dati' per continuare.")

# Footer
st.markdown("""
    <hr>
    <div style='text-align: center; color: #888888;'>
        © 2024 - Boosha AI + Result Consulting.
    </div>
    """, unsafe_allow_html=True)