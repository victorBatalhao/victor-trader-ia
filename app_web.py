import streamlit as st
import datetime
import yfinance as yf
from bot_trader import executar_analise_total, ACOES, gerar_grafico_historico

st.set_page_config(page_title="Victor Trader", layout="wide")

st.sidebar.title("📡 Status B3")
for ticker in ACOES:
    try:
        p = yf.download(ticker, period="1d", progress=False)['Close'].iloc[-1]
        st.sidebar.success(f"{ticker}: R$ {p:.2f}")
    except:
        st.sidebar.error(f"{ticker}: Erro de Dados") # Mensagem de erro solicitada

st.title("🚀 Victor Trader IA")

if st.button("📊 ANALISAR AGORA E ENVIAR TELEGRAM"):
    executar_analise_total("MANUAL")
    st.success("Enviado!")

st.divider()

for ticker in ACOES:
    fig = gerar_grafico_historico(ticker) # Gráficos detalhados com datas
    if fig: st.plotly_chart(fig, use_container_width=True)