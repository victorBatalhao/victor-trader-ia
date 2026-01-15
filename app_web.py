import streamlit as st
import threading
import time
import schedule
import yfinance as yf
import pandas as pd
import os
import datetime
from bot_trader import executar_analise_total, ACOES, gerar_grafico_interativo, NOME_ARQUIVO

st.set_page_config(page_title="Victor Trader v3.2", page_icon="📈", layout="wide")

# --- BARRA LATERAL ---
st.sidebar.title("📡 Status da Conexão")
for ticker in ACOES:
    try:
        check = yf.Ticker(ticker).fast_info['last_price']
        st.sidebar.success(f"● {ticker}: OK") if check else st.sidebar.error(f"○ {ticker}: Erro")
    except:
        st.sidebar.warning(f"○ {ticker}: Offline")

# --- CORPO ---
st.title("🚀 Victor Trader IA")

if st.button("📊 DISPARAR ANÁLISE COMPLETA", use_container_width=True):
    with st.spinner("IA processando..."):
        executar_analise_total()
        st.success("Relatório enviado ao Telegram!")

st.divider()

# --- GESTÃO DO CSV ---
st.subheader("📁 Histórico de Performance (CSV)")
if os.path.isfile(NOME_ARQUIVO):
    df_hist = pd.read_csv(NOME_ARQUIVO)
    st.write("Últimas 5 operações registradas no servidor:")
    st.dataframe(df_hist.tail(5), use_container_width=True)
    
    csv_data = df_hist.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 BAIXAR BASE DE DADOS COMPLETA",
        data=csv_data,
        file_name=f"historico_trader_{datetime.date.today()}.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    st.info("O histórico aparecerá aqui após a primeira análise concluída.")

st.divider()
st.subheader("📈 Gráficos de Tendência")
cols = st.columns(2)
for i, ticker in enumerate(ACOES):
    with cols[i % 2]:
        fig = gerar_grafico_interativo(ticker)
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: st.warning(f"Aguardando dados de {ticker}")