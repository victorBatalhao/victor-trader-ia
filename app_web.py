import streamlit as st
import datetime
import yfinance as yf
from bot_trader import executar_analise_total, ACOES, gerar_grafico_historico

st.set_page_config(page_title="Victor Trader Pro", layout="wide")

# --- ALERTA AUTOMÁTICO DE FECHAMENTO ---
agora = datetime.datetime.now()
if agora.hour == 18 and agora.minute >= 5 and 'enviado' not in st.session_state:
    executar_analise_total(tipo_alerta="FECHAMENTO AUTOMÁTICO")
    st.session_state.enviado = True

# --- INTERFACE ---
st.title("🚀 Victor Trader IA v3.5.0")

# Status na lateral
st.sidebar.title("📡 Status")
for ticker in ACOES:
    try:
        p = yf.download(ticker, period="1d", progress=False)['Close'].iloc[-1]
        st.sidebar.success(f"{ticker}: R$ {p:.2f}")
    except:
        st.sidebar.error(f"{ticker}: FALTANDO INFO")

if st.button("📊 ANALISAR AGORA E ENVIAR TELEGRAM", use_container_width=True):
    executar_analise_total(tipo_alerta="SOLICITAÇÃO MANUAL")
    st.success("Sinal enviado!")

st.divider()

st.subheader("📈 Gráficos Históricos (Dias Anteriores)")
for ticker in ACOES:
    fig = gerar_grafico_historico(ticker)
    if fig: st.plotly_chart(fig, use_container_width=True)
    else: st.error(f"Erro ao carregar {ticker}")