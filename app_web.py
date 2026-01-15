import streamlit as st
import yfinance as yf
import pandas as pd
from bot_trader import executar_analise_total, ACOES, gerar_grafico_historico

st.set_page_config(page_title="Victor Trader IA", layout="wide")

# Sidebar: Status de Conexão com Erros Detalhados
st.sidebar.title("📡 Status dos Dados")
for ticker in ACOES:
    try:
        tkt = yf.Ticker(ticker)
        info = tkt.history(period="1d")
        if info.empty:
            st.sidebar.error(f"⚠️ {ticker}: Sem dados hoje")
        else:
            preco = info['Close'].iloc[-1]
            st.sidebar.success(f"● {ticker}: R$ {preco:.2f} (OK)")
    except:
        st.sidebar.error(f"❌ {ticker}: Erro de Conexão")

st.title("🚀 Victor Trader IA - Painel de Controle")

if st.button("📊 EXECUTAR ANÁLISE E ENVIAR AO TELEGRAM", use_container_width=True):
    with st.spinner("IA processando sinais de compra e venda..."):
        executar_analise_total()
        st.success("Sinais enviados para o Telegram!")

st.divider()

# Interface Gráfica: Gráficos Detalhados
st.subheader("📈 Gráficos de Histórico Detalhado (Datas e Valores)")
for ticker in ACOES:
    fig = gerar_grafico_historico(ticker)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"⚠️ Não foi possível carregar o gráfico de {ticker}. O Yahoo Finance pode estar instável.")

st.divider()
st.caption("Sistema v3.2.7 - Monitoramento Quantitativo Profissional")