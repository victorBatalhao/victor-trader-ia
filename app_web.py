import streamlit as st
import pandas as pd
import os
import datetime
import yfinance as yf
from bot_trader import executar_analise_total, ACOES, gerar_grafico_interativo, NOME_ARQUIVO

st.set_page_config(page_title="Victor Trader Pro", layout="wide")

# Barra Lateral - Força a exibição do último preço conhecido
st.sidebar.title("📡 Monitor de Sinais")
for ticker in ACOES:
    try:
        data = yf.download(ticker, period="5d", progress=False)
        preco = data['Close'].iloc[-1]
        st.sidebar.success(f"{ticker}: R$ {preco:.2f}")
    except:
        st.sidebar.error(f"{ticker}: Offline")

st.title("🚀 Victor Trader IA v3.2.5")

if st.button("📊 DISPARAR ANÁLISE COMPLETA", use_container_width=True):
    with st.spinner("IA processando dados históricos e atuais..."):
        executar_analise_total()
        st.success("Relatório enviado! Verifique seu Telegram.")
        st.rerun()

st.divider()

# Histórico de Dados
st.subheader("📁 Histórico e Backup")
if os.path.isfile(NOME_ARQUIVO):
    df = pd.read_csv(NOME_ARQUIVO)
    st.dataframe(df.tail(10), use_container_width=True)
    st.download_button("📥 Baixar Planilha CSV", df.to_csv(index=False), "backup.csv", "text/csv")
else:
    st.info("Aguardando dados para gerar histórico.")

st.divider()

# Gráficos de Tendência - Corrigidos para não aparecerem em branco
st.subheader("📈 Visualização de Tendências (Preço vs MA10)")
cols = st.columns(2)
for i, ticker in enumerate(ACOES):
    with cols[i % 2]:
        fig = gerar_grafico_interativo(ticker)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Aguardando dados de {ticker}...")